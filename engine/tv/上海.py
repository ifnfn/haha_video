#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser


# 东方卫视
class ParserSmgbbLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '东方卫视'
        self.area = '中国,上海'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '生活时尚' : '上海-生活时尚',
            '第一财经' : '上海-第一财经',
            '纪实频道' : '上海-纪实频道',
            '艺术人文' : '上海-艺术人文',
            '外语频道' : '上海-外语ICS',
            '新闻综合' : '上海-新闻',
            '娱乐频道' : '上海-娱乐',
        }

        self.cmd['source'] = 'http://l.smgbb.cn/'
        self.cmd['regular'] = ['(<ul id="channels" class="ul_l_m">[\s\S]*</ul>)']

    def CmdParser(self, js):
        channel = re.findall('<a href="\?channel=(.*?)" class="channel_name">(.*?)</a>', js['data'])
        for pid, albumName in channel:
            videoUrl = 'smgbbtv://' + pid
            album,_ = self.NewAlbumAndVideo(albumName, videoUrl)
            self.db.SaveAlbum(album)

class SmgbbLivetv(LivetvMenu):
    '''
    东方卫视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserSmgbbLivetv]
