#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import utils, LivetvMenu

from .common import PRIOR_BTV
from .livetvdb import LivetvParser, LivetvDB


# 陕西卫视
class ParserBTV(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '北京电视台'
        self.order = PRIOR_BTV
        self.area = '中国,北京'
        self.Alias = {
        }

        self.cmd['source'] = 'http://l.smgbb.cn/'
        self.cmd['regular'] = ['(<ul id="channels" class="ul_l_m">[\s\S]*</ul>)']

    def CmdParser(self, js):
        pass

class BtvLivetv(LivetvMenu):
    '''
    北京卫视
    '''
    def __init__(self, name):
        super().__init__(name)

    def UpdateAlbumList(self):
        self.tvList = [
            ('北京卫视', 'BTV1'),
            ('BTV-文艺', 'BTV2'),
            ('BTV-科教', 'BTV3'),
            ('BTV-影视', 'BTV4'),
            ('BTV-财经', 'BTV5'),
            ('BTV-生活', 'BTV7'),
            ('BTV-青年', 'BTV8'),
            ('BTV-新闻', 'BTV9'),
            ('卡酷少儿', 'KAKU'),  # http://his.cdn.brtn.cn/approve/live?channel=
        ]

        db = LivetvDB()
        parser = ParserBTV()
        for name, pid in self.tvList:
            album  = parser.NewAlbum(name)
            if album == None:
                continue

            v = album.NewVideo()
            v.order = PRIOR_BTV
            v.name     = '北京电视台'
            v.vid      = utils.getVidoId('http://his.cdn.brtn.cn/approve/live?channel=%s' % pid)

            v.resolution = utils.GetScript('btv', 'get_resolution', [pid])

            #v.SetVideoUrl('default', {
            #    'script' : 'btv',
            #    'parameters' : [pid]
            #})

            v.info = utils.GetScript('btv', 'get_channel', [pid])

            album.videos.append(v)
            db.SaveAlbum(album)
