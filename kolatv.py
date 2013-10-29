#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import redis
import logging
import tornado.escape
import sohuengine, letvengine, textengine
import engine as eg
from db import DB
import utils

from ThreadPool import ThreadPool

POOLSIZE = 10

log = logging.getLogger('crawler')

class Kolatv:
    def __init__(self):
        self.thread_pool = ThreadPool(POOLSIZE)
        self.db = DB()
        self.command = eg.Commands(self.db.map_table)
        self.engines = {}
        self.MenuList = {}

        self.AddEngine(sohuengine.SohuEngine)
        #self.AddEngine(letvengine.LetvEngine)
        self.AddEngine(textengine.TextvEngine)

    def AddEngine(self, egClass):
        e = egClass(self.db, self.command)
        self.engines[e.engine_name] = e
        e.GetMenu(self.MenuList)

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
            return self.db.GetAlbumListJson(argument, m.cid)

        return data, 0

    def GetMenuAlbumListByCid(self, cid, argument):
        cid = utils.autoint(cid)
        return self.db.GetAlbumListJson(argument, cid)

    def GetVideoListByPid(self, pid, argument):
        return self.db.GetVideoListJson(pid=pid, arg=argument)

    # 得到真实播放地址
    def GetRealPlayer(self, text, cid, definition, step):
        menu = self.FindMenuById(utils.autoint(cid))
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

        for _, eg in list(self.engines.items()):
            if eg.ParserHtml(js) != None:
                break

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

    def _get_album(self, All=False):
        argument = {}
        argument['fields'] = {'engineList' : True,
                              'albumName': True,
                              'albumPageUrl': True,
                              'vid': True,
                              'playlistid': True}

        albumList = []
        data, _ = self.db.GetAlbumListJson(argument, All=All, disablePage=True)
        for p in data:
            for (name, engine) in list(self.engines.items()):
                if 'engineList' in p and name in p['engineList']:
                    albumList.append(engine.NewAlbum(p))
                    break

        return albumList

    # 更新所有节目的排名数据
    def UpdateAllScore(self):
        print("UpdateAllScore")
        for album in self._get_album(True):
            album.UpdateScoreCommand()

        self.command.Execute()

    # 更新所有节目的完全信息
    def UpdateAllFullInfo(self):
        print("UpdateAllFullInfo")

        for album in self._get_album(True):
            album.UpdateFullInfoCommand()

        self.command.Execute()

    # 更新所有节目的播放信息
    def UpdateAllPlayInfo(self):
        for album in self._get_album():
            album.UpdateAlbumPlayInfoCommand()

        self.command.Execute()

    # 更新所有节目主页
    def UpdateAllAlbumPage(self):
        for album in self._get_album(True):
            album.UpdateAlbumPageCommand()

        self.command.Execute()

    def UpdateAllHotList(self):
        for (_, menu) in list(self.MenuList.items()):
            menu.UpdateHotList()

    # 更新所有节目（增加新的节目）
    def UpdateAllAlbumList(self):
        for (_, menu) in list(self.MenuList.items()):
            menu.UpdateAlbumList()
