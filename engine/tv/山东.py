#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time

import tornado.escape

from kola import LivetvMenu, utils

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB


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

class ShangDongLiveTV(LivetvMenu):
    '''
    山东省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ShangDongLivetv]
