#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .wolidou import WolidouBaseMenu, WolidouDirectParser
from kola import utils

# 广东省电视台
class GuanDongLivetvWolidouParser(WolidouDirectParser):
    def __init__(self, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = '广东电视台'
        self.area = '中国,广东'

    def NewEpgScript(self, albumName):
        return utils.GetScript('epg', 'get_channel_cutv', [albumName])

class GuanDongLiveTV(WolidouBaseMenu):
    '''
    广东省内所有电视台
    '''
    def __init__(self, name):
        self.Parser = GuanDongLivetvWolidouParser
        super().__init__(name)
        self.AlbumPage = [
            ('广东-珠江频道', 'http://www.wolidou.com/x/?s=qq&f=flv&u=gdtvzj'),
            ('广东-公共频道', 'http://www.wolidou.com/x/?s=qq&f=flv&u=gdtvgg'),
            ('深圳-都市频道', 'http://www.wolidou.com/x/?s=topway&f=rtmp&u=7324394407c4d8125e3771e02cff6135'),
            ('深圳-电视剧',   'http://www.wolidou.com/x/?s=topway&f=rtmp&u=1e471ef1ab6b5ef3309a168acd7e8df2'),
            ('深圳-财经生活', 'http://www.wolidou.com/x/?s=topway&f=rtmp&u=82095635d41a182306589dcc5ea18b89'),
            ('深圳-娱乐频道', 'http://www.wolidou.com/x/?s=topway&f=rtmp&u=fe152fa9fddd7052663892e9a3573795'),
            ('深圳-少儿频道', 'http://www.wolidou.com/x/?s=topway&f=rtmp&u=f5bf2f2e18057e0851a4eaa74139ebe3'),
            ('深圳-公共频道', 'http://www.wolidou.com/x/?s=topway&f=rtmp&u=48554e172655812ad8c0d4c2c09204cd'),
            ('深圳-国际频道', 'rtmp://113.105.76.231/sztv_int/livestream')
        ]
