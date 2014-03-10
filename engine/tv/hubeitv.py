#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .tvielivetv import ParserTVIELivetv
from .common import PRIOR_DEFTV
from kola import LivetvMenu


# 湖北省电视台
class ParserHuBeiLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('59.175.153.182')
        self.tvName = '湖北电视台'
        self.area = '中国,湖北'
        self.order = PRIOR_DEFTV

        self.Alias = {
            'CCTV13' : 'CCTV-13 新闻',
            "湖北公共" : "湖北-公共频道",
            "湖北经视" : "湖北-经视频道",
            "湖北教育" : "湖北-教育频道",
            "湖北体育" : "湖北-体育频道",
            "垄上频道" : "湖北-垄上频道",
            "天天读网" : "湖北-天天读网",
            "美嘉购物" : "湖北-美嘉购物",
            "城市频道" : "湖北-城市频道",
            "手机频道" : "湖北-手机频道",
            "孕育指南" : "湖北-孕育指南",
            "湖北影视" : "湖北-影视频道",
            "职业指南" : "湖北-职业指南",
            "长江TV"  : "湖北-长江TV",
        }

        self.ExcludeName = ['.*广播', '卫视备份', '演播室.*', '湖北之声', 'CCTV-13-彩电', '网台直播']

class HuBeiLiveTV(LivetvMenu):
    '''
    湖北省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserHuBeiLivetv]
