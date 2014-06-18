#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .wolidou import WolidouDirectParser, WolidouBaseMenu
from .common import PRIOR_DEFTV
from kola import utils

# 天津省电视台
class TianjinLivetvWolidouParser(WolidouDirectParser):
    def __init__(self, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = '天津台'
        self.area = '中国,天津'

    def NewEpgScript(self, albumName):
        return utils.GetTvmaoEpgScript(albumName)

class TianjinLiveTV(WolidouBaseMenu):
    '''
    天津所有电视台
    '''
    def __init__(self, name):
        self.Parser = TianjinLivetvWolidouParser
        super().__init__(name)
        self.AlbumPage = [
            ('天津-新闻频道', 'http://www.wolidou.com/x/?s=gsft&f=flv&u=tjtv111'),
            ('天津-文艺频道', 'http://www.wolidou.com/x/?s=gsft&f=flv&u=tjtv2'),
            ('天津-影视频道', 'http://www.wolidou.com/x/?s=gsft&f=flv&u=tjtv3'),
            ('天津-都市频道', 'http://www.wolidou.com/x/?s=gsft&f=flv&u=tjtv4'),
            ('天津-科教频道', 'http://www.wolidou.com/x/?s=gsft&f=flv&u=tjtv6'),
            ('天津-少儿频道', 'http://www.wolidou.com/x/?s=gsft&f=flv&u=tjtv7'),
            ('天津-公共频道', 'http://www.wolidou.com/x/?s=gsft&f=flv&u=tjtv8'),
        ]