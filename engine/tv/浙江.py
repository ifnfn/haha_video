#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import utils, LivetvMenu

from .livetvdb import LivetvParser, LivetvDB


# 温州电视台
class ParserWenZhouLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '温州电视台'
        self.area = '中国,浙江,温州'

        self.cmd['source'] = 'http://tv.dhtv.cn'
        self.cmd['regular'] = ['(<a href=.* data-source=.*</a>)']
        self.Alias = {}
        self.ExcludeName = []

    def CmdParser(self, js):
        db = LivetvDB()

        ch_list = re.findall('data-source="(.*?)" data-id="(.*?)">(.*?)<i>', js['data'])
        for source, _, name in ch_list:
            albumName = '温州-' + name
            album = self.NewAlbum(albumName)

            v = album.NewVideo()
            v.vid = utils.getVidoId(js['source'] + '/' + source)
            v.order = 2
            v.name = self.tvName

            v.SetUrl('wztv://' + source, album)

            album.videos.append(v)
            db.SaveAlbum(album)

class ZheJianLiveTV(LivetvMenu):
    '''
    浙江省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [
            ParserWenZhouLivetv, # 温州
        ]
