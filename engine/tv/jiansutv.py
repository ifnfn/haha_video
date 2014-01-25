#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from xml.etree import ElementTree
import tornado.escape
from engine.tv import LivetvParser, LivetvDB, ParserTVIELivetv
from kola import utils, LivetvMenu
from engine import GetUrl


# 江苏电视台
class ParserJiansuLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '江苏电视台'

        #self.cmd['source'] = 'http://newplayerapi.jstv.com/rest/getplayer_1.html'
        self.cmd['source'] = 'http://newplayerapi.jstv.com/rest/getplayer_2.html'
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
                    album.categories = self.tvCate.GetCategories(album.albumName)
                    album.largePicUrl = 'http://newplayer.jstv.com' + ch['logo']

                    v = album.NewVideo()
                    v.vid      = utils.getVidoId('http://streamabr.jstv.com' + ch['name'])
                    v.priority = 2
                    v.name     = "JSTV"

                    videoUrl = 'http://streamabr.jstv.com'

                    v.SetVideoUrl('default', {
                        'text' : videoUrl + ch['auto']
                    })

                    v.SetVideoUrl('super', {
                        'text' : videoUrl + ch['supor']
                    })

                    v.SetVideoUrl('high', {
                        'text' : videoUrl + ch['high']
                    })

                    v.SetVideoUrl('normal', {
                        'text' : videoUrl + ch['fluent']
                    })

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
