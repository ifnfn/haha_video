#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape

from .livetvdb import LivetvParser, LivetvDB
from kola import utils, LivetvMenu

from .common import PRIOR_DEFTV
from .wolidou import WolidouBaseParser, WolidouBaseMenu


# 江苏电视台
class ParserJianSuLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '江苏电视台'
        self.area = '中国,江苏'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '学习频道' : '江苏-学习频道',
            '好享购物' : '江苏-好享购物'
        }
        self.ExcludeName = []

        self.cmd['source'] = 'http://newplayerapi.jstv.com/rest/getplayer_1.html'
        #self.cmd['source'] = 'http://newplayerapi.jstv.com/rest/getplayer_2.html'

    def CmdParser(self, js):
        db = LivetvDB()

        tvlist = tornado.escape.json_decode(js['data'])

        if tvlist['status'] == 'ok':
            for stations in tvlist['paramz']['stations']:
                for ch in stations['channels']:
                    album  = self.NewAlbum(ch['name'])
                    if album == None:
                        continue

                    album.largePicUrl = 'http://newplayer.jstv.com' + ch['logo']

                    v = album.NewVideo()
                    v.order  = self.order
                    v.name   = self.tvName

                    v.vid    = utils.getVidoId('http://streamabr.jstv.com' + ch['name'])

                    videoUrl = 'http://streamabr.jstv.com'

                    if ch['supor']:
                        v.SetVideoUrl('default', {'text' : videoUrl + ch['supor']})
                        v.SetVideoUrl('super',   {'text' : videoUrl + ch['supor']})

                    if ch['high']:
                        v.SetVideoUrl('high', {'text' : videoUrl + ch['high']})

                    if ch['fluent']:
                        v.SetVideoUrl('normal', {'text' : videoUrl + ch['fluent']})

                    v.info = utils.GetScript('jstv', 'get_channel', [ch['id']])

                    album.videos.append(v)
                    db.SaveAlbum(album)

class JianSuLiveTV2(LivetvMenu):
    '''
    江苏省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserJianSuLivetv]

# 江苏省电视台
class ParserHuNanLivetvWolidou(WolidouBaseParser):
    def __init__(self, alubmName=None, url=None):
        super().__init__(alubmName, url)
        self.tvName = '江苏电视台'
        self.area = '中国,江苏'
        self.cmd['cache']   = False

class JianSuLiveTV(WolidouBaseMenu):
    '''
    江苏省内所有电视台
    '''
    def __init__(self, name):
        self.Parser = ParserHuNanLivetvWolidou
        super().__init__(name)
        self.AlbumPage = [
            ('江苏卫视', ['http://www.wolidou.com/tvp/206/play206_0_0.html',
                          'http://www.wolidou.com/tvp/206/play206_0_1.html',
                        ]
            ),
            ('江苏-城市频道', 'http://www.wolidou.com/tvp/377/play377_0_0.html'),
            ('江苏-综艺频道','http://www.wolidou.com/tvp/377/play377_0_1.html'),
            ('江苏-公共频道','http://www.wolidou.com/tvp/377/play377_0_2.html'),
            ('江苏-影视频道','http://www.wolidou.com/tvp/377/play377_0_3.html'),
            ('江苏-休闲频道','http://www.wolidou.com/tvp/377/play377_0_4.html'),
            ('江苏-国际频道','http://www.wolidou.com/tvp/377/play377_0_5.html'),
            ('江苏-教育频道','http://www.wolidou.com/tvp/377/play377_0_6.html'),
            ('江苏-学习频道','http://www.wolidou.com/tvp/377/play377_0_7.html'),
            ('江苏-好享购物','http://www.wolidou.com/tvp/377/play377_0_8.html'),
        ]
