#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape

from .livetvdb import LivetvParser, LivetvDB
from kola import utils, LivetvMenu

from .common import PRIOR_CNTV


class ParserCntvLivetv(LivetvParser):
    def __init__(self, station=None, tv_id=None):
        super().__init__()
        self.tvName = '中央电视台'
        self.area = ''
        self.order = PRIOR_CNTV

        self.Alias = {
            'CCTV-Español' : 'CCTV-欧洲',
            'CCTV-العربية'     : 'CCTV-阿拉伯',
            'CCTV-Français' : 'CCTV-法语',
            'CCTV-Русский'  : 'CCTV-俄语',
            'CCTV-4 (亚洲)' : 'CCTV-4 中文国际'
        }
        self.ExcludeName = ('厦门卫视', '香港卫视', '山东教育台', '延边卫视', 'CCTV-4 \(欧洲\)', 'CCTV-4 \(美洲\)')

        self.cmd['source'] = 'http://tv.cntv.cn/live'
        self.cmd['regular'] = ['var chs = (.*);']

    def CmdParser(self, js):
        db = LivetvDB()
        tvlist = tornado.escape.json_decode(js['data'])
        for x, v in tvlist.items():
            if x in [ "数字频道", "城市频道"]:
                continue
            for ch in v:
                if ch[2] == '0' or ch[1] == '':
                    continue

                album  = self.NewAlbum(ch[1])
                if album == None:
                    continue
                album.area = self.city.GetCity(ch[3])

                v = album.NewVideo()
                v.order = self.order
                v.name     = self.tvName

                v.vid      = utils.getVidoId('http://vcbox.cntv.chinacache.net/cache/%s.f4m' % ch[0])
                v.SetVideoUrl('default', {'text' : ch[0]})
                v.SetVideoUrlScript('default', 'cntv', [ch[0], ch[5]])

                v.info = utils.GetScript('cntv', 'get_channel', [v.vid])

                album.videos.append(v)
                db.SaveAlbum(album)

class CntvLiveTV(LivetvMenu):
    '''
    CNTV电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserCntvLivetv]
