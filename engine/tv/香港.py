#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .wolidou import WolidouBaseParser, WolidouBaseMenu


#香港电视台
class HongKongLivetvParserWolidou(WolidouBaseParser):
    def __init__(self, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = '凤凰卫视'
        self.area = '中国,香港'

class HongKongLiveTV(WolidouBaseMenu):
    '''
    辽宁省电视台
    '''
    def __init__(self, name):
        self.Parser = HongKongLivetvParserWolidou
        super().__init__(name)
        self.AlbumPage = [
            ('凤凰卫视-中文台' , [
                           'http://www.wolidou.com/tvp/201/play201_2_0.html',
                           'http://www.wolidou.com/tvp/201/play201_2_0.html',
                           'http://www.wolidou.com/tvp/201/play201_1_1.html'
                           ]),
            ('凤凰卫视-资讯台', ['http://www.wolidou.com/tvp/202/play202_2_1.html']),
            ('星空卫视', ['http://www.wolidou.com/tvp/222/play222_2_0.html']),
            ('华娱卫视', ['http://www.wolidou.com/tvp/891/play891_0_0.html']),
            ('香港卫视', ['http://www.wolidou.com/tvp/337/play337_0_0.html'])
        ]