#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from kola import utils, LivetvMenu
from engine import City
from .livetvdb import LivetvParser, LivetvDB
from .common import PRIOR_QQ

# 腾讯直播电视
class ParserQQLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '腾讯'
        self.order = PRIOR_QQ

        self.cmd['source'] = 'http://v.qq.com/live/tv/34.html'
        self.cmd['regular'] = ['(data-cname=.*data-playid=.*data-key=.*>)']

    def CmdParser(self, js):
        db = LivetvDB()
        city = City()

        playlist = js['data'].split(">\n")

        for ch_text in playlist:
            ch_list = re.findall('(data-cname|data-playid|data-key)="([\s\S]*?)"', ch_text)

            ch = {}
            for k,v in ch_list:
                ch[k] = v

            album  = self.NewAlbum(ch['data-cname'])
            album.area = city.GetCity(album.albumName)

            v = album.NewVideo()
            v.order = self.order
            v.name     = self.tvName

            playUrl = 'http://zb.v.qq.com:1863/?progid=%s&redirect=0&apptype=live&pla=ios' % ch['data-playid']
            v.vid   = utils.getVidoId(playUrl)

            v.SetVideoUrl('default', {
                'script' : 'qqtv',
                'parameters' : [playUrl]
            })

            v.info = {
                'script' : 'qqtv',
                'function' : 'get_channel',
                'parameters' : [],
            }

            album.videos.append(v)
            db.SaveAlbum(album)

class QQLiveTV(LivetvMenu):
    '''
    腾讯电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserQQLivetv]
