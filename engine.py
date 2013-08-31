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

def AddCommand(command):
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
        self.albumName = ""
        self.url = ""
        self.pid = ""
        self.vid = ""
        self.playlist_id = ""
        self.filmType = "" # "TV" or ""
        self.data = {}
        self.tvSets = "" # 最新集数
        self.dailyPlayNum    = 0 # 每日播放次数
        self.weeklyPlayNum   = 0 # 每周播放次数
        self.monthlyPlayNum  = 0 # 每月播放次数
        self.totalPlayNum    = 0 # 总播放资料
        self.dailyIndexScore = 0 # 每日指数

    def update_videolist(self, times = 0):
        pass

    # 更新该节目信息
    def UpdateInfo(self, times = 0):
        pass

    def post(self):
        pass

# 一级分类菜单
class VideoMenuBase:
    def __init__(self, name, engine, url):
        self.name = name
        self.url = url
        self.HotList = []
        self.HomeUrlList = []
        self.engine = engine
        self.regular = '(.*)'

    def Reset(self):
        self.HotList = []

    # 更新热门节目表
    def UpdateHotList(self):
        self.HotList = []
        self.engine.UpdateHotList(self)

    # 更新本菜单节目网址，并提交命令服务器
    def UploadProgrammeList(self):
        for url in self.HomeUrlList:
            for page in self.engine.GetHtmlList(url):
                cmd = {
                    'source': page,
                    'dest': PARSER_HOST,
                    'menu': self.name,
                    'regular': self.regular
                }

                AddCommand(cmd)

class VideoEngine:
    def __init__(self):
        self.engine_name = "EngineBase"
        self.programme_class = ProgrammeBase

    # 获取节目一级菜单, 返回分类列表
    def GetMenu(self, times = 0):
        return []

    # 生成所有分页网址, 返回网址列表
    def GetHtmlList(self, playurl, times = 0):
        return []

    # 获取真实播放节目源地址
    def GetRealPlayUrl(self, playurl, times = 0):
        return []

    # 更新一级菜单首页热门节目表
    def UpdateHotList(self, menu, times = 0):
        pass

    # 获取节目的播放列表
    def GetProgrammePlayList(self, programme, times = 0):
        pass

    # 将 BeautifulSoup的节目 tag 转成节目单
    def ParserProgramme(self, tag, programme):
       return False

    # 解析一页节目单, 返回该页上节目列表
    def ParserHtml(self, text):
        return []

#================================= 以下是 搜索视频的搜索引擎 =======================================
SOHU_HOST = 'tv.sohu.com'

class SohuProgramme(ProgrammeBase):
    def __init__(self):
        ProgrammeBase.__init__(self)

    # 更新该节目信息
    def UpdateInfo(self, times = 0):
        if times > MAX_TRY:
            return
        if self.playlist_id != '':
            try:
                playurl = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=%s' % self.playlist_id
                playurl = 'http://index.tv.sohu.com/index/switch-aid/%s' % self.playlist_id
                _, _, _, response = fetch(playurl)

                data = json.loads(response)
                if data and data.has_key('attachment'):
                    album = data['attachment']['album']
                    if album:
                        self.albumName = album['albumName']

                    index = data['attachment']['index']
                    if index:
                        self.dailyPlayNum = int(index['dailyPlayNum']) # 每日播放次数
                        self.dailyIndexScore = float(index['dailyIndexScore']) # 每日指数

                print "UpdateInfo: albumName=", self.albumName, \
                        "dailyPlayNum=", self.dailyPlayNum, \
                        "dailyIndexScore=", self.dailyIndexScore
            except:
                t, v, tb = sys.exc_info()
                log.error("GetSoHuRealUrl playurl:  %s, %s,%s, %s" % (playurl, t, v, traceback.format_tb(tb)))
                self.UpdateInfo(times + 1)

class SohuVideoMenu(VideoMenuBase):
    def __init__(self, name, engine, url):
        VideoMenuBase.__init__(self, name, engine, url)
        self.regular = '(<a class="pic" target="_blank" title=".+/></a>)'

