#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .wolidou import WolidouDirectParser, WolidouBaseMenu
from kola import utils

# 北京台
class JsonLivetvWolidouParser(WolidouDirectParser):
    def __init__(self, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = '北京台'
        self.area = '中国,天津'

    def NewEpgScript(self, albumName):
        return utils.GetTvmaoEpgScript(albumName)

class JsonLiveTV(WolidouBaseMenu):
    '''
    北京台
    '''
    def __init__(self, name):
        self.Parser = JsonLivetvWolidouParser
        super().__init__(name)
        self.AlbumPage = [
            ('北京-文艺频道', ['http://www.wolidou.com/x/?s=sohu&f=flv&u=btv2',
                         'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=btvwy']),
            ('北京-科教频道', ['http://www.wolidou.com/x/?s=sohu&f=flv&u=btv3',
                         'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=btvkj']),
            ('北京-影视频道', 'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=btvys'),
            ('北京-财经频道', ['http://www.wolidou.com/x/?s=sohu&f=flv&u=btv5',
                         'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=btvcj'
                         ]),
            ('北京-生活频道', ['http://61.55.175.79:81/youkulive/207/400/0/wolidou.com.flv',
                         'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=btvsh']),
            ('北京-青年频道', ['http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=btvqn',
                         'http://61.55.175.79:81/youkulive/206/400/0/wolidou.com.flv']),
            ('北京-新闻频道', 'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=btvxw'),
        ]
