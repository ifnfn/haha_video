#! env /usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
from time import sleep

from utils.dataSaver import DataSaver
from Queue import PriorityQueue
from utils.mylogger import logging
from utils.BeautifulSoup import BeautifulSoup as bs
from utils.ThreadPool import ThreadPool
from utils.fetchTools import fetch_httplib2 as fetch
import time
import traceback
import json
import random
#import BeautifulSoup as bs
import urllib
import base64, zlib
import re
import redis
from random import randint
from urllib2 import HTTPError
from urlparse import urlparse
from xml.dom.minidom import parseString

import engine as eg


POOLSIZE = 10

log = logging.getLogger("crawler")
engine = eg.SohuEngine()

class Kolatv:
    def __init__(self):
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=2)
        self.UpdateMainMenu()
        self.thread_pool = ThreadPool(POOLSIZE)

    def UpdateMainMenu(self):
        self.MenuList = engine.GetMenu()
        #self.db.flushdb()
        self.db.delete('menu')

        for n in self.MenuList:
            print "save menu: ", n
            self.db.rpush('menu', n)
            menu = self.MenuList[n]
            menu.UpdateHotList()

            # 将最热节目存入数据库
            self.db.delete('hot:%s' % n)
            for v in menu.HotList:
                text = json.dumps(v, ensure_ascii = False)
                self.db.rpush('hot:%s' % n, text)
            menu.UploadProgrammeList()

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
                list = menu.ParserHtml(name, text)
                if list:
                    for p in list:
                        try:
                            self.db.zadd(menuName, p.albumName, p.dailyPlayNum) # 节目名
                            print "ZADD: ", menuName, p.dailyPlayNum, p.albumName
                        except:
                            print "ZADD ERROR: ", menuName, p.dailyPlayNum, p.albumName
                            print sys.exc_info()[0],sys.exc_info()[1]
                self.db.save()

        return True

    def FindMenu(self, name):
        if self.MenuList.has_key(name):
            return self.MenuList[name]
        else:
            return None

    def AddTask(self, data):
        self.thread_pool.add_job(self.ParserHtml, [data])

tv = Kolatv()

def main():
    return

if __name__ == "__main__":
    main()

