#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import utils, LivetvMenu
from .common import PRIOR_DEFTV

from .livetvdb import LivetvParser, LivetvDB


# 吉林电视台
class ParserJLntvLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '吉林电视台'
        self.area   = '中国,吉林'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '吉林台-公共·新闻' : '吉林-公共新闻',
            '吉林台-东北戏曲' : '吉林-东北戏曲',
            '吉林台-都市频道' : '吉林-都市频道',
            '吉林台-吉林卫视' : '吉林-吉林卫视',
            '吉林台-家有购物' : '吉林-家有购物',
            '吉林台-篮球频道' : '吉林-篮球频道',
            '吉林台-生活频道' : '吉林-生活频道',
            '吉林台-乡村频道' : '吉林-乡村频道',
            '吉林台-影视频道' : '吉林-影视频道',
            '吉林台-综艺·文化' : '吉林-综艺文化',
        }
        self.ExcludeName = ['交通918', 'FM1054', 'FM89']

        self.cmd['source']  = 'http://live.jlntv.cn/index.php?option=default,live&ItemId=86&type=record&channelId=6'
        self.cmd['regular'] = ['(<li id="T_Menu_.*</a></li>)']

    def CmdParser(self, js):
        db = LivetvDB()

        ch_list = re.findall('<li id="T_Menu_(\d*)"><a href="(.*)">(.*)</a></li>', js['data'])

        for _, u, n in ch_list:
            n = '吉林台-' + n
            album  = self.NewAlbum(n)
            if album == None:
                continue

            v = album.NewVideo()
            v.order  = self.order
            v.name   = self.tvName

            playUrl  = 'http://live.jlntv.cn/' + u
            v.vid    = utils.getVidoId(playUrl)
#            v.largePicUrl = x[0][2]

            v.SetVideoUrlScript('default', 'jlntv', [playUrl])
            v.info = utils.GetScript('jlntv', 'get_channel',[])

            album.videos.append(v)
            db.SaveAlbum(album)

class JilingLiveTV(LivetvMenu):
    '''
    吉林所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserJLntvLivetv]
