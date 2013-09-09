#! env /usr/bin/python
# -*- coding: utf-8 -*-

import json
import base64
import redis
import sohuengine as eg

from utils.mylogger import logging
from utils.ThreadPool import ThreadPool
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
        self.sched.add_interval_job(self.UpdateAll, hours=2, seconds= 10)


    def UpdateAlbumList(self):
        for (_, menu) in self.MenuList.items():
            menu.UpdateAlbumList()

    def ParserHtml(self, data):
        js = json.loads(data)
        if (js == None) or (not js.has_key('data')):
            print "Error: ", js['source']
            return False

        text = base64.decodestring(js['data'])
        if text:
            js['data'] = text
            menuName = js['menu']
            menu = self.FindMenu(menuName)
            if menu:
                name = js['name']
                menu.ParserHtml(name, js)

        return True

    def UpdateNewest(self): # 更新最新节目
        print "UpdateNewest"
        pass

    def UpdateHottest(self): #　更新最热门的节目
        print "UpdateHottest"
        pass

    def UpdateTop200(self):
        print "UpdateTop200"
        pass
    # 发起全网更新
    def UpdateAll(self):
        # 更新所有菜单最增节目
        #
        # 更新所有节目的最新数据
        #    0. 更新最新节目10/20部每小时一次
        #    1. 更新各菜单下最热50部节目最新数据(每4小时一次）
        #    2. 更新前200部节目最新数据(每12小时一次）
        #    3. 更新所有节目的最新数据(每天一次）
        print "UpdateAll"
        #for (_, menu) in self.MenuList.items():
        #    menu.UpdateAlbumList()         # 重新获得所有节目列表
        #    menu.UpdateAllAlbumFullInfo()  # 更新节目详细信息

    def GetRealPlayer(self, text):
        text = base64.decodestring(text)
        return self.engine.ParserRealUrl(text)

    def FindMenu(self, name):
        if self.MenuList.has_key(name):
            return self.MenuList[name]
        else:
            return None

    def AddTask(self, data):
        self.thread_pool.add_job(self.ParserHtml, [data])

def main():
    # 第一步：通过 engine.GetMenu 列表所有 menu
    # 第二步：得到节目的基本信息, menu.UpdateAlbumList，分三小步：
    #       １、获得菜单下所有节目部分信息（得到所有节目的 albumPageUrl, albumName) (解析器：CmdParserTVAll)
    #       ２、通过节目的 albumPageUrl 得到节目的部分信息：vid, pid, playlistid (解析器:CmdParserAlbum)
    # 　　　　　　　　　　　　　得到的信息可能并不完整，有时无法得到playlistid数据
    #       ３、当 playlistid 的数据没有得到的话通过命令xxx得到节目信息
    #       ４、获得节目的最完整数据
    # 　　　 ５、获得节目的指数数据

    tv = Kolatv()
    tv.UpdateAlbumList()  # 更所有菜单的节目列表
    for (_, m) in tv.MenuList.items():
        m.UpdateAllAlbumFullInfo()

if __name__ == '__main__':
    main()

