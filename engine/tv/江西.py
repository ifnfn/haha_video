#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from bs4 import BeautifulSoup as bs

from kola import LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser


# 江西电视台
class ParserJianXiLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '江西电视台'
        self.area = '中国,江西'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '江西卫视频道在线直播' : '江西卫视',
            '江西都市频道在线直播' : '江西-都市',
            '江西经济生活频道在线直播' : '江西-经济',
            '江西影视频道在线直播' : '江西-影视',
            '江西公共频道在线直播' : '江西-公共',
            '江西少儿频道在线直播' : '江西-少儿',
            '红色经典频道在线直播' : '江西-红色经典',
            '移动电视频道在线直播' : '江西-移动电视',
            '风尚购物频道在线直播' : '江西-风尚购物'
        }
        self.ExcludeName = []

        self.cmd['source'] = 'http://www.jxntv.cn/live/'
        self.cmd['regular'] = ['(<li><a href=".*.shtml">.*</a></li>)']

    def CmdParser(self, js):
        baseUrl = js['source']
        soup = bs(js['data'])  # , from_encoding = 'GBK')

        albumTag = soup.findAll('a')
        for ch in albumTag:
            href = baseUrl + ch.get('href')
            albumName = ch.text
            videoUrl = re.sub('^http://', 'jxtv://', href)
            album, _ = self.NewAlbumAndVideo(albumName, videoUrl)
            self.db.SaveAlbum(album)

class JianXiLiveTV(LivetvMenu):
    '''
    江西省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserJianXiLivetv]
