#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import traceback
import re
import time, datetime
import tornado.escape
from xml.etree import ElementTree
from engine.kolaclient import KolaClient

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
        self.width = 0
        self.height = 0
        self.channel_url = ''
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
        print(self.name)
        for ch in self.channels:
            ch.Show()

    def GetChannel(self):
        pass

    def GetVideoUrl(self, ch):
        pass

    def GetEPG(self, ch, time):
        pass

class JLNTV(TVStation):
    def __init__(self):
        super().__init__()
        self.base_url = 'http://live.jlntv.cn'
        self.GetChannel()

    def GetChannel(self):
        url = self.base_url + '/index.php?option=default,live&ItemId=86&type=record&channelId=6'
        text = self.haha.GetCacheUrl(url)
        if text:
            text = text.decode()
            ch_list = re.findall('<li id="T_Menu_(\d*)"><a href="(.*)">(.*)</a></li>', text)

            for i, v, n in ch_list:
                ch = Channel()
                ch.cid = i
                ch.channel_url = self.base_url + '/' + v
                ch.name = n
                if self.GetVideoUrl(ch):
                    self.channels.append(ch)
#                print(i, self.base_url + '/' + v, n)

    def GetVideoUrl(self, ch):
        text = self.haha.GetCacheUrl(ch.channel_url)
        if text:
            text = text.decode()
            x = re.findall("var playurl = '(.*)';", text)
            if x:
                ch.video_url = x[0]
#                print(x[0])

    def GetEPG(self, ch, time):
        pass

