#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape

from kola import LivetvMenu

from .common import PRIOR_CNTV
from .livetvdb import LivetvParser


class ParserCntvLivetv(LivetvParser):
    def __init__(self, station=None, tv_id=None):
        super().__init__()
        self.tvName = '中央电视台'
        self.area = ''
        self.order = PRIOR_CNTV

        self.ExcludeName = ('厦门卫视', '香港卫视', '山东教育台', '延边卫视', 'CCTV-4 \(欧洲\)', 'CCTV-4 \(美洲\)', 'CCTV-9 纪录(英)', 'CCTV-NEWS')

        self.cmd['source'] = 'http://tv.cntv.cn/live'
        self.cmd['regular'] = ['var chs = (.*);']

    def CmdParser(self, js):
        tvlist = tornado.escape.json_decode(js['data'])
        for x, v in tvlist.items():
            if x in [ "数字频道", "城市频道"]:
                continue
            for ch in v:
                if ch[2] == '0' or ch[1] == '':
                    continue

                albumName = ch[1]
                videoUrl = "pa://cctv_p2p_hd" + ch[0]

                album, v = self.NewAlbumAndVideo(albumName, videoUrl)
                if album:
                    album.area = self.city.GetCity(ch[3])

                self.db.SaveAlbum(album)

class CntvLiveTV(LivetvMenu):
    '''
    CNTV电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserCntvLivetv]
