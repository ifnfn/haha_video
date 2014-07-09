#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape

from kola import utils, LivetvMenu, json_get

from .common import PRIOR_SOHU
from .livetvdb import LivetvParser, LivetvDB


# 搜狐直播电视
class ParserSohuLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '搜狐'
        self.order = PRIOR_SOHU

        self.ExcludeName = ['浙江卫视', '无锡.*', ' 南京.*']

        self.cmd['source'] = 'http://tvimg.tv.itc.cn/live/top.json'

    def CmdParser(self, js):
        db = LivetvDB()

        tvlist = tornado.escape.json_decode(js['data'])
        for v in tvlist['attachment']:
            pid = json_get(v, 'id', '')

            alubmName = json_get(v, 'name', '')
            album  = self.NewAlbum(alubmName)
            if album == None:
                continue

            album.smallPicUrl = json_get(v, 'ico', '')

            videoUrl = 'sohutv://%d' % pid
            v = album.NewVideo(videoUrl)
            
            if v:
                album.videos.append(v)
                db.SaveAlbum(album)

class SohuLiveTV(LivetvMenu):
    '''
    搜狐电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserSohuLivetv]
