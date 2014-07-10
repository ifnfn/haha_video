#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvDB, LivetvParser


# 辽宁省电视台
class LiaoningLivetvParser(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '辽宁电视台'
        self.area = '中国,辽宁'
        self.order = PRIOR_DEFTV

        self.ExcludeName = ['辽宁卫视']
        self.cmd['source'] = 'http://zd.lntv.cn/lnradiotvnetwork/live_liveInfoList.do?flag=1'
        self.cmd['regular'] = ['<dt><a href="(live_liveDetail.do.*?)">']

    def CmdParser(self, js):
        name_map = {
            '1' : '辽宁卫视',      # 1
            '2' : '辽宁-都市频道',  # 2
            '3' : '辽宁-影视频道',  # 3
            '4' : '辽宁-体育频道',  # 4
            '5' : '辽宁-生活频道',  # 5
            '6' : '辽宁-教育青少',  # 6
            '7' : '辽宁-北方频道',  # 7
            '8' : '辽宁-宜佳购物',  # 8
        }

        db = LivetvDB()
        playlist = js['data'].split("\n")
        for href in playlist:
            for x in re.findall('id=(\w*)', href):
                if x in name_map:
                    albumName = name_map[x]
                    album = self.NewAlbum(albumName)
                    if not album:
                        continue

                    videoUrl = 'lntv://' + x
                    v = album.NewVideo(videoUrl)

                    if v:
                        album.videos.append(v)
                        db.SaveAlbum(album)
                    break

class LiaoNingLiveTV(LivetvMenu): # 无效
    '''
    辽宁省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [LiaoningLivetvParser]
