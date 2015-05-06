#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import LivetvMenu

from .common import PRIOR_QQ
from .livetvdb import LivetvParser


# 腾讯直播电视
class ParserQQLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '腾讯'
        self.order = PRIOR_QQ

        self.cmd['source'] = 'http://v.qq.com/live/tv/34.html'
        self.cmd['regular'] = ['(data-cname=.*data-playid=.*data-key=.*>)']

    def CmdParser(self, js):
        playlist = js['data'].split(">\n")

        for ch_text in playlist:
            ch_list = re.findall('(data-cname|data-playid|data-key)="([\s\S]*?)"', ch_text)

            ch = {}
            for k,v in ch_list:
                ch[k] = v

            if ch:
                albumName = ch['data-cname']
                videoUrl = 'qqtv://' + ch['data-playid']

                album, _ = self.NewAlbumAndVideo(albumName, videoUrl)
                self.db.SaveAlbum(album)

class QQLiveTV(LivetvMenu):
    '''
    腾讯电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserQQLivetv]
