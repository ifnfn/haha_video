#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape

from kola import utils, LivetvMenu, json_get

from .common import PRIOR_SOHU
from .livetvdb import LivetvParser, LivetvDB


# 搜狐直播电视
class ParserSohuLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '搜狐'
        self.order = PRIOR_SOHU
        self.Alias = {
            '无锡综合' : '无锡-综合',
            '南京教科' : '南京-教科',
            '南京生活' : '南京-生活',
            '南京娱乐' : '南京-娱乐',
            '南京综合' : '南京-综合'
        }
        self.ExcludeName = ['浙江卫视']

        self.cmd['source'] = 'http://tvimg.tv.itc.cn/live/top.json'

    def CmdParser(self, js):
        db = LivetvDB()

        tvlist = tornado.escape.json_decode(js['data'])
        for v in tvlist['attachment']:
            pid = json_get(v, 'id', '')

            alubmName = json_get(v, 'name', '')
            album  = self.NewAlbum(alubmName)
            if album == None:
                continue

            album.smallPicUrl = json_get(v, 'ico', '')

            v = album.NewVideo()
            v.order = self.order
            v.name     = self.tvName

            playUrl    = 'http://live.tv.sohu.com/live/player_json.jhtml?encoding=utf-8&lid=%s&type=1' % pid
            v.vid      = utils.getVidoId(playUrl)

            v.SetUrl('sohutv://%d' % pid)

            #v.SetVideoUrlScript('default', 'sohulive', [playUrl])
            v.info = utils.GetScript('sohulive', 'get_channel', [pid])

            album.videos.append(v)
            db.SaveAlbum(album)

class SohuLiveTV(LivetvMenu):
    '''
    搜狐电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserSohuLivetv]
