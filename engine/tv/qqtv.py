#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import LivetvMenu

from .common import PRIOR_QQ
from .livetvdb import LivetvParser, LivetvDB


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

        playlist = js['data'].split(">\n")

        for ch_text in playlist:
            ch_list = re.findall('(data-cname|data-playid|data-key)="([\s\S]*?)"', ch_text)

            ch = {}
            for k,v in ch_list:
                ch[k] = v

            albumName = ch['data-cname']
            album  = self.NewAlbum(albumName)
            if album == None:
                continue

            videoUrl = 'qqtv://' + ch['data-playid']
            v = album.NewVideo(videoUrl)

            if v:
                album.videos.append(v)
                db.SaveAlbum(album)

class QQLiveTV(LivetvMenu):
    '''
    腾讯电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserQQLivetv]
