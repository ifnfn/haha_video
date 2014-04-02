#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import utils, LivetvMenu

from .common import PRIOR_QQ
from .livetvdb import LivetvParser, LivetvDB


# 腾讯直播电视
class ParserQQLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '腾讯'
        self.order = PRIOR_QQ
        self.Alias = {
            '浙江卫视[高清]' : '浙江卫视',
            '广东卫视[高清]' : '广东卫视',
            '东方卫视[高清]' : '东方卫视',
            '深圳卫视[高清]' : '深圳卫视',
            '广东公共' : '广东-公共'
        }
        self.cmd['source'] = 'http://v.qq.com/live/tv/34.html'
        self.cmd['regular'] = ['(data-cname=.*data-playid=.*data-key=.*>)']

    def CmdParser(self, js):
        db = LivetvDB()

        playlist = js['data'].split(">\n")

        for ch_text in playlist:
            ch_list = re.findall('(data-cname|data-playid|data-key)="([\s\S]*?)"', ch_text)

            ch = {}
            for k,v in ch_list:
                ch[k] = v

            album  = self.NewAlbum(ch['data-cname'])
            if album == None:
                continue

            v = album.NewVideo()
            v.order = self.order
            v.name  = self.tvName

            playUrl = 'http://zb.v.qq.com:1863/?progid=%s&redirect=0&apptype=live&pla=ios' % ch['data-playid']
            v.vid   = utils.getVidoId(playUrl)

            v.SetVideoUrlScript('default', 'qqtv', [playUrl])
            v.info = utils.GetScript('qqtv', 'get_channel', [ch['data-key']])

            album.videos.append(v)
            db.SaveAlbum(album)

class QQLiveTV(LivetvMenu):
    '''
    腾讯电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserQQLivetv]
