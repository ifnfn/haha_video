#! env /usr/bin/python
# -*- coding: utf-8 -*-

import sys

from utils.mylogger import logging
from utils.ThreadPool import ThreadPool
#from utils.BeautifulSoup import BeautifulSoup as bs
#from utils.fetchTools import fetch_httplib2 as fetch
import json
import base64
#import re
import redis

import engine as eg


POOLSIZE = 10

log = logging.getLogger('crawler')
engine = eg.SohuEngine()

class Kolatv:
    def __init__(self):
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=2)
        self.thread_pool = ThreadPool(POOLSIZE)
        self.MenuList = engine.GetMenu()

    def UpdateMainMenu(self):
        #self.MenuList = engine.GetMenu()
        #self.db.flushdb()
        self.db.delete('menu')

        for (n, menu) in self.MenuList.items():
            menu.UpdateAlbumList()
            print 'save menu: ', n
            self.db.rpush('menu', n)

            # 将最热节目存入数据库
            self.db.delete('hot:%s' % n)
            for v in menu.HotList:
                text = json.dumps(v, ensure_ascii = False)
                self.db.rpush('hot:%s' % n, text)

    def ParserHtml(self, data):
        js = json.loads(data)
        if js == None:
            return False

        text =base64.decodestring(js['data'])
        if text:
            js['data'] = text
            menuName = js['menu']
            menu = self.FindMenu(menuName)
            if menu:
                text = js['data']
                name = js['name']
                plist = menu.ParserHtml(name, text)
                if plist:
                    for p in plist:
                        try:
                            self.db.zadd(menuName, p.albumName, p.dailyPlayNum) # 节目名
                            print 'ZADD: ', menuName, p.dailyPlayNum, p.albumName
                        except:
                            print 'ZADD ERROR: ', menuName, p.dailyPlayNum, p.albumName
                            print sys.exc_info()[0],sys.exc_info()[1]
                self.db.save()

        return True

    # 发起全网更新
    def FullUpdate(self):
        # 更新所有菜单最增节目
        #
        # 更新所有节目的最新数据
        #    0. 更新最新节目10/20部每小时一次
        #    1. 更新各菜单下最热50部节目最新数据(每4小时一次）
        #    2. 更新前200部节目最新数据(每12小时一次）
        #    3. 更新所有节目的最新数据(每天一次）
        pass

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
    # 第三步：获得节目的最完整数据
    # 第四步：获得节目的指数数据

    tv = Kolatv()
    tv.UpdateMainMenu() # 更所有菜单的节目列表
    for (_, m) in tv.MenuList.items():
        m.UpdateAllAlbumFullInfo()

if __name__ == '__main__':
    main()

