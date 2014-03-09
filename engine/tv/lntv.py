#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu, utils

from .common import PRIOR_TV
from .livetvdb import LivetvParser, LivetvDB
from bs4 import BeautifulSoup as bs


# 辽宁省电视台
class LiaoningLivetvParser(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '辽宁电视台'
        self.area = '中国,辽宁'
        self.order = PRIOR_TV

        self.Alias = {
            '辽宁北方' : '辽宁-北方',
            '辽宁都市' : '辽宁-都市',
            '辽宁教育青少' : '辽宁-教育青少',
            '辽宁生活' : '辽宁-生活',
            '辽宁体育' : '辽宁-体育',
            '辽宁宜佳购物' : '辽宁-宜佳购物',
            '辽宁影视剧' : '辽宁-影视剧',
        }

        self.cmd['source'] = 'http://www.lntv.cn'
        self.cmd['regular'] = ["(<li ><a href='/tv.html\?id=\w*'>.*</a>)"]

    def CmdParser(self, js):
        db = LivetvDB()
        soup = bs(js['data'])  # , from_encoding = 'GBK')
        albumTag = soup.findAll('a')
        for ch in albumTag:
            href = 'http://www.lntv.cn' + ch.get('href')
            albumName = ch.text
            album  = self.NewAlbum(albumName)

            v = album.NewVideo()
            v.order = self.order
            v.name  = self.tvName

            v.vid   = utils.getVidoId(href)
            v.SetVideoUrlScript('default', 'lntv', [href])

            v.info = utils.GetScript('lntv', 'get_channel',[href])

            album.videos.append(v)
            db.SaveAlbum(album)

class LiaoNingLiveTV(LivetvMenu):
    '''
    辽宁省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [LiaoningLivetvParser]
