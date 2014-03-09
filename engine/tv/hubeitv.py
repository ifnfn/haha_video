#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .tvielivetv import ParserTVIELivetv
from .common import PRIOR_TV
from kola import LivetvMenu


# 湖北省电视台
class ParserHuBeiLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('59.175.153.182')
        self.tvName = '湖北电视台'
        self.area = '中国,湖北'
        self.order = PRIOR_TV

        self.Alias = {
            'CCTV13' : 'CCTV-13 新闻',
            "湖北公共" : "湖北台-公共频道",
            "湖北经视" : "湖北台-经视频道",
            "湖北教育" : "湖北台-教育频道",
        }

        self.ExcludeName = ['.*广播', '卫视备份', '演播室.*', '湖北之声', 'CCTV-13-彩电']

class HuBeiLiveTV(LivetvMenu):
    '''
    湖北省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserHuBeiLivetv]
