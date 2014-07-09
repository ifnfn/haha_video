#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu, utils

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB


class TextLivetvParser(LivetvParser):
    def __init__(self):
        super().__init__()

        self.order = PRIOR_DEFTV
        self.tvs = {
            '沈阳-新闻频道' : ('http://streamer.csytv.com/live/1?fmt=h264_800k_flv', {}),
            '沈阳-经济频道' : ('http://streamer.csytv.com/live/2?fmt=h264_800k_flv', {}),
            '沈阳-公共频道' : ('http://streamer.csytv.com/live/3?fmt=h264_800k_flv', {}),
        }

        self.cmd['text'] = 'OK'

    def CmdParser(self, js):
        db = LivetvDB()
        for alubmName, (videoUrl, _) in self.tvs.items():
            album = self.NewAlbum(alubmName)

            v = album.NewVideo(videoUrl)
            if v:
                album.videos.append(v)
                db.SaveAlbum(album)

class TextLiveTV(LivetvMenu):
    '''
    文本电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [TextLivetvParser]
