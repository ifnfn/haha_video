#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .wolidou import WolidouBaseParser, WolidouBaseMenu

# 湖南省电视台
class ParserGuanDongLivetvWolidou(WolidouBaseParser):
    def __init__(self, alubmName=None, url=None):
        super().__init__(alubmName, url)
        self.tvName = '广东电视台'
        self.area = '中国,广东'
        #self.cmd['cache'] = False

class GuanDongnLiveTV(WolidouBaseMenu):
    '''
    湖南省内所有电视台
    '''
    def __init__(self, name):
        self.Parser = ParserGuanDongLivetvWolidou
        super().__init__(name)
        self.AlbumPage = [
            ('广东-珠江频道', 'http://www.wolidou.com/tvp/417/play417_0_0.html'),
            ('广东-公共频道', 'http://www.wolidou.com/tvp/417/play417_0_1.html'),
            ('广东-体育频道', 'http://www.wolidou.com/tvp/292/play292_2_0.html'),
        ]
