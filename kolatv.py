#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import base64
import redis
import logging
import tornado.escape
import sohuengine as eg

from ThreadPool import ThreadPool
from apscheduler.scheduler import Scheduler

POOLSIZE = 10

log = logging.getLogger('crawler')

class Kolatv:
    def __init__(self):
        self.engine = eg.SohuEngine()
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=2)
        self.thread_pool = ThreadPool(POOLSIZE)
        self.MenuList = self.engine.GetMenu()
        self.sched = Scheduler()
        self.sched.start()
        self.sched.add_interval_job(self.UpdateNewest, hours=1)
        self.sched.add_interval_job(self.UpdateHottest, hours=4)
        self.sched.add_interval_job(self.UpdateTop200, hours=12)
        self.sched.add_interval_job(self.UpdateAllAlbumList, hours=2, seconds= 10)

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

    def ParserHtml(self, data):
        js = tornado.escape.json_decode(data)
        if (js == None) or ('data' not in js):
            db = redis.Redis(host='127.0.0.1', port=6379, db=2) # 出错页
            db.rpush('urls', js['source'])
            print("Error:", js['source'])
            return False

        text = base64.decodebytes(js['data'].encode())
        if text:
            js['data'] = text
            menuName = js['menu']
            menu = self.FindMenu(menuName)
            if menu:
                name = js['name']
                menu.ParserHtml(name, js)

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

    # 更新所有节目的排名数据
    def UpdateAllScore(self):
        print("UpdateAllScore")
        for (_, menu) in self.MenuList.items():
            menu.UpdateAllScore()

    # 更新所有节目的完全信息
    def UpdateAllFullInfo(self):
        print("UpdateAllFullInfo")
        for (_, menu) in self.MenuList.items():
            menu.UpdateAllFullInfo()

    # 更新所有节目（增加新的节目）
    def UpdateAllAlbumList(self):
        for (_, menu) in list(self.MenuList.items()):
            menu.UpdateAlbumList()

    # 更新所有节目的播放信息
    def UpdateAllPlayInfo(self):
        for (_, menu) in list(self.MenuList.items()):
            menu.UpdateAllPlayInfo()

    # 更新所有节目主页
    def UpdateAllAlbumPage(self):
        for (_, menu) in list(self.MenuList.items()):
            menu.UpdateAllHomePage()

    def UpdateAllHotList(self):
        for (_, menu) in list(self.MenuList.items()):
            menu.UpdateHotList()
