#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu

from .common import PRIOR_DEFTV
from .tvielivetv import ParserTVIELivetv


# 湖北省电视台
class ParserHuBeiLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('59.175.153.182')
        self.tvName = '湖北台'
        self.area = '中国,湖北'
        self.order = PRIOR_DEFTV

        self.Alias = {
            'CCTV13' : 'CCTV-13 新闻',
            "湖北公共" : "湖北公共",
            "湖北经视" : "湖北经视",
            "湖北教育" : "湖北教育",
            "湖北体育" : "湖北体育生活",
            "垄上频道" : "湖北垄上",
            "天天读网" : "湖北天天读网",
            "美嘉购物" : "湖北美嘉购物",
            "城市频道" : "湖北城市",
            "手机频道" : "湖北手机",
            "孕育指南" : "湖北孕育指南",
            "湖北影视" : "湖北影视",
            "职业指南" : "湖北职业指南",
            "长江TV"  : "湖北长江TV",
            "碟市频道" : "湖北碟市",
        }

        self.ExcludeName = ['.*广播', '卫视备份', '演播室.*', '湖北之声', 'CCTV-13-彩电', '网台直播', 'CCTV13', '湖北电视台',
                            '湖北场外直播', '联播湖北', '湖北卫视彩电备份', '手机电视', '网罗湖北', '虚拟直播', '钓鱼频道', '湖北手机']

class HuBeiLiveTV(LivetvMenu):
    '''
    湖北省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserHuBeiLivetv]
