#! env /usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
reload(sys)
sys.setdefaultencoding("utf-8")
f_path = os.path.dirname(__file__)
if len(f_path) < 1: f_path = "."
sys.path.append(f_path)
sys.path.append(f_path + "/..")

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

LIST_URL_TYPE = 'LIST_URL'
ITEM_URL_TYPE = 'ITEM_URL'
REAL_URL_TYPE = 'REAL_URL'

PARSE_TYPE = 1

MAX_TRY = 10

BASE_URL = 'http://v.baidu.com/movie_intro/?dtype=moviePlaySource&service=json&id=%d'
SUPPORT_URL = 'http://v.baidu.com/v?rn=10&word=%s&ct=905969666'


BAIY_HOST = 'www.baiy.net'
AIPAI_HOST = 'www.aipai.com'
WL_HOST = 'www.56.com'
UK_HOST = 'v.youku.com'
SOHU_HOST = 'tv.sohu.com'
KUSIX_HOST = 'v.ku6.com'
TUDOU_HOST = 'www.tudou.com'


def zip_data(data):
    return base64.b64encode(zlib.compress(data, zlib.Z_BEST_SPEED))

def GetBaiyRealUrl(playurl, times=0):
    res = []
    if times > MAX_TRY:
        return res
    try:
        _, _, _, response = fetch(playurl)
        soup = bs(response)
        playlist = soup.findAll('ul', id="playlist")
        if playlist:
            newplayurl = playlist[0].script['src']
            if newplayurl:
                url = 'http://' + BAIY_HOST + newplayurl
                _, _, _, response = fetch(url)
                uri = re.findall("(?<=unescape\(').*.(?='\);)", response)[0]
                info = urllib.unquote(uri)
                for s in info.split('$$$'):
                    res.extend([s.split('$')])
        return res
    except:
        t, v, tb = sys.exc_info()
        log.error("GetBaiyRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))
        return GetBaiyRealUrl(playurl, times + 1)

def GetAiPaiRealUrl(playurl, times=0):
    res = []
    if times > MAX_TRY:
        return res
    try:
        _, _, _, response = fetch(playurl)
        assetpurl = re.findall("(?<=asset_pUrl \= \').*.(?=\'\;)", response)
        if assetpurl:
            realurl = assetpurl[0].replace('iphone.aipai.com/', '').replace('card.m3u8', 'card.flv')
            res.append(['', realurl])
        return res
    except:
        t, v, tb = sys.exc_info()
        log.error("GetAiPaiRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))
        return GetAiPaiRealUrl(playurl, times + 1)

def GetWlRealUrl(playurl, times=0):
    res = []
    if times > MAX_TRY:
        return res
    try:
        _, _, _, response = fetch(playurl)
        oflvo = re.findall('(?<=var _oFlv_o \= )\{.*.\}(?=;)', response)
        if not oflvo:
            return res

        jdata = json.loads(oflvo[0])
        pid = jdata['id']
#         pid = re.findall('(?<=var _oFlv_o \= \{\"id\"\:\")\d+(?=\",\")', response)
        if pid:
#             pid = pid[0]
            url = 'http://vxml.56.com/json/%d/?src=site' % (int(pid))
            _, _, _, response = fetch(url)
            jdata = json.loads(response)
            rfiles = jdata['info']['rfiles']
            for rf in rfiles:
                realurl = rf['url']
                playtype = rf['type']  # 可能是清晰度
                res.append(['', realurl])
        return res
    except:
        t, v, tb = sys.exc_info()
        log.error("GetWlRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))
        return GetWlRealUrl(playurl, times + 1)

def FindUKVideo(info, stream_type=None, times=0):
    segs = info['data'][0]['segs']
    types = segs.keys()
    if not stream_type:
        for x in ['hd2', 'mp4', 'flv']:
            if x in types:
                stream_type = x
                break
        else:
            raise NotImplementedError()
    file_type = {'hd2':'flv', 'mp4':'mp4', 'flv':'flv'}[stream_type]

    seed = info['data'][0]['seed']
    source = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\\:._-1234567890")
    mixed = ''
    while source:
        seed = (seed * 211 + 30031) & 0xFFFF
        index = seed * len(source) >> 16
        c = source.pop(index)
        mixed += c

    ids = info['data'][0]['streamfileids'][stream_type].split('*')[:-1]
    vid = ''.join(mixed[int(i)] for i in ids)

    sid = '%s%s%s' % (int(time.time() * 1000), randint(1000, 1999), randint(1000, 9999))

    urls = []
    for s in segs[stream_type]:
        no = '%02x' % int(s['no'])
        url = 'http://f.youku.com/player/getFlvPath/sid/%s_%s/st/%s/fileid/%s%s%s?K=%s&ts=%s' % (sid, no, file_type, vid[:8], no.upper(), vid[10:], s['k'], s['seconds'])
        urls.append((url, int(s['size'])))
    return urls

def GetUKInfo(videoId2, times=0):
    if times > MAX_TRY:
        return None
    try:
        url = 'http://v.youku.com/player/getPlayList/VideoIDS/%s' % (videoId2)
        _, _, _, response = fetch(url)
        return json.loads(response)
    except:
        return GetUKInfo(videoId2, times + 1)

def GetUKouRealUrl(playurl, times=0):
    res = []
    if times > MAX_TRY:
        return res
    try:
        _, _, _, response = fetch(playurl)
        id2 = re.search(r"var\s+videoId2\s*=\s*'(\S+)'", response).group(1)
        info = GetUKInfo(id2)
        urls, _ = zip(*FindUKVideo(info, stream_type=None))
        if len(urls) == 1:
            url = urls[0]
            _, _, location, response = fetch(url)
            res.append(['', location])
        else:
            for url in urls:
                _, _, location, response = fetch(url)
                res.append(['', location])
                time.sleep(2)
        return res
    except:
        t, v, tb = sys.exc_info()
        log.error("GetUKouRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))
        return GetUKouRealUrl(playurl, times + 1)

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

def GetKuSixRealUrl(playurl, times=0):
    res = []
    if times > MAX_TRY:
        return res
    try:
        _, _, _, response = fetch(playurl)
        data = re.findall('data: {.*.} }\,', response)
        if data:
            data = data[0][5:-2]
            jdata = json.loads(data)
            t = jdata['data']['t']
            f = jdata['data']['f']
            size = jdata['data']['videosize']
            res.append(['', f])
        return res
    except:
        t, v, tb = sys.exc_info()
        log.error("GetKuSixRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))
        return GetKuSixRealUrl(playurl, times + 1)

def GetTuDouRealUrl(playurl, times=0):
    res = []
    if times > MAX_TRY:
        return res
    try:
        _, _, _, response = fetch(playurl)
        iid = re.search(r'iid\s*[:=]\s*(\d+)', response).group(1)
        title = re.search(r"kw\s*[:=]\s*'([^']+)'", response.decode('gb18030')).group(1)
        _, _, _, response = fetch('http://v2.tudou.com/v?it=' + iid + '&st=1,2,3,4,99')
        doc = parseString(response)
        title = title or doc.firstChild.getAttribute('tt') or doc.firstChild.getAttribute('title')
        urls = [(int(n.getAttribute('brt')), n.firstChild.nodeValue.strip()) for n in doc.getElementsByTagName('f')]
        url = max(urls, key=lambda x:x[0])[1]
        print url
        if len(urls) == 1:
            url = urls[0]
            res.append(['', url])
        else:
            for url in urls:
                res.append(['', url[1]])
        return res
    except:
        t, v, tb = sys.exc_info()
        log.error("GetTuDouRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))
        return GetTuDouRealUrl(playurl, times + 1)

def GetRealPlayUrl(playurl, times=0):
    res = []
    if times > MAX_TRY:
        return res
    _, netloc, _, _, _, _ = urlparse(playurl)
    if netloc == BAIY_HOST:
        result = GetBaiyRealUrl(playurl)
        for _, _, lang, realurl, _ in result:
            lang = urllib.unquote(lang).decode("utf-8").replace('%', '\\').decode('unicode_escape').encode('utf-8')
            res.append([lang, realurl])
    elif netloc == AIPAI_HOST:
        result = GetAiPaiRealUrl(playurl)
        res.extend(result)
    elif netloc == WL_HOST:
        result = GetWlRealUrl(playurl)
        res.extend(result)
    elif netloc == UK_HOST:
        result = GetUKouRealUrl(playurl)
        res.extend(result)
    elif netloc == SOHU_HOST:
        result = GetSoHuRealUrl(playurl)
        res.extend(result)
    elif netloc == KUSIX_HOST:
        result = GetKuSixRealUrl(playurl)
        res.extend(result)
    elif netloc == TUDOU_HOST:
        result = GetTuDouRealUrl(playurl)
        res.extend(result)

    return res

class Film:
    def __init__(self):
        pass

class Teleplay:
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
        self.update_videolist()

class Drama:
    def __init__(self, url):
        self.url = url
        self.hotList = []
        self.parser()

    def parser(self):
        try:
            _, _, _, response = fetch(self.url)
            soup = bs(response)
            playlist = soup.findAll('script')

            for a in playlist:
                urls = re.search('focslider', a.prettify())
                if urls:
                    data = re.findall('data: *([\s\S]*])', \
                                     a.prettify()\
                                     .replace('{p:', '{"p":')\
                                     .replace('p1:', '"p1":')\
                                     .replace('l:', '"l":')\
                                     .replace('t:', '"t":')\
                                     .replace('\'', '"')\
                                     .replace('#000000', '0')\
                                     .replace('bgcolor :', '"bgcolor":'))

                    if data:
                        x = json.loads(data[0].decode('utf-8'))
                        for a in x:
                            print a['p'], a['t']

        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (self.url, t, v, traceback.format_tb(tb)))

    def show(self):
        print "aaaaaaaaaa: ", self.url
class SohuVideo:
    def __init__(self):
        self.base_url = ""
        self.teleplay_list = []
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=4)
        self.title = "title:tv"
        self.menu = {"电影" : Drama, "电视剧" : Drama, "综艺" : Drama, "娱乐"
                     : Drama, "动漫": Drama, "纪录片": Drama}
        self.tv = []

    def StartUpdate(self):
        self.db.flushdb()

    def EndUpdate(self):
        self.db.save()

    def GetMenu(self):
        playurl = "http://tv.sohu.com"

        try:
            _, _, _, response = fetch(playurl)
            soup = bs(response)
            playlist = soup.findAll('dt')
            for a in playlist:
                urls = re.findall('(href|title)="(\S+)"', a.prettify())
                if len(urls) > 1:
                    if (urls[1][1] in self.menu):
                        t = self.menu[urls[1][1]](urls[0][1])
                        self.tv.append(t)
                        t.show()
                        break
        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))

    def GetTeleplay(self, playurl):
        protocol, host, _, _, _, _ = urlparse(playurl)
        self.base_url = protocol + "://" + host

        try:
            _, _, _, response = fetch(playurl)
            soup = bs(response)
            playlist = soup.findAll('li', {'class' : 'clear'})

            for a in playlist:
                tv = Teleplay()
                tv.parser(a)
                tv.post(self.title, self.db)

                print "title:%s" % tv.playlist_id, ": ", self.db.hgetall("title:%s" % tv.playlist_id)['title']
            nextPage = soup.findAll('a', {'class' : 'next'})
            if nextPage:
                next_url = re.findall('href="(\S+)"', nextPage[0].prettify())
                if next_url:
                    next_url = self.base_url + next_url[0]
                    self.GetTeleplay(next_url)
        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))

def main():
    sohu = SohuVideo()
    sohu.GetMenu()
    return
    sohu.StartUpdate()


    url_all = [
        #'http://so.tv.sohu.com/list_p11_p2_p3_p4-1_p5_p6_p70_p80_p9_2d2_p101_p11.html',    # 电影
        #'http://so.tv.sohu.com/list_p1101_p2_p3_p4_p5_p6_p7_p8_p9.html',    # 电视剧
        #'http://so.tv.sohu.com/list_p1115_p2_p3_p4_p5_p6_p7_p8_p9.html'    # 动漫
        'http://so.tv.sohu.com/list_p1115_p20_p3_p40_p50_p6-1_p77_p8_p9_d20_p109_p110.html'
      ]

    for url in url_all:
        sohu.GetTeleplay(url)

    sohu.EndUpdate()

if __name__ == "__main__":
    main()

