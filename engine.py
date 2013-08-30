#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import traceback
import sys, os
import json
#import BeautifulSoup as bs
from utils.BeautifulSoup import BeautifulSoup as bs
import urllib
from utils.fetchTools import fetch_httplib2 as fetch
import base64, zlib
import re
from urllib2 import HTTPError
from urlparse import urlparse

logging.basicConfig()
log = logging.getLogger("crawler")

MAX_TRY = 1

class VideoEngine:
    def __init__(self):
        self.base_url = ''
        self.tv = []
        self.title = "title:tv"
        self.menu = {}

    # 获取节目一级菜单, 返回分类列表
    def GetMenu(self):
        return None

    # 生成所有分页网址, 返回网址列表
    def GetHtmlList(self, playurl, times = 0):
        return None

    # 解析一页节目单, 返回该页上节目列表
    def ParserHtml(self, text):
        return None

    def FindMenu(self, name):
        for t in self.tv:
            if t.name == name:
                return t

        return None

class SohuEngine(VideoEngine):
    def __init__(self):
        VideoEngine.__init__(self)

        self.base_url = "http://so.tv.sohu.com"

#        self.menu = {"电影" : "",
#                     "电视剧" : "",
#                     "综艺" : "",
#                     "娱乐" : "",
#                     "动漫" : "",
#                     "纪录片" : "",
#                    }

    def GetMenu(self):
        ret = []
        playurl = "http://tv.sohu.com"

        try:
            _, _, _, response = fetch(playurl)
            soup = bs(response)
            playlist = soup.findAll('dt')
            for a in playlist:
                urls = re.findall('(href|title)="(\S+)"', a.prettify())
                if len(urls) > 1:
                    menu_name = urls[1][1]
                    if (menu_name in self.menu):
                        base_url = urls[0][1]
                        t = self.menu[menu_name](menu_name, self, base_url)
                        t.UpdateAllProgramme()
                        ret.append(t)
        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s" % (playurl, t, v, traceback.format_tb(tb)))

        return ret

    def ParserHtml(self, text):
        ret = []
        soup = bs(text)
        playlist = soup.findAll('li', {'class' : 'clear'})

        for a in playlist:
            tv = Programme()
            tv.parser(a)
            tv.post(self.title, self.db)
            ret.append(tv)

            print ("title:%s" % tv.playlist_id, ": ", self.db.hgetall("title:%s" % tv.playlist_id)['title'])
        return ret

    def GetHtmlList(self, playurl, times = 0):
        ret = []
        count = 0
        if times > MAX_TRY:
            return ret
        try:
            #print playurl
            _, _, _, response = fetch(playurl)

            soup = bs(response)
            data = soup.findAll('span', {'class' : 'c-red'})
            if data and len(data) > 1:
                count = int(data[1].contents[0])
                count = (count + 20 -1 ) / 20
                if count > 200:
                    count = 200

            current_page = 0
            g = re.search('p10(\d+)', playurl)
            if g:
                current_page = int(g.group(1))

            for i in range(1, count + 1):
                if i != current_page:
                    link=re.compile('p10\d+')
                    newurl = re.sub(link, 'p10%d' % i, playurl)
                    print newurl
                    ret.append(newurl)

                    # 将需要解析的地址提交至解析服务器
                    #AddCommand(newurl, 'http://127.0.0.1:9991/video/upload', "")

        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))
            self.GetHtmlList(menu, playurl, times + 1)

        return ret;

def test():
    engine = SohuEngine()
    engine.GetHtmlList('http://so.tv.sohu.com/list_p1100_p20_p3_p41_p5_p6_p77_p80_p9_2d0_p103_p11.html')

if __name__ == "__main__":
    test()
