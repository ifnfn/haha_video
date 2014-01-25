#! /usr/bin/python3
# -*- coding: utf-8 -*-

from engine.tv import LivetvParser, LivetvDB
from kola import utils, LivetvMenu


# 安徽电视台
class ParserAnhuiLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '安徽电视台'
        self.cmd['source'] = 'http://www.ahtv.cn/m2o/player/channel_xml.php?first=1&id=7'
        self.cmd['step']   = 1
        self.area = '中国,安徽'

    def CmdParser(self, js):
        ChannelMap = {
            '安徽卫视' : 2,
            '安徽公共' : 3,
            '安徽-科教频道' : 4,
            '安徽-综艺频道' : 5,
            '安徽-影视频道' : 6,
            '安徽-经济生活' : 7,
            '安徽国际'     : 8,
            '安徽-人物频道' : 9
        }

        db = LivetvDB()
        for k,v in ChannelMap.items():
            #url = 'http://www.ahtv.cn/m2o/player/channel_xml.php?first=1&id=%d' % v
            album  = self.NewAlbum(k)
            album.categories = self.tvCate.GetCategories(album.albumName)
            album.area       = self.area
            album.livetv.videoListUrl = {
                'script': 'ahtv',
                'function' : 'get_videolist',
                'parameters' : [album.cid, album.vid, v]
            }
            db.SaveAlbum(album)

class AnHuiLiveTV(LivetvMenu):
    '''
    安徽省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserAnhuiLivetv]
