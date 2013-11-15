#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys, os
import traceback
import json
import re
import time, datetime
import hashlib
import tornado.escape
from urllib.parse import unquote
from xml.etree import ElementTree
import httplib2


from ThreadPool import ThreadPool
import utils
from kolaclient import KolaClient

class EPG:
    def __init__(self):
        self.start_time = 0
        self.end_time = 0
        self.name = ''
    def Show(self):
        s = datetime.datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S")
        e = datetime.datetime.fromtimestamp(self.end_time).strftime("%Y-%m-%d %H-%M-%S")
        print("\t\t%s:  %s -> %s" % (self.name, s, e))

class Channel:
    def __init__(self):
        self.cid = ''
        self.name = ''
        self.logo = ''
        self.epg = ''
        self.video_url = ''
        self.timestamp = time.time()
        self.epgs = []
    def Show(self):
        print("\t", self.cid, self.name, self.video_url)

    def GetCurrentEPG(self):
        t = time.time()
        for e in self.epgs:
            if t >= e.start_time and t < e.end_time:
                return e
        return None

    def GetNextEPG(self):
        t = time.time()
        ok = False
        for e in self.epgs:
            if ok:
                return e
            if t >= e.start_time and t < e.end_time:
                ok = True
        return None

class TVStation:
    def __init__(self):
        self.flag = ''
        self.name = ''
        self.vid  = ''
        self.channels = []
        self.logo1 = ''
        self.logo2 = ''
        self.haha = KolaClient()

    def Show(self):
        print(self.vid, self.name)

class ZJTV(TVStation):
    def __init__(self):
        super().__init__()
        self.area = '淅江省'
        self.GetChannel()

    def GetChannel(self):
        url = 'http://player.cztv.com/livetv/assets/channel.xml'
        text = self.haha.GetCacheUrl(url).decode()
        root = ElementTree.fromstring(text)
        programList = root.getiterator("program")

        for p in programList:
            for i in p.getchildren():
                ch = Channel()
                ch.cid = i.attrib['id']
                ch.name = i.attrib['name']
                if self.GetURL(ch):
                    self.GetEPG(ch, int(ch.timestamp/1000) + 72000)
                    self.channels.append(ch)
                    ch.Show()
                    e = ch.GetCurrentEPG()
                    if e: e.Show()
                    e = ch.GetNextEPG()
                    if e: e.Show()

    def GetEPG(self, ch, time):
        url = 'http://api.cztv.com/api/getEPGByChannelTime/%s/0/%d' % (ch.cid, time)
        text = self.haha.GetCacheUrl(url)
        jdata = tornado.escape.json_decode(text)
        if 'result' in jdata:
            ch.epgs.clear()
            for epg in jdata['result'][0]:
                e = EPG()
                e.start_time = epg['start_time']
                e.end_time   = epg['end_time']
                e.name       = epg['name']
                ch.epgs.append(e)

    def GetURL(self, ch):
        url = 'http://api.cztv.com/api/getCDNByChannelId/%s?domain=api.cztv.com' % ch.cid

        text = self.haha.GetCacheUrl(url)
        js = json.loads(text.decode())

        datarates = js['result']['datarates']
        if datarates != None:
            k, v = list(datarates.items())[0]
            ch.timestamp = int(float(js['result']['timestamp']) / 1000) * 1000
            ch.video_url = 'http://%s/channels/%s/%s.flv/live?%d' % (v[0], ch.cid, k, ch.timestamp)
            return True

        return False

class HZTV(TVStation):
    def __init__(self):
        super().__init__()
        self.area = '淅江省,杭州市'
        self.GetChannel()

    def GetChannel(self):
        for i in range(1, 60):
            url = 'http://api1.hoolo.tv/player/live/channel_xml.php?id=%d' % i
            text = self.haha.GetCacheUrl(url).decode()
            root = ElementTree.fromstring(text)
            ch = Channel()
            ch.cid = i
            ch.name = root.attrib['name']
            for p in root:
                if p.tag == 'video':
                    for item in p.getchildren():
                        if 'url' in item.attrib:
                            ch.video_url = item.attrib['url']
                            self.channels.append(ch)
                            ch.Show()
                            self.GetEPG(ch, time.time())
                            break

            e = ch.GetCurrentEPG()
            if e: e.Show()
            e = ch.GetNextEPG()
            if e: e.Show()

    def GetEPG(self, ch, time):
        url = 'http://api1.hoolo.tv/player/live/program_xml.php?channel_id=%d&time=%d' % (ch.cid, time)
        text = self.haha.GetCacheUrl(url).decode()
        root = ElementTree.fromstring(text)
        programList = root.getiterator("program")

        for p in programList:
            ch.epgs.clear()
            for epg in p.getchildren():
                e = EPG()
                e.start_time = int(epg.attrib['startTime'])
                e.end_time   = e.start_time + int(epg.attrib['duration'])
                e.name       = epg.attrib['name']
                ch.epgs.append(e)

class cutv(TVStation):
    def __init__(self):
        super().__init__()
        self.tvlist = []
        self.haha.GetUrl('http://tv.cutv.com/player/cv.swf?channelId=AxeFRth')
        x= url_post('http://liveapp.cutv.com/amf',
                    "cutvTimeShiftingLiveService.getPlayInfo/1\nAxeFRth")
        print(x)
        return
        url = 'http://liveapp.cutv.com/crossdomain/timeshiftinglive/getTSLAllChannelList/first/sztv'
        text = self.haha.GetCacheUrl(url).decode()
        x = re.findall('allChannelListCallBack\((.*)\)', text)
        jdata = tornado.escape.json_decode(x[0])
        for x in jdata['tvList']:
            tv = TVStation()
            tv.vid = x['flag']
            tv.name = x['name']
            tv.Show()
            for ch_j in x['channellist']:
                ch = Channel()
                ch.cid = ch_j['id']
                ch.name = ch_j['name']
                tv.channels.append(ch)
                ch.Show()

            self.tvlist.append(tv)

    def GetEPG(self):
        url = 'http://cls.cutv.com/live/ajax/getprogrammelist2/id/AxeFRth/callback/callTslEpg'

class cutv2(TVStation):
    def __init__(self):
        super().__init__()
        self.tvlist = []
        url = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=tv_live'
        text = self.haha.GetCacheUrl(url).decode()
        root = ElementTree.fromstring(text)
        for p in root.findall('tv'):
            tv = TVStation()
            tv.vid = p.findtext('tv_id')
            tv.name = p.findtext('tv_name')
            tv.logo1 = p.findtext('tv_thumb_img')
            tv.logo2 = p.findtext('tv_logo')
            tv.Show()
            self.GetChannel(tv)


    def GetChannel(self, tv):
        url = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=channel_prg_list&tv_id=' + tv.vid
        text = self.haha.GetCacheUrl(url).decode()
        root = ElementTree.fromstring(text)
        for p in root.findall('channel'):
                ch = Channel()
                #<channel_id>22</channel_id>
                #<channel_name>深圳台-深圳卫视</channel_name>
                #<thumb>...</thumb>
                #<mobile_url>...</mobile_url>
                ch.cid = p.findtext('channel_id')
                ch.name = p.findtext('channel_name')
                ch.logo = p.findtext('thumb')
                ch.video_url = p.findtext('mobile_url')
                self.channels.append(ch)
                ch.Show()

    def GetEPG(self):
        url = 'http://cls.cutv.com/live/ajax/getprogrammelist2/id/AxeFRth/callback/callTslEpg'
if __name__ == "__main__":
   #ZJTV()
   HZTV()
   #cutv2()