class TVIEStation(TVStation):
    def __init__(self, name, url):
        super().__init__()
        self.name = name
        self.base_url = url
        self.GetChannel()

    def GetTimeStamp(self):
        text = self.haha.GetUrl('http://' + self.base_url + '/api/getUnixTimestamp')
        if text:
            jdata = tornado.escape.json_decode(text)
            if 'time' in jdata:
                return int(float(jdata['time']))

        return time.time()

    def GetChannel(self):
        url = 'http://' + self.base_url + '/api/getChannels'
        print(url)
        text = self.haha.GetCacheUrl(url)
        if text:
            jdata = tornado.escape.json_decode(text)
            #print(json.dumps(jdata, indent=4, ensure_ascii=False))
            try:
                for x in jdata['result']:
                    ch = Channel()
                    ch.cid = x['id']
                    if 'name' in x:
                        ch.name = x['name']
                    if 'display_name' in x:
                        ch.name = x['display_name']
                    if self.GetVideoUrl(ch):
                        self.channels.append(ch)
            except:
                t, v, tb = sys.exc_info()
                print("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

    def GetVideoUrl(self, ch):
        url = 'http://' + self.base_url + '/api/getCDNByChannelId/' + ch.cid
        text = self.haha.GetCacheUrl(url)
        if text:
            try:
                jdata = tornado.escape.json_decode(text)
                if 'result' in jdata:
                    datarates = jdata['result']['datarates']
                    if datarates != None:
                        k, v = list(datarates.items())[0]
                        ch.timestamp = int(float(jdata['result']['timestamp']) / 1000) * 1000
                        ch.video_url = 'http://%s/channels/%s/%s.flv/live?%d' % (v[0], ch.cid, k, ch.timestamp)
                        return True
                elif 'streams' in jdata:
                    channel_name = jdata['channel_name']
                    customer_name = jdata['customer_name']
                    streams = jdata['streams']
                    k, v = list(streams.items())[0]
                    url = v['cdnlist'][0]
                    ch.video_url = 'http://%s/channels/%s/%s/flv:%s/live?%d' % (url, customer_name, channel_name, k, self.GetTimeStamp())

                    return True
            except:
                print('Get', url, 'error:', text)

        return False

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

class NBTV(TVIEStation):
    def __init__(self):
        self.area = '淅江省,宁波市'
        super().__init__('宁波电视台', 'ming-api.nbtv.cn')

class UCATV(TVIEStation):
    def __init__(self):
        self.area = '新疆'
        super().__init__('新疆电视台', 'epgsrv01.ucatv.com.cn')

class ZJTV(TVIEStation):
    def __init__(self):
        self.area = '淅江省'
        super().__init__('浙江电视台', 'api.cztv.com')

class HZTV(TVStation):
    def __init__(self):
        super().__init__()
        self.name = '杭州电视台'
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
                            self.GetEPG(ch, time.time())
                            break

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

class DHTV(TVStation):
    def __init__(self):
        super().__init__()
        self.name = '温州电视台'
        self.area = '淅江省,温州市'
        self.GetChannel()

    def GetChannel(self):
        url = 'http://v.dhtv.cn/tv/'
        text = self.haha.GetCacheUrl(url)
        if text:
            text = text.decode()
            ch_list = re.findall('(http://v.dhtv.cn/tv/\?channal=(.+))">(.*)</a></li>', text)
            for u, source, name in ch_list:
                ch = Channel()
                ch.source = source
                ch.name = name
                ch.channel_url = u
                if self.GetVideoUrl(ch):
                    self.GetEPG(ch)
                    self.channels.append(ch)

    def GetVideoUrl(self, ch):
        url = 'http://www.dhtv.cn/static/??js/tv.js?acm'
        text = self.haha.GetCacheUrl(url)
        if text:
            text = text.decode()
            x = re.findall("streamer' : '(.*)'\+\_info.source,", text)
            if x:
                ch.video_url = x[0] + ch.source
                return True

        return False

    def GetEPG(self, ch, ctime=time.time()):
        text = self.haha.GetCacheUrl(ch.channel_url)
        if text:
            text = text.decode()
            x = re.findall("var _info = {'id':'(\d*)','source':'(.*)','date':'(.*)'}", text)
            if x:
                ch.cid = x[0][0]
        if ch.cid == '':
            return False

        url = 'http://www.dhtv.cn/api/programs/?ac=get&_channel=' + ch.cid
        text = self.haha.GetCacheUrl(url)
        try:
            jdata = tornado.escape.json_decode(text)
            if jdata:
                ch.epgs.clear()
                for epg in jdata['data']:
                    print(epg)

                return True
        except:
            pass
        return False

class CUTV(TVStation):
    def __init__(self):
        super().__init__()
        self.tvlist = {}

    def GetTV(self):
        if not self.tvlist:
            url = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=tv_live'
            text = self.haha.GetCacheUrl(url).decode()
            root = ElementTree.fromstring(text)
            for p in root.findall('tv'):
                tv = TVStation()
                tv.vid = p.findtext('tv_id')
                tv.name = p.findtext('tv_name')
                tv.logo1 = p.findtext('tv_thumb_img')
                tv.logo2 = p.findtext('tv_logo')
                self.tvlist[tv.name] = tv

    def GetStation(self, name):
        if name not in self.tvlist:
            print(name)
            self.GetTV()
        if name in self.tvlist:
            return self.tvlist[name]
        else:
            return None

class CutvStation(TVStation):
    cutv = CUTV()
    def __init__(self, name):
        super().__init__()
        tv = cutv.GetStation(name)
        if tv:
            self.vid = tv.vid
            self.name = tv.name
            self.logo1 = tv.logo1
            self.logo2 = tv.logo2
            self.GetChannel()

    def GetChannel(self):
        url = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=channel_prg_list&tv_id=' + self.vid
        text = self.haha.GetCacheUrl(url).decode()
        root = ElementTree.fromstring(text)
        for p in root.findall('channel'):
                ch = Channel()
                ch.cid = p.findtext('channel_id')
                ch.name = p.findtext('channel_name')
                ch.logo = p.findtext('thumb')
                ch.video_url = p.findtext('mobile_url')
                self.channels.append(ch)

    def GetEPG(self):
        url = 'http://cls.cutv.com/live/ajax/getprogrammelist2/id/AxeFRth'

cutv = CUTV()

TVStationList = {
#    '新疆电视台' : UCATV,
#    '浙江电视台' : ZJTV,
#    '杭州电视台' : HZTV,
#    '宁波电视台' : NBTV,
#    '吉林电视台' : JLNTV,
#    '温州电视台' : DHTV,
    '绍兴电视台' : CutvStation('绍兴台'),
#    '深圳电视台' : CutvStation('深圳台'),
#    '太原电视台' : CutvStation('太原台'),
#    '荆州电视台' : CutvStation('荆州台'),
#    '湖北电视台' : CutvStation('湖北台'),
#    '襄阳电视台' : CutvStation('襄阳台'),
#    '石家庄电视台' : CutvStation('石家庄台'),
#    '南通电视台' : CutvStation('南通台'),
#    '柳州电视台' : CutvStation('柳州台'),
#    '济南电视台' : CutvStation('济南台'),
#    '武汉电视台' : CutvStation('武汉台'),
#    '苏州电视台' : CutvStation('苏州台'),
#    '西安电视台' : CutvStation('西安台'),
#    '西宁电视台' : CutvStation('西宁台'),
#    '郑州电视台' : CutvStation('郑州台'),
#    '泰州电视台' : CutvStation('泰州台'),
#    '台州电视台' : CutvStation('台州台'),
#    '安阳电视台' : CutvStation('安阳台'),
#    '南宁电视台' : CutvStation('南宁台'),
#    '大连电视台' : CutvStation('大连台'),
#    '兰州电视台' : CutvStation('兰州台'),
#    '珠海电视台' : CutvStation('珠海台'),
}

TVList = {
    '浙江电视台' : {
        'channels' : [{
            'script'     : 'zjtv.lua',
            'function'   : 'get_channel',
            'parameters' : 'api.cztv.com',
            'area'       : '浙江省'},
        ]
    },
    '杭州电视台' : {
        'channels' : [{
            'script'   : 'hztv.lua',
            'function' : 'get_channel',
            'area'     : '浙江省杭州市'}
        ]
    },
    '宁波电视台' : {
        'channels' : [
            {'script'     : 'jztv.lua',
             'parameters' : 'ming-api.nbtv.com',
             'area'       : '浙江省杭州市' },
        ]
    },
}


def main():
    ret=[]
    for name, v in list(TVStationList.items()):
        if type(v) == type:
            ret.append(v())
        else:
            ret.append(v)

    for tv in ret:
        tv.Show()

if __name__ == "__main__":
    main()
