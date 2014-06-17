#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu

from kola import utils
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

    def NewEpgScript(self, albumName):
        return utils.GetScript('epg', 'get_channel_tvmao', [albumName])

    def CmdParser(self, js):
        for alubmName, (url, info) in self.tvs.items():
            epgInfo = self.NewEpgScript(alubmName)
            album  = self.NewAlbum(alubmName, epgInfo)

            v = album.NewVideo()
            v.order = self.order

            v.vid   = utils.getVidoId(url)

            v.SetVideoUrl(alubmName, url)

            if info:
                v.info = info

            album.videos.append(v)
            LivetvDB().SaveAlbum(album)

class TextLiveTV(LivetvMenu):
    '''
    文本电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [TextLivetvParser]
