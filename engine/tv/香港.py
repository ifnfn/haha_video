#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import utils

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB
from .wolidou import WolidouBaseParser, WolidouBaseMenu


class TextLivetvParser(LivetvParser):
    def __init__(self):
        super().__init__()

        self.order = PRIOR_DEFTV
        self.tvs = {
            '凤凰卫视-资讯台': ('http://live.3gv.ifeng.com/zixun.m3u8', {}),
            '凤凰卫视-中文台': ('http://live.3gv.ifeng.com/zhongwen.m3u8', {}),
        }

        self.cmd['text'] = 'OK'

    def CmdParser(self, js):
        for name, (url, info) in self.tvs.items():
            album = self.NewAlbum(name)

            v = album.NewVideo()
            v.order = self.order

            v.vid = utils.getVidoId(url)

            v.SetVideoUrl(name, url)

            if info:
                v.info = info

            album.videos.append(v)
            LivetvDB().SaveAlbum(album)


# 香港电视台
class HongKongLivetvParserWolidou(WolidouBaseParser):
    def __init__(self, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = '凤凰卫视'
        self.area = '中国,香港'

class HongKongLiveTV(WolidouBaseMenu):
    '''
    辽电视台
    '''
    def __init__(self, name):
        self.Parser = HongKongLivetvParserWolidou
        super().__init__(name)
        self.AlbumPage = [
            ('凤凰卫视-中文台' , [
                           'http://www.wolidou.com/tvp/201/play201_2_0.html',
                           'http://www.wolidou.com/tvp/201/play201_1_1.html',
                           ]),
            ('凤凰卫视-资讯台', ['http://www.wolidou.com/tvp/202/play202_2_1.html']),
            # ('凤凰卫视-香港台', ['http://www.wolidou.com/tvp/201/play201_0_1.html']),
            ('星空卫视', ['http://www.wolidou.com/tvp/222/play222_2_0.html']),
            ('华娱卫视', ['http://www.wolidou.com/tvp/891/play891_0_0.html']),
            ('香港卫视', ['http://www.wolidou.com/tvp/337/play337_0_0.html']),
        ]

        self.parserClassList.append(TextLivetvParser)
