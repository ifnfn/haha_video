#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .tvielivetv import ParserTVIELivetv
from .common import PRIOR_TV
from kola import LivetvMenu


# 黑龙江省电视台
class ParserHLJLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.hljtv.com')
        self.tvName = '黑龙江电视台'
        self.area = '中国,黑龙江'
        self.order = PRIOR_TV

        self.Alias = {
            '卫视' : '黑龙江卫视',
            '第七' : '黑龙江台-第七频道',
            '公共' : '黑龙江台-公共频道',
            '考试' : '黑龙江台-考试频道',
            '导视' : '黑龙江台-导视频道',
        }
        self.ExcludeName = ()

class HeiLongJiangLiveTV(LivetvMenu):
    '''
    黑龙江省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserHLJLivetv]
