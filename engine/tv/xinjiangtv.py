#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu
from .livetvdb import TVCategory
from .tvielivetv import ParserTVIELivetv
from .common import PRIOR_UCTV

# 新疆电视台
class ParserUCLivetv(ParserTVIELivetv):
    class UCTVCategory(TVCategory):
        def __init__(self):
            super().__init__()
            self.filter = {
                '类型' : {
                    '体育台' : '体育|足球|网球|cctv-5|CCTV5|cctv5|CCTV-5|中央电视台五套',
                    '综合台' : '综合|财|都市|经济|旅游',
                    '少儿台' : '动画|卡通|动漫|少儿',
                    '地方台' : '.*',
                }
            }

    def __init__(self):
        super().__init__('epgsrv01.ucatv.com.cn')
        self.tvCate = self.UCTVCategory()
        self.tvName = '新疆电视台'
        self.priority = PRIOR_UCTV

        self.ExcludeName = ('.*广播', '106点5旅游音乐', '天山云LIVE', 'CCTV-4')
        self.area = '中国,新疆'
        self.Alias = {
            'CCTV-1' : 'CCTV-1 综合',
            'CCTV-2' : 'CCTV-2 财经',
            'CCTV-3' : 'CCTV-3 综艺',
            'CCTV-4' : 'CCTV-3 国际',
            'CCTV-5' : 'CCTV-5 体育',
            'CCTV-6' : 'CCTV-6 电影',
            'CCTV-7' : 'CCTV-7 军事农业',
            'CCTV-8' : 'CCTV-8 电视剧',
            'CCTV-9' : 'CCTV-9 纪录',
            'CCTV-10' : 'CCTV-10 科教',
            'CCTV-11' : 'CCTV-11 戏曲',
            'CCTV-12' : 'CCTV-12 社会与法',
            'CCTV-13' : 'CCTV-13 新闻',
            'CCTV-少儿' : 'CCTV-14 少儿'
        }
        
class XinJianLiveTV(LivetvMenu):
    '''
    新疆所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserUCLivetv]
