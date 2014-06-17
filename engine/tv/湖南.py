#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .wolidou import WolidouBaseMenu, WolidouDirectParser
from kola import utils

# 湖南省电视台
class ParserHuNanLivetvWolidou(WolidouDirectParser):
    def __init__(self, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = '湖南电视台'
        self.area = '中国,湖南'

    def NewEpgScript(self, albumName):
        return utils.GetScript('epg', 'get_channel_tvmao', [albumName])

class HuNanLiveTV(WolidouBaseMenu):
    '''
    湖南省内所有电视台
    '''
    def __init__(self, name):
        self.Parser = ParserHuNanLivetvWolidou
        super().__init__(name)
        self.AlbumPage = [
            ('湖南卫视', [
            'http://www.wolidou.com/x/?s=jstv&f=flv&u=hntvsd',
            'http://www.wolidou.com/x/?s=jstv&f=flv&u=hntv1"',
            ]),
        ]
