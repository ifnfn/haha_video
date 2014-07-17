#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser


class TextLivetvParser(LivetvParser):
    def __init__(self):
        super().__init__()

        self.order = PRIOR_DEFTV
        self.tvs = {
            '池州-新闻综合': 'rtmp://60.174.36.89:1935/live/vod4',
            '池州-经济频道': 'rtmp://60.174.36.89:1935/live/vod3',

            '山西-经济资讯': 'http://218.26.188.207/flvss?bitrate=800000&channel=Shan1XiFinance ',
            '山西-黄河频道': 'http://218.26.188.211/flvss?bitrate=800000&channel=HuangHeNews',
            '山西-影视频道': 'http://218.26.188.211/flvss?bitrate=800000&channel=Shan1XiFilm',
            '山西-科教频道': 'http://218.26.188.207/flvss?bitrate=800000&channel=Shan1XiEdu',
            '山西-公共频道': 'http://218.26.188.211/flvss?bitrate=800000&channel=Shan1XiPublic',
            '山西-少儿频道': 'http://218.26.188.211/flvss?bitrate=800000&channel=Shan1XiChild',
            '大庆-影视频道': 'rtmp://live1.baihuwang.com:1935/live/ys',
            '大庆-新闻综合': 'rtmp://live1.baihuwang.com:1935/live/zh',
            '大庆-直播频道': 'rtmp://live1.baihuwang.com:1935/live/kj',
            '大庆-百湖频道': 'rtmp://live1.baihuwang.com:1935/live/bh',
        }

        self.cmd['text'] = 'OK'

    def CmdParser(self, js):
        for albumName, videoUrl in self.tvs.items():
            album, _ = self.NewAlbumAndVideo(albumName, videoUrl)
            self.db.SaveAlbum(album)

class TextLiveTV(LivetvMenu):
    '''
    文本电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [TextLivetvParser]
