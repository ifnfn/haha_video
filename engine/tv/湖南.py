#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .wolidou import WolidouBaseParser, WolidouBaseMenu

# 湖南省电视台
class ParserHuNanLivetvWolidou(WolidouBaseParser):
    def __init__(self, alubmName=None, url=None):
        super().__init__(alubmName, url)
        self.tvName = '湖南电视台'
        self.area = '中国,湖南'
        self.cmd['cache']   = False

class HuNanLiveTV(WolidouBaseMenu):
    '''
    湖南省内所有电视台
    '''
    def __init__(self, name):
        self.Parser = ParserHuNanLivetvWolidou
        super().__init__(name)
        self.AlbumPage = [
            ('湖南卫视', [
            #'http://www.wolidou.com/tvp/204/play204_1_0.html',
            'http://www.wolidou.com/tvp/204/play204_2_0.html',
            'http://www.wolidou.com/tvp/204/play204_2_2.html',
            'http://www.wolidou.com/tvp/204/play204_3_0.html',
            #'http://www.wolidou.com/tvp/204/play204_3_3.html',
            ]),
        ]
