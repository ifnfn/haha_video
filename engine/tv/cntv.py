#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape

from kola import utils, LivetvMenu

from .common import PRIOR_CNTV
from .livetvdb import LivetvParser, LivetvDB


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
        self.ExcludeName = ('厦门卫视', '香港卫视', '山东教育台', '延边卫视', 'CCTV-4 \(欧洲\)', 'CCTV-4 \(美洲\)', 'CCTV-9 纪录(英)', 'CCTV-NEWS')

        self.cmd['source'] = 'http://tv.cntv.cn/live'
        self.cmd['regular'] = ['var chs = (.*);']

    def CmdParser(self, js):
        db = LivetvDB()
        tvlist = tornado.escape.json_decode(js['data'])
        for x, v in tvlist.items():
            if x in [ "数字频道", "城市频道"]:
                continue
            for ch in v:
                albumName = ch[1]
                if ch[2] == '0' or albumName == '':
                    continue

                album  = self.NewAlbum(albumName)
                if album == None:
                    continue
                album.area = self.city.GetCity(ch[3])

                v = album.NewVideo()
                v.order = self.order
                v.name  = self.tvName

                href = "pa://cctv_p2p_hd" + ch[0]
                v.vid   = utils.getVidoId(href)
                v.SetUrl(href)
                #v.SetVideoUrl('default', {'text' : ch[0]})
                #v.SetVideoUrlScript('default', 'cntv', [ch[0], ch[5]])

                v.info = utils.GetScript('cntv', 'get_channel', [ch[0]])

                album.videos.append(v)
                db.SaveAlbum(album)

class CntvLiveTV(LivetvMenu):
    '''
    CNTV电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserCntvLivetv]
