#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .tvielivetv import ParserTVIELivetv
from .common import PRIOR_TV
from kola import LivetvMenu


# 河北省电视台
class ParserHeBeiLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.hebtv.com')
        self.tvName = '河北电视台'
        self.area = '中国,河北'
        self.order = PRIOR_TV

        self.Alias = {
            '河北卫视-标清' : '河北卫视',
            '河北经视' : '河北台-经济频道',
            '河北都市' : '河北台-都市频道',
            '河北影视' : '河北台-影视频道',
            '河北公共' : '河北台-公共频道',
            '河北购物' : '河北台-购物频道',
            '农民频道' : '河北台-农民频道',
            '少儿科教' : '河北台-少儿科教',
        }
        self.ExcludeName = []

class HeBeiLiveTV(LivetvMenu):
    '''
    河北省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserHeBeiLivetv]
