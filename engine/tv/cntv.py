#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape

from engine import City
from .livetvdb import LivetvParser, LivetvDB
from kola import utils, LivetvMenu

from .common import PRIOR_CNTV


class ParserCntvLivetv(LivetvParser):
    def __init__(self, station=None, tv_id=None):
        super().__init__()
        self.tvName = '中央电视台'
        self.order = PRIOR_CNTV
        self.area = ''
        self.cmd['source'] = 'http://tv.cntv.cn/live'
        self.cmd['regular'] = ['var chs = (.*);']

        #self.Alias = {
        #}
        self.ExcludeName = ('厦门卫视', '香港卫视', '山东教育台', '延边卫视')

    def CmdParser(self, js):
        db = LivetvDB()
        city = City()
        tvlist = tornado.escape.json_decode(js['data'])
        for x, v in tvlist.items():
            print(x)
            if x in [ "数字频道", "城市频道"]:
                continue
            for ch in v:
                if ch[2] == '0' or ch[1] == '':
                    continue

                album  = self.NewAlbum(ch[1])
                album.area = city.GetCity(ch[3])

                v = album.NewVideo()
                v.order = self.order
                v.name     = self.tvName

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
