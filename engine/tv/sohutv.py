#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape
from kola import utils, LivetvMenu, json_get
from engine import City
from .livetvdb import LivetvParser, LivetvDB
from .common import PRIOR_SOHU

# 搜狐直播电视
class ParserSohuLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '搜狐'
        self.order = PRIOR_SOHU

        self.cmd['source'] = 'http://tvimg.tv.itc.cn/live/top.json'

    def CmdParser(self, js):
        db = LivetvDB()
        city = City()

        tvlist = tornado.escape.json_decode(js['data'])
        for v in tvlist['attachment']:
            pid = json_get(v, 'id', '')

            name = json_get(v, 'name', '')
            album  = self.NewAlbum(name)
            album.smallPicUrl = json_get(v, 'ico', '')
            album.area = city.GetCity(album.albumName)

            v = album.NewVideo()
            v.order = self.order
            v.name     = self.tvName

            playUrl    = 'http://live.tv.sohu.com/live/player_json.jhtml?encoding=utf-8&lid=%s&type=1' % pid
            v.vid      = utils.getVidoId(playUrl)

            v.SetVideoUrl('default', {
                'script' : 'sohulive',
                'parameters' : [playUrl]
            })

            v.info = {
                'script' : 'sohulive',
                'function' : 'get_channel',
                'parameters' : [pid],
            }

            album.videos.append(v)
            db.SaveAlbum(album)

class SohuLiveTV(LivetvMenu):
    '''
    搜狐电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserSohuLivetv]
