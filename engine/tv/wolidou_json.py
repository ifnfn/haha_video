#! /usr/bin/python3
# -*- coding: utf-8 -*-

import json
import posixpath

from kola import utils

from .common import PRIOR_DEFTV
from .wolidou import WolidouDirectParser, WolidouBaseMenu


class JsonLivetvWolidouParser(WolidouDirectParser):
    def __init__(self, order=None, area=None, tvName=None, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = tvName
        self.area = area
        self.order = order
        self.epgInfo = None

    def SetEpgScript(self, epg):
        paramList = epg.split('#')
        if paramList:
            func = paramList[0]
            args = paramList[1:]
            self.epgInfo = utils.GetScript('epg', func, args)

    def NewEpgScript(self, albumName):
        if self.epgInfo:
            return self.epgInfo
        else:
            return utils.GetTvmaoEpgScript(albumName)

class JsonLiveTV(WolidouBaseMenu):
    def __init__(self, name):
        self.Parser = JsonLivetvWolidouParser
        super().__init__(name)

    def UpdateAlbumList(self):
        '''
        [
            {
                "area" : "中国,北京",
                "tvName" : "中央台",
                "epg": "get_channel_wasu#CCTV-1",
                "channel": [
                    {
                        "name": "CCTV-1 综合",
                        "urls" : [
                                "http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv1",
                                "rtmp://live.asbctv.com/livepkgr/_definst_/20asUBiNYsYoats8AbvqT0mfBclSk246JHoLj0TIibO37R3zdi14"]
                    },
                    {
                        "name": "CCTV-2 财经",
                        "urls" : "http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv2"
                    }
                ]
            },
            {
                "area" : "中国,北京",
                "tvName" : "北京台",
                "epg": "get_channel_tvmao#BTV2",
                "channels": [
                    {
                        "name": "北京-文艺频道",
                        "urls" :"http://www.wolidou.com/x/?s=sohu&f=flv&u=btv2#http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=btvwy"
                    }
                ]
            }
        ]
        '''
        for p in self.parserClassList:
            p().Execute()

        try:
            fn = posixpath.abspath('tv.json')
            js = json.loads(open(fn, encoding='utf8').read())
            count = 0
            for tv in js:
                tvName = tv['tvName']
                area = tv['area']
                if 'order' in tv:
                    order = tv['order']
                else:
                    order = PRIOR_DEFTV

                for ch in tv['channels']:
                    urls = ch['urls']
                    albumName = ch['name']
                    count += 1
                    print(count, albumName)
                    parser = None

                    if type(urls) == str:
                        urls = urls.split('#')

                    for u in urls:
                        if type(u) == str:
                            parser = self.Parser(order, area, tvName, albumName, u)
                            if 'epg' in ch:
                                parser.SetEpgScript(ch['epg'])
                            parser.CmdParser(parser.cmd)

        except Exception as e:
            print(e)
