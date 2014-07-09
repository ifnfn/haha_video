#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB


class TextLivetvParser(LivetvParser):
    def __init__(self):
        super().__init__()

        self.order = PRIOR_DEFTV
        self.tvs = {
            '池州-新闻综合': 'rtmp://60.174.36.89:1935/live/vod4',
            '池州-经济频道': 'rtmp://60.174.36.89:1935/live/vod3',
        }

        self.cmd['text'] = 'OK'

    def CmdParser(self, js):
        db = LivetvDB()
        for alubmName, videoUrl in self.tvs.items():
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
