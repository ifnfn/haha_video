#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import redis
import logging
import tornado.escape
import sohuengine, letvengine
import engine
from db import DB

from ThreadPool import ThreadPool

POOLSIZE = 10

log = logging.getLogger('crawler')

class Kolatv:
    def __init__(self):
        self.db = DB()
        self.command = engine.Commands(self.db.map_table)
        self.engine = sohuengine.SohuEngine(self.db, self.command)
        self.letv_engine = letvengine.LetvEngine(self.db, self.command)
        self.engines = {}
        self.engines[self.engine.engine_name] = self.engine
        self.engines[self.letv_engine.engine_name] = self.letv_engine

        self.thread_pool = ThreadPool(POOLSIZE)
        self.MenuList = {}

        self.engine.GetMenu(self.MenuList)
        #self.letv_engine.GetMenu(self.MenuList)

    def GetEngine(self, name):
        if name in self.engines:
            return self.engines[name]
        return None

    def GetMenuJsonInfoById(self, cid_list):
        ret = []
        count = len(cid_list)
        for _, menu in list(self.MenuList.items()):
            if count == 0 or str(menu.cid) in cid_list:
                ret.append(menu.GetJsonInfo())

        return ret

    def GetMenuJsonInfoByName(self, name_list):
        ret = []
        count = len(name_list)
        for name, menu in list(self.MenuList.items()):
            if count == 0 or name in name_list:
                ret.append(menu.GetJsonInfo())

        return ret

    def GetMenuAlbumListByName(self, menuName, argument):
        data = []
        m = self.FindMenu(menuName)
        if m:
            data = self.db.GetAlbumListJson(argument, m.cid)

        return data

    def GetVideoListByPid(self, pid, argument):
        return self.db.GetVideoListJson(pid=pid, arg=argument)

    # 得到真实播放地址
    def GetRealPlayer(self, text, cid, definition, step):
        menu = self.FindMenuById(engine.autoint(cid))
        if menu == None:
            return {}

        return menu.GetRealPlayer(text, definition, step)

    def ParserHtml(self, data):
        js = tornado.escape.json_decode(data)
        if (js == None) or ('data' not in js):
            db = redis.Redis(host='127.0.0.1', port=6379, db=2) # 出错页
            db.rpush('urls', js['source'])
            print("Error:", js['source'])
            return False

        if self.engine.ParserHtml(js) == None:
            self.letv_engine.ParserHtml(js)

        return True

    def FindMenuById(self, cid):
        for _, menu in list(self.MenuList.items()):
            if menu.cid == cid:
                return menu

        return None

    def FindMenu(self, name):
        if name in self.MenuList:
            return self.MenuList[name]
        else:
            return None

    def AddTask(self, data):
        self.thread_pool.add_job(self.ParserHtml, [data])

    def UpdateNewest(self): # 更新最新节目
        print("UpdateNewest")
        pass

    def UpdateHottest(self): #　更新最热门的节目
        print("UpdateHottest")
        pass

    def UpdateTop200(self):
        print("UpdateTop200")
        pass

    def _get_data(self, All=False):
        argument = {}
        argument['fields'] = {'albumName': True,
                              'albumPageUrl': True,
                              'vid': True,
                              'playlistid': True}
        return self.db.GetAlbumListJson(argument, All=All)

    # 更新所有节目的排名数据
    def UpdateAllScore(self):
        print("UpdateAllScore")

        for p in self._get_data(True):
            for (name, engine) in list(self.engines.items()):
                if hasattr(p, 'sources') and name in p.sources:
                    engine.NewAlbum(p).UpdateScoreCommand()
                else:
                    self.engine.NewAlbum(p).UpdateScoreCommand()
        self.command.Execute()

    # 更新所有节目的完全信息
    def UpdateAllFullInfo(self):
        print("UpdateAllFullInfo")

        for p in self._get_data(True):
            for (name, engine) in list(self.engines.items()):
                if hasattr(p, 'sources') and name in p.sources:
                    engine.NewAlbum(p).UpdateFullInfoCommand()
                else:
                    self.engine.NewAlbum(p).UpdateFullInfoCommand()
        self.command.Execute()

    # 更新所有节目的播放信息
    def UpdateAllPlayInfo(self):
        for p in self._get_data():
            for (name, engine) in list(self.engines.items()):
                if hasattr(p, 'sources') and name in p.sources:
                    engine.NewAlbum(p).UpdateAlbumPlayInfoCommand()
                else:
                    self.engine.NewAlbum(p).UpdateAlbumPlayInfoCommand()
        self.command.Execute()

    # 更新所有节目主页
    def UpdateAllAlbumPage(self):
        for p in self._get_data(All=True):
            for (name, engine) in list(self.engines.items()):
                if hasattr(p, 'sources') and name in p.sources:
                    engine.NewAlbum(p).UpdateAlbumPageCommand()
                else:
                    self.engine.NewAlbum(p).UpdateAlbumPageCommand()
        self.command.Execute()

    def UpdateAllHotList(self):
        for (_, menu) in list(self.MenuList.items()):
            menu.UpdateHotList()

    # 更新所有节目（增加新的节目）
    def UpdateAllAlbumList(self):
        for (_, menu) in list(self.MenuList.items()):
            menu.UpdateAlbumList()
