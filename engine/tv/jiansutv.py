#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape

from .livetvdb import LivetvParser, LivetvDB
from kola import utils, LivetvMenu

from .common import PRIOR_JSTV


# 江苏电视台
class ParserJianSuLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '江苏电视台'
        self.area = '中国,江苏'
        self.order = PRIOR_JSTV

        self.Alias = {
            '学习频道' : '江苏-学习频道',
            '好享购物' : '江苏-好享购物'
        }
        self.ExcludeName = []

        self.cmd['source'] = 'http://newplayerapi.jstv.com/rest/getplayer_1.html'
        #self.cmd['source'] = 'http://newplayerapi.jstv.com/rest/getplayer_2.html'

    def CmdParser(self, js):
        db = LivetvDB()

        tvlist = tornado.escape.json_decode(js['data'])

        if tvlist['status'] == 'ok':
            for stations in tvlist['paramz']['stations']:
                for ch in stations['channels']:
                    album  = self.NewAlbum(ch['name'])
                    if album == None:
                        continue

                    album.largePicUrl = 'http://newplayer.jstv.com' + ch['logo']

                    v = album.NewVideo()
                    v.order  = self.order
                    v.name   = self.tvName

                    v.vid    = utils.getVidoId('http://streamabr.jstv.com' + ch['name'])

                    videoUrl = 'http://streamabr.jstv.com'

                    if ch['supor']:
                        v.SetVideoUrl('default', {'text' : videoUrl + ch['supor']})
                        v.SetVideoUrl('super',   {'text' : videoUrl + ch['supor']})

                    if ch['high']:
                        v.SetVideoUrl('high', {'text' : videoUrl + ch['high']})

                    if ch['fluent']:
                        v.SetVideoUrl('normal', {'text' : videoUrl + ch['fluent']})

                    v.info = utils.GetScript('jstv', 'get_channel', [ch['id']])

                    album.videos.append(v)
                    db.SaveAlbum(album)

class JianSuLiveTV(LivetvMenu):
    '''
    江苏省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserJianSuLivetv]
