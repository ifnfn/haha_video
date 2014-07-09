#! /usr/bin/python3
# -*- coding: utf-8 -*-

import posixpath
import re

import tornado.escape

from kola import LivetvMenu, utils

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB


class WolidouDirectParser(LivetvParser):
    def __init__(self, albumName=None, url=None):
        super().__init__()
        self.order = PRIOR_DEFTV

        self.cmd['text'] = 'OK'

    def GetChannel(self, name):
        #channels = ['浙江', '杭州', '宁波', '绍兴', '温州', '义乌']
        #channels = ['凤凰']
        channels = ['.*']
        for p in list(channels):
            if re.findall(p, name):
                return name

    def CmdParser(self, js):
        db = LivetvDB()
        try:
            fn = posixpath.abspath('tv.json')
            js = tornado.escape.json_decode(open(fn, encoding='utf8').read())
            for ch in js:
                urls = ch['urls']
                albumName = ch['name']
                if self.GetChannel(albumName) == None:
                    continue

                album  = self.NewAlbum(albumName)
                if album == None:
                    continue

                if type(urls) == str:
                    urls = urls.split('#')

                order = 0
                for u in urls:
                    v = album.NewVideo(u)
                    if v:
                        urlScript = utils.GetScript('wolidou', 'get_video_url', [u])
                        v.SetVideoUrl('default', urlScript)
                        v.name  = '其他 %d' % (order + 1)
                        album.videos.append(v)
                        order += 1
                db.SaveAlbum(album)

        except Exception as e:
            print(e)

class WolidouTV(LivetvMenu):
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [WolidouDirectParser]
