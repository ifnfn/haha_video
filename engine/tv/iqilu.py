#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import utils, LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser
import tornado.escape
import re


# 齐鲁电视台
class ParserIQilu(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '齐鲁电视台'
        self.area = '中国,山东'
        self.order = PRIOR_DEFTV

        self.cmd['source'] = 'http://v.iqilu.com/live/sdtv/'

    def CmdParser(self, js):
        t = re.findall('var channels = ([\s\S]*?});', js['data'])
        if t:
            t = re.subn('/\*[\s\S]*?\*/', '', t[0])

        if not t:
            return
        jdata = tornado.escape.json_decode(t[0])

        for live, v  in jdata.items():
            # "id":29,"live":"shenghuo","m3u8":"99/6","catname":"生活频道"
            albumName = v['catname']
            if live != 'sdtv':
                albumName = '山东-' + albumName
            m3u8 = v['m3u8']

            videoUrl = 'iqilu://%s/%s' % (live, m3u8)
            album,_ = self.NewAlbumAndVideo(albumName, videoUrl)
            if album:
                self.db.SaveAlbum(album)

class IQiluLiveTV(LivetvMenu):
    '''
    齐鲁电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserIQilu]

