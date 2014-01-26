#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from xml.etree import ElementTree
import tornado.escape
from engine.tv import LivetvParser, LivetvDB
from kola import utils, LivetvMenu
from engine import GetUrl, City

class ParserCntvLivetv(LivetvParser):
    def __init__(self, station=None, tv_id=None):
        super().__init__()
        self.area = ''
        self.cmd['source'] = 'http://tv.cntv.cn/live'
        self.cmd['regular'] = ['var chs = (.*);']

    def CmdParser(self, js):
        db = LivetvDB()
        city = City()
        tvlist = tornado.escape.json_decode(js['data'])
        for x, v in tvlist.items():
            print(x)
            if x in [ "数字频道", "城市频道"]:
                continue
            for ch in v:
                if ch[2] == '0' or ch[1] in ['厦门卫视', '香港卫视', '山东教育台', '延边卫视']:
                    continue
                album  = self.NewAlbum(ch[1])
                album.categories = self.tvCate.GetCategories(album.albumName)
                album.area = city.GetCity(ch[3])

                v = album.NewVideo()
                v.priority = 2
                v.name     = "CNTV"
                v.vid      = utils.getVidoId('http://vcbox.cntv.chinacache.net/cache/%s.f4m' % ch[0])
                v.SetVideoUrl('default', {'text' : ch[0]})
                v.SetVideoUrl('default', {
                    'script' : 'cntv',
                    'parameters' : [ch[0], ch[5]]
                })

                v.info = {
                    'script' : 'cntv',
                    'function' : 'get_channel',
                    'parameters' : [v.vid],
                }

                album.videos.append(v)
                db.SaveAlbum(album)

class CntvLiveTV(LivetvMenu):
    '''
    CNTV电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserCntvLivetv]
