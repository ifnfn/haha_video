#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape
from kola import utils, LivetvMenu
from engine.tv import LivetvParser, LivetvDB
from .common import PRIOR_JSTV

# 江苏电视台
class ParserJiansuLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '江苏电视台'
        self.order = PRIOR_JSTV

        self.cmd['source'] = 'http://newplayerapi.jstv.com/rest/getplayer_1.html'
        #self.cmd['source'] = 'http://newplayerapi.jstv.com/rest/getplayer_2.html'
        self.Alias = {}
        self.ExcludeName = ()
        self.area = '中国,江苏'

    def CmdParser(self, js):
        db = LivetvDB()

        tvlist = tornado.escape.json_decode(js['data'])

        if tvlist['status'] == 'ok':
            for stations in tvlist['paramz']['stations']:
                for ch in stations['channels']:
                    album  = self.NewAlbum(ch['name'])
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

                    v.info = {
                        'script'     : 'jstv',
                        'function'   : 'get_channel',
                        'parameters' : [ch['id']],
                    }
                    album.videos.append(v)
                    db.SaveAlbum(album)

class JianSuLiveTV(LivetvMenu):
    '''
    江苏省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserJiansuLivetv]
