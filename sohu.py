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

log = logging.getLogger("crawler")

MAX_TRY = 1

SOHU_HOST = 'tv.sohu.com'

def AddCommand(source, dest, title):
    cmd_server = 'http://127.0.0.1:9990/video/addcommand'
    command = {
        'source': source,
        'dest': dest,
        'menu': title
    }
    _, _, _, response = fetch(cmd_server, 'POST', json.dumps(command))

def GetSoHuInfo(host, prot, tfile, new, times=0):
    if times > MAX_TRY:
        return
    try:
        url = 'http://%s/?prot=%s&file=%s&new=%s' % (host, prot, tfile, new)
        _, _, _, response = fetch(url)
        start, _, host, key, _, _, _, _ = response.split('|')
        return '%s%s?key=%s' % (start[:-1], new, key)
    except:
        t, v, tb = sys.exc_info()
        log.error("GetSoHuInfo %s,%s,%s" % (t, v, traceback.format_tb(tb)))
        return GetSoHuInfo(host, prot, tfile, new, times + 1)

def GetSoHuRealUrl(playurl, times=0):
    res = []
    if times > MAX_TRY:
        return res
    try:
        _, _, _, response = fetch(playurl)
        vid = re.search('vid="(\d+)', response).group(1)
        newurl = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
        #print newurl
        _, _, _, response = fetch(newurl)
        jdata = json.loads(response)
        host = jdata['allot']
        prot = jdata['prot']
        urls = []
        data = jdata['data']
        title = data['tvName']
        size = sum(data['clipsBytes'])
        for tfile, new in zip(data['clipsURL'], data['su']):
            urls.append(GetSoHuInfo(host, prot, tfile, new))
        if len(urls) == 1:
            url = urls[0]
            res.append(['', url])
        else:
            for url in urls:
                res.append(['', url])
        return res
    except:
        t, v, tb = sys.exc_info()
        log.error("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))
        return GetSoHuRealUrl(playurl, times + 1)

def GetRealPlayUrl(playurl, times=0):
    res = []
    if times > MAX_TRY:
        return res
    _, netloc, _, _, _, _ = urlparse(playurl)
    if netloc == SOHU_HOST:
        result = GetSoHuRealUrl(playurl)
        res.extend(result)

    return res

class Video:
    def __init__(self):
        pass

class Programme:
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

class VideoMenuBase:
    def __init__(self, name, engine, url):
        self.name = name
        self.url = url
        self.hotList = []
        self.grogramme_list = []
        self.HomeUrlList = []
        self.engine = engine

        self.UpdateHotList()

    # 更新所有节目
    def UpdateAllProgramme(self):
        for url in self.HomeUrlList:
            self.engine.GetHtmlList(self.name, url)
            #engine.GetProgramme(url)

    # 更新热门节目表
    def UpdateHotList(self):
        try:
            _, _, _, response = fetch(self.url)
            soup = bs(response)

            playlist = soup.findAll('script')
            for a in playlist:
                urls = re.search('focslider', a.prettify())
                if urls:
                    data = re.findall('data: *([\s\S]*])', a.prettify()\
                                      .replace('http:', 'httx:')\
                                      .replace('p:', '"p":')\
                                      .replace('httx:', 'http:')\
                                      .replace('p1:', '"p1":')\
                                      .replace('l:', '"l":')\
                                      .replace('t:', '"t":')\
                                      .replace('\'', '"')\
                                      .replace('\n', '')\
                                      .replace('\t', '')\
                                      .replace(' ', '')\
                                      .replace('#', '0x')\
                                      .replace('bgcolor', '"bgcolor"'))
                    if data:
                        x = json.loads(data[0])
                        for a in x:
                            one = {}
                            one['large_image'] = a['p']
                            one['small_image'] = a['p1']
                            one['url']         = a['l']
                            one['title']       = a['t']
                            self.hotList.append(one)
                            print a['t']

        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (self.url, t, v, traceback.format_tb(tb)))

    def show(self):
        pass

class Movie(VideoMenuBase):
    def __init__(self, name, engine, url):
        VideoMenuBase.__init__(self, name, engine, url)
        self.HomeUrlList = [
#            'http://so.tv.sohu.com/list_p1100_p20_p3_p42013_p5_p6_p77_p80_p9_2d0_p101_p11.html',
#            'http://so.tv.sohu.com/list_p1100_p20_p3_p42012_p5_p6_p77_p80_p9_2d0_p101_p11.html',
#            'http://so.tv.sohu.com/list_p1100_p20_p3_p42011_p5_p6_p77_p80_p9_2d0_p101_p11.html',
#            'http://so.tv.sohu.com/list_p1100_p20_p3_p42010_p5_p6_p77_p80_p9_2d0_p101_p11.html'
#            'http://so.tv.sohu.com/list_p1100_p20_p3_p411_p5_p6_p77_p80_p9_2d0_p101_p11.html',
#            'http://so.tv.sohu.com/list_p1100_p20_p3_p490_p5_p6_p77_p80_p9_2d0_p101_p11.html',
#            'http://so.tv.sohu.com/list_p1100_p20_p3_p480_p5_p6_p77_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p41_p5_p6_p77_p80_p9_2d0_p103_p11.html']


class Sohu:
    def __init__(self):
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=4)


def main():
    engine = SohuEngine()
    engine.GetMenu()
    engine.SaveMenu()

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

