#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .wolidou import WolidouDirectParser, WolidouBaseMenu
from .common import PRIOR_DEFTV
from kola import utils

# 福建省电视台
class FuJianLivetvWolidouParser(WolidouDirectParser):
    def __init__(self, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = '福建台'
        self.area = '中国,福建'
        self.order = PRIOR_DEFTV

    def NewEpgScript(self, albumName):
        return utils.GetTvmaoEpgScript(albumName)

class FuJianLiveTV(WolidouBaseMenu):
    '''
    福建省电视台
    '''
    def __init__(self, name):
        self.Parser = FuJianLivetvWolidouParser
        super().__init__(name)
        self.AlbumPage = [
            ('福建-综合频道', 'rtmp://stream1.fjtv.net:1935/live/zhpd_sd'),
            ('福建-公共频道', 'rtmp://stream1.fjtv.net:1935/live/ggpd_sd'),
            ('福建-新闻频道', 'rtmp://stream1.fjtv.net:1935/live/xwpd_sd'),
            ('福建-电视剧频道', 'rtmp://stream1.fjtv.net:1935/live/dsjpd_sd'),
            ('福建-都市频道', 'rtmp://stream1.fjtv.net:1935/live/dspd_sd'),
            ('福建-经济频道', 'rtmp://stream1.fjtv.net:1935/live/jjpd_sd'),
            ('福建-少儿频道', 'rtmp://stream1.fjtv.net:1935/live/child_sd'),
        ]