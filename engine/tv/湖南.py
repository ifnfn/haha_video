#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .common import PRIOR_DEFTV
from kola import LivetvMenu
from .wolidou import ParserVideoPage

# 湖南省电视台
class ParserHuNanLivetv(ParserVideoPage):
    def __init__(self, url=None):
        super().__init__()
        self.tvName = '湖南电视台'
        self.area = '中国,湖南'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '湖南电视台' : '湖南卫视'
        }

        self.ExcludeName = []

        if url:
            self.cmd['source']    = url
            self.cmd['albumName'] = '湖南卫视'

class HuNanLiveTV(LivetvMenu):
    '''
    湖南省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserHuNanLivetv]

    def UpdateAlbumList(self):
        page = [
            #'http://www.wolidou.com/tvp/204/play204_1_0.html',
            'http://www.wolidou.com/tvp/204/play204_2_0.html',
            'http://www.wolidou.com/tvp/204/play204_2_2.html',
            'http://www.wolidou.com/tvp/204/play204_3_0.html',
            #'http://www.wolidou.com/tvp/204/play204_3_3.html',
        ]

        for p in page:
            ParserHuNanLivetv(p).Execute()
