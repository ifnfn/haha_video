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

COMMAND_HOST = 'http://127.0.0.1:9990/video/addcommand'
PARSER_HOST  = 'http://127.0.0.1:9991/video/upload'

MAX_TRY = 1

def AddCommand(source, dest, title):
    command = {
        'source': source,
        'dest': dest,
        'menu': title
    }
    _, _, _, response = fetch(COMMAND_HOST, 'POST', json.dumps(command))

# 每个 Video 表示一个可以播放视频
class VideoBase:
    def __init__(self):
        pass

    # 获得播放视频源列表，返回m3u8
    def GetRealUrl(self, playurl):
        return ""

# 一个节目，表示一部电影、电视剧集
class ProgrammeBase:
    def __init__(self):
        self.title= ""
        self.href = ""
        self.playlist_id = ""
        self.db = None
        self.item = {'href': "",
                     'pic' : "",
                     'playlist_id' : ""
                    }

    def update_videolist(self, times = 0):
        pass

    def post(self):
        pass
        tv.post(self.title, self.db)

# 一级分类菜单
class VideoMenuBase:
    def __init__(self, name, engine, url):
        self.name = name
        self.url = url
        self.hotList = []
        self.grogramme_list = []
        self.HomeUrlList = []
        self.engine = engine

    def Reset(self):
        self.grogramme_list.clear()

    # 更新热门节目表
    def UpdateHotList(self):
        self.HotList.clear()
        self.engine.UpdateHotList(self)

    # 更新本菜单节目网址，并提交命令服务器
    def UploadProgrammeList(self):
        for url in self.HomeUrlList:
            for page in self.engine.GetHtmlList(url):
                AddCommand(page, PARSER_HOST,  self.name)

    # 将 解决HTML 文本，生成节目列表
    def ParserHtml(self, text):
        list = self.engine.ParserHtml(ProgrammeBase, text)
        if list:
            self.group.extend(list)

class VideoEngine:
    def __init__(self):
        self.engine_name = "EngineBase"
        self.base_url = ''
        self.tv = []
        self.title = "title:tv"
        self.menu = {}

    # 获取节目一级菜单, 返回分类列表
    def GetMenu(self):
        return []

    # 生成所有分页网址, 返回网址列表
    def GetHtmlList(self, playurl, times = 0):
        return []

    # 解析一页节目单, 返回该页上节目列表
    def ParserHtml(self, pg_class, text):
        return []

    # 获取真实播放节目源地址
    def GetRealPlayUrl(self, playurl, times = 0):
        return []

    # 更新一级菜单首页热门节目表
    def UpdateHotList(self, menu, times = 0):
        pass

    def ParserProgramme(self, tag):
       return None

SOHU_HOST = 'tv.sohu.com'

class SohuMovie(VideoMenuBase):
    def __init__(self, name, engine, url):
        VideoMenuBase.__init__(self, name, engine, url)
        self.HomeUrlList = [
            'http://so.tv.sohu.com/list_p1100_p20_p3_p42013_p5_p6_p77_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p42012_p5_p6_p77_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p42011_p5_p6_p77_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p42010_p5_p6_p77_p80_p9_2d0_p101_p11.html'
            'http://so.tv.sohu.com/list_p1100_p20_p3_p411_p5_p6_p77_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p490_p5_p6_p77_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p480_p5_p6_p77_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p41_p5_p6_p77_p80_p9_2d0_p103_p11.html']

# Sohu 搜索引擎
class SohuEngine(VideoEngine):
    def __init__(self):
        VideoEngine.__init__(self)

        self.engine_name = "SohuEngine"
        self.base_url = "http://so.tv.sohu.com"

        self.menu = {
            "电影"   : SohuMovie,
            "电视剧" : None,
            "综艺"   : None,
            "娱乐"   : None,
            "动漫"   : None,
            "纪录片" : None,
        }

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
                        u = urls[0][1]

                        if self.menu[menu_name]:
                            t = self.menu[menu_name](menu_name, self, u)
                            ret.append(t)
        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s, %s" % (playurl, t, v, traceback.format_tb(tb)))

        return ret

    def ParserHtml(self, pg_class, text):
        ret = []
        soup = bs(text)
        playlist = soup.findAll('li', {'class' : 'clear'})

        for tag in playlist:
            tv = pg_class()
            self.ParserProgramme(tag):
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
            print playurl
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
            return self.GetSoHuInfo(host, prot, tfile, new, times + 1)

    def GetRealUrl(self, playurl, times=0):
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
                urls.append(self.GetSoHuInfo(host, prot, tfile, new))
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
            return self.GetRealUrl(playurl, times + 1)

    def UpdateHotList(self, menu, times = 0):
        try:
            _, _, _, response = fetch(menu.url)
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
                            menu.hotList.append(one)
                            print a['t']

        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (menu.url, t, v, traceback.format_tb(tb)))
            self.UpdateHotList(menu, times + 1)

    def ParserProgramme(self, tag):
        ret = ProgrammeBase()

        x = tag.findNext("a", {'class' : 'pic'})
        if x:
            urls = re.findall('(href|img src)="(\S+)"', x.prettify())
            for u in urls:
                if u[0] == 'href':
                    ret.href = u[1]
                    ret.item['href'] = u[1]
                elif u[0] == 'img src':
                    ret.item['pic'] = u[1]
                    newid = re.findall('(vrsab_ver|vrsab)([0-9]+)', u[1])
                    if len(newid) > 0:
                        ret.playlist_id = newid[0][1]
                        ret.item['playlist_id'] = ret.playlist_id

        x = tag.findNext('em', {'class' : 'super'})
        if x:
            ret.item['super'] = x.contents[0]

        x = tag.findNext('i')
        if x:
            ret.item['update'] = x.contents[0]

        x = tag.findNext('p', {'class' : 'tit tit-p'}).contents[0]
        if x:
            ret.title = x.contents[0].decode('utf-8')
            ret.item['title'] = x.contents[0].decode('utf-8')

        x = tag.findNext('p', {'class' : 'desc'})
        if x:
            ret.item['desc'] = x.contents[0].decode('utf-8')

        x = tag.findNext("span", {'class' : 'pmt2'})
        if x:
            ret.item['publish'] = x.contents[0]

        return ret

def test():
    engine = SohuEngine()
    engine.GetMenu()
    engine.GetHtmlList('http://so.tv.sohu.com/list_p1100_p20_p3_p41_p5_p6_p77_p80_p9_2d0_p103_p11.html')
    return engine

if __name__ == "__main__":
    test()
