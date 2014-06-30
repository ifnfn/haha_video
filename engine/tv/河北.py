#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu

from .common import PRIOR_DEFTV
from .tvielivetv import ParserTVIELivetv


# 河北省电视台
class ParserHeBeiLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.hebtv.com')
        self.tvName = '河北电视台'
        self.area = '中国,河北'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '河北卫视-标清' : '河北卫视',
            '河北卫视-高清' : '河北卫视HD',
            '河北经视' : '河北经济',
            '河北都市' : '河北都市',
            '河北影视' : '河北影视',
            '河北公共' : '河北公共',
            '河北购物' : '河北购物',
            '农民频道' : '河北农民',
            '少儿科教' : '河北少儿科教',
        }
        self.ExcludeName = []

class HeBeiLiveTV(LivetvMenu):
    '''
    河北省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserHeBeiLivetv]