class SohuMovie(SohuVideoMenu):
    def __init__(self, name, engine, url):
        SohuVideoMenu.__init__(self, name, engine, url)
        self.HomeUrlList = [
            'http://so.tv.sohu.com/list_p1100_p20_p3_p42013_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p42012_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p42011_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p42010_p5_p6_p73_p80_p9_2d0_p101_p11.html'
            'http://so.tv.sohu.com/list_p1100_p20_p3_p411_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p490_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p480_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p41_p5_p6_p73_p80_p9_2d0_p103_p11.html'
        ]

# Sohu 搜索引擎
class SohuEngine(VideoEngine):
    def __init__(self):
        VideoEngine.__init__(self)
        self.programme_class = SohuProgramme

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

    def GetMenu(self, times = 0):
        ret = {}
        playurl = "http://tv.sohu.com"

        if times > MAX_TRY:
            return ret

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
                            ret[menu_name.decode('utf-8')] = t
        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s, %s" % (playurl, t, v, traceback.format_tb(tb)))
            return self.GetMenu(times + 1)

        return ret

    def ParserHtml(self, text):
        ret = []
        soup = bs(text)
        playlist = soup.findAll('a')

        for tag in playlist:
            tv = self.programme_class()
            if self.ParserProgramme(tag, tv):
                tv.UpdateInfo() # 更新节目信息
                ret.append(tv)

            #print ("title:%s" % tv.playlist_id, ": ", self.db.hgetall("title:%s" % tv.playlist_id)['title'])
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
            return self.GetHtmlList(playurl, times + 1)

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
        if times > MAX_TRY:
            return ret
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
                            menu.HotList.append(one)
                            print a['t']

        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (menu.url, t, v, traceback.format_tb(tb)))
            self.UpdateHotList(menu, times + 1)

    def ParserProgramme(self, tag, programme):
        ret = False
        if tag == None or programme == None:
            return False

        x = tag.findNext("a", {'class' : 'pic'})
        if x:
            urls = re.findall('(href|img src)="(\S+)"', x.prettify())
            for u in urls:
                if u[0] == 'href':
                    programme.url = u[1]
                    try:
                        ids = re.search('(\d+)_(\d+)',u)
                        if ids:
                            pid = ids.group(1)
                            vid = ids.group(2)
                            ret = True
                    except:
                        pass
                elif u[0] == 'img src':
                    newid = re.findall('(vrsab_ver|vrsab)([0-9]+)', u[1])
                    if len(newid) > 0:
                        programme.playlist_id = newid[0][1]
                        ret = True
            if ret == False and programme.url != "":
                _, _, _, response = fetch(programme.url)
                rlist = re.findall('var (playlistId|pid|vid)\s*="(\d+)', response)
                if rlist:
                    for r in rlist:
                        if r[0] == 'vid':
                            programme.vid = r[1]
                        elif r[0] == 'pid':
                            programme.pid = r[1]
                        elif r[0] == 'playlistId':
                            programme.playlist_id = r[1]
                    ret = True

        return ret

    # 获取节目的播放列表
    def GetProgrammePlayList(self, programme, times = 0):
        if times > MAX_TRY or programme.url == "":
            return

        try:
            if programme.playlist_id == "" :
                _, _, _, response = fetch(programme.url)
                if response == None:
                    print "error url: ", programme.url
                    return
                id = re.findall('(var PLAYLIST_ID|playlistId)\s*="(\d+)', response)
                if id:
                    programme.playlist_id = id[0][1]
                else:
                    # 多部电视情况
                    return
            newurl = 'http://hot.vrs.sohu.com/vrs_videolist.action?playlist_id=%s' % programme.playlist_id
            #print newurl
            _, _, _, response = fetch(newurl)
            oflvo = re.search('var vrsvideolist \= (\{.*.\})', response.decode('gb18030')).group(1)

            if not oflvo:
                return

            jdata = json.loads(oflvo.decode('utf-8'))
            programme.videolist = jdata['videolist']

        except:
            t, v, tb = sys.exc_info()
            log.error("SohuGetVideoList:  %s, %s,%s,%s" % (programme.url, t, v, traceback.format_tb(tb)))
            self.GetProgrammePlayList(programme, times + 1)

