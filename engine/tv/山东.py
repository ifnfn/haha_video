#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time

import tornado.escape

from kola import LivetvMenu, utils

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB
from .m2oplayer import M2OLivetvParser


# 山东电视台
class ShangDongLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '济南电视台'
        self.area = '中国,山东,济南'
        self.order = PRIOR_DEFTV

        self.cmd['source'] = 'http://v.iqilu.com/live/sdtv/'
        self.cmd['regular'] = ['var channels = ({[\s\S]*?});']

    def CmdParser(self, js):
        db = LivetvDB()

        link = re.compile('/\*[\s\S]*?\*/')
        text = re.sub(link, '', js['data'])
        jdata = tornado.escape.json_decode(text)

        for tv in jdata:
            #'live': 'nongke', 'catname': '农科频道', 'id': 30, 'm3u8': '99/4'
            "http://m3u8.iqilu.com/live/' +livedata['m3u8']+ '.m3u8?st='+s+'&e='+t+'"
            albumName = tv['catname']
            s = time.time()
            t = ''
            url = 'http://m3u8.iqilu.com/live/' + tv['m3u8'] + '.m3u8?st=' + s + '&e=' + t
            album  = self.NewAlbum(albumName)

            v = album.NewVideo()
            v.order = self.order
            v.name  = self.tvName

            v.vid   = utils.getVidoId(url)
            v.SetVideoUrlScript('default', 'm2oplayer', [url])

            v.info = utils.GetScript('m2oplayer', 'get_channel',['http://%s/m2o/player/program_xml.php?channel_id=%d' % (self.baseUrl, js['channel_id'])])

            album.videos.append(v)
            db.SaveAlbum(album)

# 济南电视台
class ParserJiNanLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '济南电视台'
        self.area = '中国,山东,济南'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '新闻频道' : '济南-新闻频道',
            '都市频道' : '济南-都市频道',
            '影视频道' : '济南-影视频道',
            '娱乐频道' : '济南-娱乐频道',
            '生活频道' : '济南-生活频道',
            '商务频道' : '济南-商务频道',
            '少儿频道' : '济南-少儿频道',
            '新闻高清' : '济南-新闻HD'
        }

        self.ExcludeName = ['济南都市', '济南商务', '济南少儿', '济南生活', '济南新闻', '济南影视', '济南娱乐'] # 与 VST 重复
        self.baseUrl = 'www.ijntv.cn'
        self.channelIds = (5, 6, 7, 8, 9, 10, 11, 13)

class ShangDongLiveTV(LivetvMenu):
    '''
    山东省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserJiNanLivetv]
