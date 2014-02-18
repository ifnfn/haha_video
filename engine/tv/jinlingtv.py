#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from .livetvdb import LivetvParser, LivetvDB
from kola import utils, LivetvMenu

# 吉林电视台
class ParserJLntvLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '吉林电视台'

        self.cmd['source']  = 'http://live.jlntv.cn/index.php?option=default,live&ItemId=86&type=record&channelId=6'
        self.cmd['regular'] = ['(<li id="T_Menu_.*</a></li>)']

        self.Alias = {}
        self.ExcludeName = ('交通918', 'FM1054', 'FM89')
        self.area = '中国,吉林'

    def CmdParser(self, js):
        db = LivetvDB()

        ch_list = re.findall('<li id="T_Menu_(\d*)"><a href="(.*)">(.*)</a></li>', js['data'])

        for _, u, n in ch_list:
            album  = self.NewAlbum(n)
            album.categories = self.tvCate.GetCategories(n)

            v = album.NewVideo()
            v.order  = self.order
            v.name   = self.tvName

            playUrl  = 'http://live.jlntv.cn/' + u
            v.vid    = utils.getVidoId(playUrl)
#            v.largePicUrl = x[0][2]

            v.SetVideoUrl('default', {
                'script' : 'jlntv',
                'parameters' : [playUrl]
            })

            v.info = {
                      'script' : 'jlntv',
                      'function' : 'get_channel',
                      'parameters' : []}

            album.videos.append(v)
            db.SaveAlbum(album)

class JilingLiveTV(LivetvMenu):
    '''
    吉林所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserJLntvLivetv]
