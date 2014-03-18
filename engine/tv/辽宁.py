#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu, utils

from .common import PRIOR_DEFTV
from .livetvdb import LivetvDB
from bs4 import BeautifulSoup as bs
from .wolidou import WolidouBaseParser, WolidouBaseMenu


# 辽宁省电视台
class LiaoningLivetvParser(WolidouBaseParser):
    def __init__(self):
        super().__init__()
        self.tvName = '辽宁电视台'
        self.area = '中国,辽宁'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '辽宁北方' : '辽宁-北方',
            '辽宁都市' : '辽宁-都市',
            '辽宁教育青少' : '辽宁-教育青少',
            '辽宁生活' : '辽宁-生活',
            '辽宁体育' : '辽宁-体育',
            '辽宁宜佳购物' : '辽宁-宜佳购物',
            '辽宁影视剧' : '辽宁-影视剧',
        }

        self.ExcludeName = ['辽宁卫视']
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

# 辽宁省电视台
class LiaoningLivetvParserWolidou(WolidouBaseParser):
    def __init__(self, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = '辽宁电视台'
        self.area = '中国,辽宁'

class LiaoNingLiveTV(WolidouBaseMenu):
    '''
    辽宁省电视台
    '''
    def __init__(self, name):
        self.Parser = LiaoningLivetvParserWolidou
        super().__init__(name)
        self.AlbumPage = [
            ('辽宁-都市' , 'http://www.wolidou.com/tvp/359/play359_1_0.html'),
            ('辽宁-影视剧',  'http://www.wolidou.com/tvp/359/play359_1_1.html'),
            ('辽宁-生活' , 'http://www.wolidou.com/tvp/359/play359_1_2.html'),
            ('辽宁-少儿' , 'http://www.wolidou.com/tvp/359/play359_1_3.html'),
            ('辽宁-北方' , 'http://www.wolidou.com/tvp/359/play359_1_4.html'),
            ('辽宁-经济' , 'http://www.wolidou.com/tvp/359/play359_1_5.html'),
            ('辽宁-公共' , 'http://www.wolidou.com/tvp/359/play359_1_6.html'),
            ('辽宁-宜佳购物' , 'http://www.wolidou.com/tvp/359/play359_1_7.html'),
        ]

class LiaoNingLiveTV2(LivetvMenu): # 无效
    '''
    辽宁省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [LiaoningLivetvParser]
