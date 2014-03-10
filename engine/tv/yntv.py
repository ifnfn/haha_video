#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .tvielivetv import ParserTVIELivetv
from .common import PRIOR_DEFTV
from kola import LivetvMenu


# 云南电视台
class ParserYunNanLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('mediamobile.yntv.cn')
        self.tvName = '云南电视台'
        self.area = '中国,云南'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '卫视频道YNTV_1' : '云南卫视',
            '都市频道YNTV_2' : '云南-都市频道',
            '娱乐频道YNTV_3' : '云南-娱乐频道',
            '公共频道YNTV_6' : '云南-公共频道',
        }
        self.ExcludeName = ['云南卫视CDN']

class YunNanLiveTV(LivetvMenu):
    '''
    云南省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserYunNanLivetv]
