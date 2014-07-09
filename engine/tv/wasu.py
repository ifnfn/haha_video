#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import utils, LivetvMenu

from .common import PRIOR_WASU
from .livetvdb import LivetvParser, LivetvDB


# 华数直播电视
class ParserWasuLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '华数'
        self.order = PRIOR_WASU
        self.Alias = {
            '浙江钱江都市' : '浙江钱江都市',
            '浙江少儿' : '浙江-少儿',
            '浙江经视' : '浙江-经视',
            '浙江教育科技（高清）' : '浙江-教育科技',
            '浙江影视娱乐' : '浙江-影视',
            '浙江民生休闲' : '浙江-民生休闲',
            '浙江公共新农村' : '浙江-公共新农村',
            '数码时代' : '数码时代',
            '宁波新闻综合' : '宁波-新闻综合',
            '温州新闻综合' : '温州-新闻综合',
            '湖州新闻综合' : '湖州-新闻综合',
            '金华新闻综合' : '金华-新闻综合',
            '绍兴新闻综合' : '绍兴-新闻综合',
            '舟山新闻综合' : '舟山-新闻综合',
            '嘉兴新闻综合' : '嘉兴-新闻综合',
            '衢州新闻综合' : '衢州-新闻综合',
            '丽水新闻综合' : '丽水-新闻综合',
            '台州新闻综合' : '台州-新闻综合',
            '华数0频道' : '华数0频道',
            '杭州综合' : '杭州-综合',
            '杭州影视' : '杭州-影视',
            '杭州西湖明珠' : '杭州-西湖明珠',
            '杭州体育' : '杭州-体育',
        }
        self.cmd['source'] = 'http://live.wasu.cn/'
        self.cmd['regular'] = ['(<a class="ys" href=".*">.*</a>)']

    def CmdParser(self, js):
        db = LivetvDB()

        playlist = js['data'].split("\n")

        for ch_text in playlist:
            ch_list = re.findall('<a class="ys" href="(.*)">(.*)</a>', ch_text)

            if not ch_list:
                continue

            videoUrl = ch_list[0][0]
            alubmName = ch_list[0][1]

            album  = self.NewAlbum(alubmName)
            if album == None:
                continue

            v = album.NewVideo(videoUrl)
            if v:
                album.videos.append(v)
                db.SaveAlbum(album)

class WasuLiveTV(LivetvMenu):
    '''
    华数电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserWasuLivetv]
