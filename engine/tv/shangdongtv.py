#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu

from .common import PRIOR_DEFTV
from .m2oplayer import M2OLivetvParser


# 济南电视台
class ParserJiNanLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '济南电视台'
        self.area = '中国,山东,济南'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '新闻频道' : '济南-新闻频道',
            '都市频道' : '济南-都市频道',
            '影视频道' : '济南-影视频道',
            '娱乐频道' : '济南-娱乐频道',
            '生活频道' : '济南-生活频道',
            '商务频道' : '济南-商务频道',
            '少儿频道' : '济南-少儿频道',
            '新闻高清' : '济南-新闻高清'
        }

        self.ExcludeName = []
        self.baseUrl = 'www.ijntv.cn'
        self.channelIds = (5, 6, 7, 8, 9, 10, 11, 13)

class ShangDongLiveTV(LivetvMenu):
    '''
    山东省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserJiNanLivetv]