def test():
    url = 'http://so.tv.sohu.com/list_p1100_p20_p3_p41_p5_p6_p73_p80_p9_2d0_p103_p11.html'
    _, _, _, response = fetch(url)
    soup = bs(response)
    playlist = soup.findAll('a', {'class' : 'pic'}) # <a class="pic"
    for a in playlist:
        print a

    print "\n\n\n\n"
    playlist = re.findall('(<a class="pic" target="_blank" title=".+/></a>)', response)
    playlist = re.findall('(.*)', response)
    for a in playlist:
        print a
    return

    url= 'http://index.tv.sohu.com/index/switch-aid/5497903'
    url= 'http://index.tv.sohu.com/index/switch-aid/243'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii = False, indent = 4)
    return
    url= 'http://search.vrs.sohu.com/avs_i1268037_pr380470620_o2_n_p1000_chltv.sohu.com.json'
    _, _, _, response = fetch(url)
    oflvo = re.search('var video_album_videos_result=(\{.*.\})', response).group(1)
    a = json.loads(oflvo)
    print json.dumps(a, ensure_ascii = False, indent = 4)
    return

    url ='http://search.vrs.sohu.com/v?id=1268036&pageSize=200000&pageNum=1'
    url ='http://search.vrs.sohu.com/v?id=1268037&pid=5497903&pageNum=1&pageSize=50&isgbk=true&var=video_similar_search_result'
    _, _, _, response = fetch(url)
    oflvo = re.search('var video_similar_search_result=(\{.*.\})', response).group(1)
    a = json.loads(oflvo)
    print json.dumps(a, ensure_ascii = False, indent = 4)
    return

    url = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5112241'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii = False, indent = 4)
    return
    url = 'http://so.tv.sohu.com/iapi?v=4&c=101&t=1&area=%u5185%u5730&o=3&pagenum=1&pagesize=3'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii = False, indent = 4)


    url = 'http://so.tv.sohu.com/jsl?c=100&area=12_25&o=1'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii = False, indent = 4)
    print len(a['r'])
    return
    url = 'http://so.tv.sohu.com/jsl?c=100&cate=100100_100107&o=1&pageSize=1'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii = False, indent = 4)
    return

    engine = SohuEngine()
    engine.GetMenu()
    #engine.GetHtmlList('http://so.tv.sohu.com/list_p1100_p20_p3_p41_p5_p6_p73_p80_p9_2d0_p103_p11.html')
    return engine

def test_addcommand():
    url_all = [
        'http://so.tv.sohu.com/list_p11_p2_p3_p4-1_p5_p6_p70_p80_p9_2d2_p101_p11.html',    # 电影
        'http://so.tv.sohu.com/list_p1101_p2_p3_p4_p5_p6_p7_p8_p9.html',    # 电视剧
        'http://so.tv.sohu.com/list_p1115_p2_p3_p4_p5_p6_p7_p8_p9.html'    # 动漫
        'http://so.tv.sohu.com/list_p1115_p20_p3_p40_p50_p6-1_p73_p8_p9_d20_p109_p110.html'
      ]
    for url in url_all:
        AddCommand(url, 'http://127.0.0.1:9991/video/upload', "test")

if __name__ == "__main__":
    #u = 'http://store.tv.sohu.com/view_html/5800313_1298146.html'
    #print re.search('(\d+)_(\d+)',u)
    #print re.search('(\d+)_(\d+)',u).group(1)
    #print re.search('(\d+)_(\d+)',u).group(2)
    #re.search('(\d+)_(\d+)',u)
    test()
