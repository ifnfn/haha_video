#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

import tornado.escape

from kola import LivetvMenu

from .common import PRIOR_VST, PRIOR_LETV, PRIOR_IMGO, PRIOR_CNTV
from .livetvdb import LivetvParser


class ParserYYLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = 'YY'
        self.order = PRIOR_VST
        self.Alias = {
            '海南卫视(旅游卫视)' : '旅游卫视'
        }
        self.cmd['cache'] = True
        self.cmd['source'] = 'http://live.yy.com/t'
        self.cmd['regular'] = ['var liveData = (.*?]);']

        self.ExcludeName = ['右上角订阅']

    def CmdParser(self, js):
        jdata = tornado.escape.json_decode(js['data'])

        for ch in jdata:
            albumName = ch['nick']
            hrefs = 'http://hls.yy.com/live/%s_%s.m3u8' % (ch['channel'], ch['liveChannel'])
            if albumName in ['浙江卫视']:
                pass
            album,_ = self.NewAlbumAndVideo(albumName, hrefs)
            if album:
                self.db.SaveAlbum(album)

class YYLiveTV(LivetvMenu):
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserYYLivetv]
