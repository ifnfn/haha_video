#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import redis
import logging
import tornado.escape
import sohuengine as eg

from ThreadPool import ThreadPool

POOLSIZE = 10

log = logging.getLogger('crawler')

class Kolatv:
    def __init__(self):
        self.engine = eg.SohuEngine()
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=2)
        self.thread_pool = ThreadPool(POOLSIZE)
        self.MenuList = self.engine.GetMenu()

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
            data = self.engine.GetAlbumListJson(argument, m.cid)

        return data

    def GetVideoListByPid(self, pid, argument):
        return self.engine.db.GetVideoListJson(pid=pid, arg=argument)

    def ParserHtml(self, data):
        js = tornado.escape.json_decode(data)
        if (js == None) or ('data' not in js):
            db = redis.Redis(host='127.0.0.1', port=6379, db=2) # 出错页
            db.rpush('urls', js['source'])
            print("Error:", js['source'])
            return False

        self.engine.ParserHtml(js)

        return True

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
        return self.engine.GetAlbumListJson(argument, All=All)

    # 更新所有节目的排名数据
    def UpdateAllScore(self):
        print("UpdateAllScore")

        for p in self._get_data(True):
            self.engine.NewAlbum(p).UpdateScoreCommand()
        self.engine.command.Execute()

    # 更新所有节目的完全信息
    def UpdateAllFullInfo(self):
        print("UpdateAllFullInfo")

        for p in self._get_data(True):
            self.engine.NewAlbum(p).UpdateFullInfoCommand()
        self.engine.command.Execute()

    # 更新所有节目的播放信息
    def UpdateAllPlayInfo(self):
        for p in self._get_data():
            self.engine.NewAlbum(p).UpdateAlbumPlayInfoCommand()
        self.engine.command.Execute()

    # 更新所有节目主页
    def UpdateAllAlbumPage(self):
        for p in self._get_data(All=True):
            self.engine.NewAlbum(p).UpdateAlbumPageCommand()
        self.engine.command.Execute()

    def UpdateAllHotList(self):
        for (_, menu) in list(self.MenuList.items()):
            menu.UpdateHotList()

    # 更新所有节目（增加新的节目）
    def UpdateAllAlbumList(self):
        for (_, menu) in list(self.MenuList.items()):
            #menu.UpdateAlbumList()
            menu.UpdateAlbumList2()
