#! /usr/bin/python3
# -*- coding: utf-8 -*-

import logging

import redis
import tornado.escape

import engine
from kola import DB, ThreadPool


POOLSIZE = 10

log = logging.getLogger('crawler')

class KolaEngine:
    def __init__(self):
        self.thread_pool = ThreadPool(POOLSIZE)
        self.db = DB()
        self.command = engine.EngineCommands()
        self.engines = {}
        self.MenuList = []
        self.UpdateAlbumFlag = False

        self.AddEngine(engine.LetvEngine)
        self.AddEngine(engine.SohuEngine)
        self.AddEngine(engine.QiyiEngine)
        self.AddEngine(engine.LiveEngine)
        #self.AddEngine(engine.WolidouEngine)

    def AddEngine(self, egClass):
        e = egClass()
        self.engines[e.engine_name] = e
        e.GetMenu(self.MenuList)

    def GetEngine(self, name):
        if name in self.engines:
            return self.engines[name]
        return None

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
                              'private': True,
                              'cid': True,
                              'vid': True}

        albumList = []
        data, _ = self.db.GetAlbumListJson(argument, disablePage=True, full=True)
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
        for menu in self.MenuList:
            menu.UpdateHotList()

    # 更新所有节目（增加新的节目）
    def UpdateAllAlbumList(self):
        self.UpdateAlbumFlag = True
        for menu in self.MenuList:
            menu.UpdateAlbumList()

    def CommandEmptyMessage(self):
        if self.UpdateAlbumFlag == True:
            self.UpdateAlbumFlag = False
