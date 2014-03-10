#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .tvielivetv import ParserTVIELivetv
from .common import PRIOR_DEFTV
from kola import LivetvMenu


# 河北省电视台
class ParserHeBeiLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.hebtv.com')
        self.tvName = '河北电视台'
        self.area = '中国,河北'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '河北卫视-标清' : '河北卫视',
            '河北经视' : '河北-经济频道',
            '河北都市' : '河北-都市频道',
            '河北影视' : '河北-影视频道',
            '河北公共' : '河北-公共频道',
            '河北购物' : '河北-购物频道',
            '农民频道' : '河北-农民频道',
            '少儿科教' : '河北-少儿科教',
        }
        self.ExcludeName = []

class HeBeiLiveTV(LivetvMenu):
    '''
    河北省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserHeBeiLivetv]
