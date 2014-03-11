#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import utils, LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB
from .tvielivetv import ParserTVIELivetv


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
            '外语频道' : '上海-外语频道',
            '新闻综合' : '上海-新闻综合',
            '娱乐频道' : '上海-娱乐频道',
        }

        self.cmd['source'] = 'http://l.smgbb.cn/'
        self.cmd['regular'] = ['(<ul id="channels" class="ul_l_m">[\s\S]*</ul>)']

    def CmdParser(self, js):
        db = LivetvDB()

        channel = re.findall('<a href="\?channel=(.*?)" class="channel_name">(.*?)</a>', js['data'])
        for pid, name in channel:
            album  = self.NewAlbum(name)
            if album == None:
                continue

            v = album.NewVideo()
            v.order = self.order
            v.name     = self.tvName

            playUrl    = 'http://l.smgbb.cn/channelurl.ashx?starttime=0&endtime=0&channelcode=%s' % pid
            v.vid      = utils.getVidoId(playUrl)

            v.SetVideoUrlScript('default', 'smgbbtv', [pid])
            v.info = utils.GetScript('smgbbtv', 'get_channel',[pid])

            album.videos.append(v)
            db.SaveAlbum(album)

# 上海电视台
class ParserKksmgLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.kksmg.com')
        self.tvName = '看看'
        self.area = '中国,上海'
        self.order = PRIOR_DEFTV

        self.Alias = {
            "娱乐频道" : "上海-娱乐频道",
            "艺术人文" : "上海-艺术人文",
            "戏剧频道" : "上海-戏剧频道",
            "ICS"     : "上海-ICS",
            "星尚酷"   : "上海-星尚酷",
            "上海导视" : "上海-导视",
            "新闻综合" : "上海-新闻综合",
            "星尚"     : "上海-星尚",
            "第一财经" : "上海-第一财经",
            "纪实频道" : "上海-纪实频道",
        }
        self.ExcludeName = ['.*电台', '东广新闻', '动感101', '经典947', 'LoveRadio', 
                            '第一财经音频', 'Sport'
        ]


class SmgbbLivetv(LivetvMenu):
    '''
    东方卫视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserSmgbbLivetv, ParserKksmgLivetv]
