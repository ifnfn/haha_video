#! env /usr/bin/python
# -*- coding: utf-8 -*-

import sys, os

from utils.dataSaver import DataSaver
from Queue import PriorityQueue
from time import sleep
from utils.mylogger import logging
import time
import threading
import traceback
import json
import random
from utils.BeautifulSoup import BeautifulSoup as bs
#import BeautifulSoup as bs
import urllib
from utils.fetchTools import fetch_httplib2 as fetch
import base64, zlib
import re
import redis
from random import randint
from urllib2 import HTTPError
from urlparse import urlparse
from xml.dom.minidom import parseString
import engine as eg

log = logging.getLogger("crawler")
engine = eg.SohuEngine()

MAX_TRY = 1

class Programme(eg.ProgrammeBase):
    def __init__(self):
        self.title= ""
        self.href = ""
        self.playlist_id = ""
        self.db = None
        self.item = {'href': "",
                     'pic' : "",
                     'playlist_id' : ""
                    }
        self.videolist = []

    def update(self):
        pass

    def show(self):
        print json.dumps(self.item)

    def update_videolist(self, times = 0):
        # print "Update VideoList: ", self.playlist_id, "href=", self.href
        if times > MAX_TRY or self.href == "":
            return

        try:
            if self.playlist_id == "" :
                _, _, _, response = fetch(self.href)
                if response == None:
                    print "error url: ", self.href
                    return
                id = re.findall('(var PLAYLIST_ID|playlistId)\s*="(\d+)', response)
                if id:
                    self.playlist_id = id[0][1]
                else:
                    # 多部电视情况
                    return
            newurl = 'http://hot.vrs.sohu.com/vrs_videolist.action?playlist_id=%s' % self.playlist_id
            #print newurl
            _, _, _, response = fetch(newurl)
            oflvo = re.search('var vrsvideolist \= (\{.*.\})', response.decode('gb18030')).group(1)

            if not oflvo:
                return

            jdata = json.loads(oflvo.decode('utf-8'))
            self.videolist = jdata['videolist']
            #for a in self.videolist:
            #    print a['videoImage'], a['videoName'], a['videoOrder'], a['videoId']
            self.item['videolist'] = json.dumps(self.videolist, ensure_ascii = False)

        except:
            t, v, tb = sys.exc_info()
            log.error("SohuGetVideoList:  %s, %s,%s,%s" % (self.href, t, v, traceback.format_tb(tb)))
            self.update_videolist(times + 1)

    def post(self, segname, db = None):
        if db == None:
            db = self.db
        if db == None:
            return
        title = "title:%s" % self.playlist_id
        db.rpush(segname, title)
        for x in self.item:
            db.hset(title, x, self.item[x])

    def parser(self, tag):
        x = tag.findNext("a", {'class' : 'pic'})
        if x:
            urls = re.findall('(href|img src)="(\S+)"', x.prettify())
            for u in urls:
                if u[0] == 'href':
                    self.href = u[1]
                    self.item['href'] = u[1]
                elif u[0] == 'img src':
                    self.item['pic'] = u[1]
                    newid = re.findall('(vrsab_ver|vrsab)([0-9]+)', u[1])
                    if len(newid) > 0:
                        self.playlist_id = newid[0][1]
                        self.item['playlist_id'] = self.playlist_id

        x = tag.findNext('em', {'class' : 'super'})
        if x:
            self.item['super'] = x.contents[0]

        x = tag.findNext('i')
        if x:
            self.item['update'] = x.contents[0]

        x = tag.findNext('p', {'class' : 'tit tit-p'}).contents[0]
        if x:
            self.title = x.contents[0].decode('utf-8')
            self.item['title'] = x.contents[0].decode('utf-8')

        x = tag.findNext('p', {'class' : 'desc'})
        if x:
            self.item['desc'] = x.contents[0].decode('utf-8')

        x = tag.findNext("span", {'class' : 'pmt2'})
        if x:
            self.item['publish'] = x.contents[0]
#        self.update_videolist()

class Kolatv:
    def __init__(self):
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=4)
        self.MenuList = []

    def UpdateMainMenu(self):
        self.MenuList = engine.GetMenu()
        for m in self.MenuList:
            m.UpdateHotList()
            m.UpdateAllProgramme()

    def FindMenu(self, name):
        for t in self.Menu:
            if t.name == name:
                return t

        return None

def main():
    tv = Kolatv()
    tv.UpdateMainMenu() # 更新主菜单
    return

    url_all = [
        'http://so.tv.sohu.com/list_p11_p2_p3_p4-1_p5_p6_p70_p80_p9_2d2_p101_p11.html',    # 电影
        'http://so.tv.sohu.com/list_p1101_p2_p3_p4_p5_p6_p7_p8_p9.html',    # 电视剧
        'http://so.tv.sohu.com/list_p1115_p2_p3_p4_p5_p6_p7_p8_p9.html'    # 动漫
        'http://so.tv.sohu.com/list_p1115_p20_p3_p40_p50_p6-1_p77_p8_p9_d20_p109_p110.html'
      ]
    for url in url_all:
        AddCommand(url, 'http://127.0.0.1:9991/video/upload', "test")

    return

if __name__ == "__main__":
    main()

