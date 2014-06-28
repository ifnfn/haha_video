#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import utils, LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB


# 陕西卫视
class ParserShanXiLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '陕西电视台'
        self.area = '中国,陕西'
        self.order = PRIOR_DEFTV

        self.Alias = {
        }

        self.cmd['source'] = 'http://l.smgbb.cn/'
        self.cmd['regular'] = ['(<ul id="channels" class="ul_l_m">[\s\S]*</ul>)']

    def CmdParser(self, js):
        db = LivetvDB()

        channel = re.findall('<a href="\?channel=(.*?)" class="channel_name">(.*?)</a>', js['data'])
        for pid, albumName in channel:
            album  = self.NewAlbum(albumName)
            if album == None:
                continue

            v = album.NewVideo()
            v.order = self.order
            v.name     = self.tvName

            v.SetVideoUrlScript('default', 'sxtv', [pid])
            v.info = utils.GetScript('sxtv', 'get_channel',[pid])

            album.videos.append(v)
            db.SaveAlbum(album)

class ShanXiLivetv(LivetvMenu):
    '''
    陕西卫视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserShanXiLivetv]
