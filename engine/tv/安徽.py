#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu

from .common import PRIOR_DEFTV
from .m2oplayer import M2OLivetvParser


# 安徽电视台
class ParserAnhuiLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '安徽电视台'
        self.area = '中国,安徽'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '安徽公共' : '安徽公共',
            '科教频道' : '安徽科教',
            '综艺频道' : '安徽综艺',
            '影视频道' : '安徽影视',
            '经济生活' : '安徽经济',
            '安徽国际' : '安徽国际',
            '人物频道' : '安徽人物',
        }

        self.ExcludeName = []
        self.baseUrl = 'www.ahtv.cn'
        self.channelIds = (2, 3, 4, 5, 6, 7, 8, 9)

class AnHuiLiveTV(LivetvMenu):
    '''
    安徽省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserAnhuiLivetv]
