#! /usr/bin/python3
# -*- coding: utf-8 -*-

from pymongo import Connection
import redis
import tornado.ioloop
import tornado.options
import tornado.web

from kola import BaseHandler, DB, ThreadPool

from .engines import EngineCommands, VideoEngine, KolaParser, KolaAlias
from .funshion import FunshionEngine
from .iqiyi import QiyiEngine
from .letv import LetvEngine
from .pptv import PPtvEngine
from .qq import QQEngine
from .sohu import SohuEngine
from .tv import LiveEngine


POOLSIZE = 10

class KolaEngine:
    def __init__(self):
        self.thread_pool = ThreadPool(POOLSIZE)
        self.db = DB()
        self.command = EngineCommands()
        self.engines = []
        self.UpdateAlbumFlag = False

        self.AddEngine(LiveEngine)
        self.AddEngine(QQEngine)
        self.AddEngine(QiyiEngine)
        self.AddEngine(PPtvEngine)
        self.AddEngine(SohuEngine)
        #self.AddEngine(FunshionEngine)
        #self.AddEngine(LetvEngine)

    def AddEngine(self, egClass):
        self.engines.append(egClass())

    def ParserHtml(self, data):
        js = tornado.escape.json_decode(data)
        if (js == None) or ('data' not in js):
            db = redis.Redis(host='127.0.0.1', port=6379, db=2) # 出错页
            db.rpush('urls', js['source'])
            print("Error:", js['source'])
            return False

        for eg in self.engines:
            if eg.ParserHtml(js):
                break

        return True

    def UpdateNewest(self): # 更新最新节目
        print("UpdateNewest")

    def UpdateAllHotList(self):
        print("UpdateAllHotList")

    # 更新所有节目的排名数据
    def UpdateAllScore(self):
        print("UpdateAllScore")
        for eg in self.engines:
            eg.UpdateAllScore()

    # 更新所有节目
    def UpdateAllAlbumList(self, engine):
        for eg in self.engines:
            if engine:
                if eg.engine_name in engine:
                    eg.UpdateAllAlbumList()
            else:
                eg.UpdateAllAlbumList()

    def CommandEmptyMessage(self):
        if self.UpdateAlbumFlag == True:
            self.UpdateAlbumFlag = False

    def AddTask(self, data):
        self.thread_pool.add_job(self.ParserHtml, [data])
