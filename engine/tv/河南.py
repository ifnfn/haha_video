#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .wolidou import WolidouDirectParser, WolidouBaseMenu
from .common import PRIOR_DEFTV
from kola import utils

# 河南省电视台
class HeNanLivetvWolidouParser(WolidouDirectParser):
    def __init__(self, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = '河南台'
        self.area = '中国,河南'
        self.order = PRIOR_DEFTV

    def NewEpgScript(self, albumName):
        return utils.GetTvmaoEpgScript(albumName)

class HeNanLiveTV(WolidouBaseMenu):
    '''
    河南省内所有电视台
    '''
    def __init__(self, name):
        self.Parser = HeNanLivetvWolidouParser
        super().__init__(name)
        self.AlbumPage = [
            ('河南-都市频道', 'http://www.wolidou.com/x/?s=henan&f=flv&u=hentv2'),
            ('河南-民生频道', 'http://www.wolidou.com/x/?s=henan&f=flv&u=hentv3'),
            ('河南-政法频道', 'http://www.wolidou.com/x/?s=henan&f=flv&u=hentv4'),
            ('河南-电视剧频道', 'http://www.wolidou.com/x/?s=henan&f=flv&u=hentv5'),
            ('河南-新闻频道', 'http://www.wolidou.com/x/?s=henan&f=flv&u=hentv6'),
            ('河南-公共频道', 'http://www.wolidou.com/x/?s=henan&f=flv&u=hentv8'),
            ('河南-新农村频道', 'http://www.wolidou.com/x/?s=henan&f=flv&u=hentv9'),
            ('河南-国际频道', 'http://www.wolidou.com/x/?s=henan&f=flv&u=hentv10'),
        ]