#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import LivetvMenu

from .livetvdb import LivetvParser


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
        ch_list = re.findall('data-source="(.*?)" data-id="(.*?)">(.*?)<i>', js['data'])
        for source, _, name in ch_list:
            albumName = '温州-' + name
            videoUrl = 'wztv://' + source
            album,_ = self.NewAlbumAndVideo(albumName, videoUrl)
            self.db.SaveAlbum(album)

class ZheJianLiveTV(LivetvMenu):
    '''
    浙江省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [
            ParserWenZhouLivetv, # 温州
        ]
