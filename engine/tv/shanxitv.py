#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from engine import City
from kola import utils, LivetvMenu

from .common import PRIOR_SXTV
from .livetvdb import LivetvParser, LivetvDB


# 陕西卫视
class ParserShanXiLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = 'PRIOR_SXTV'
        self.order = PRIOR_SXTV
        self.area = '中国,陕西'
        self.Alias = {
        }

        self.cmd['source'] = 'http://l.smgbb.cn/'
        self.cmd['regular'] = ['(<ul id="channels" class="ul_l_m">[\s\S]*</ul>)']

    def CmdParser(self, js):
        db = LivetvDB()
        city = City()

        channel = re.findall('<a href="\?channel=(.*?)" class="channel_name">(.*?)</a>', js['data'])
        for pid, name in channel:
            album  = self.NewAlbum(name)
            album.area = city.GetCity(album.albumName)

            v = album.NewVideo()
            v.order = self.order
            v.name     = self.tvName

            v.SetVideoUrl('default', {
                'script' : 'sxtv',
                'parameters' : [pid]
            })

            v.info = {
                'script' : 'sxtv',
                'function' : 'get_channel',
                'parameters' : [pid],
            }
            print(pid)
            print(v.info)

            album.videos.append(v)
            db.SaveAlbum(album)

class ShanXiLivetv(LivetvMenu):
    '''
    陕西卫视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserShanXiLivetv]
