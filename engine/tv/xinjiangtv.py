#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from xml.etree import ElementTree
import tornado.escape
from engine.tv import TVCategory, LivetvParser, LivetvDB, ParserTVIELivetv
from kola import utils, LivetvMenu
from engine import GetUrl

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

        self.ExcludeName = ('.*广播', '106点5旅游音乐', '天山云LIVE')
        self.area = '中国,新疆'

class XinJianLiveTV(LivetvMenu):
    '''
    新疆所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserUCLivetv]
