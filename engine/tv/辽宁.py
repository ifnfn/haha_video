#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import LivetvMenu, utils

from .common import PRIOR_DEFTV
from .livetvdb import LivetvDB, LivetvParser
from bs4 import BeautifulSoup as bs
from .wolidou import WolidouBaseParser, WolidouBaseMenu
import re

# 辽宁省电视台
class LiaoningLivetvParser(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '辽宁电视台'
        self.area = '中国,辽宁'
        self.order = PRIOR_DEFTV

        self.ExcludeName = ['辽宁卫视']
        self.cmd['source'] = 'http://zd.lntv.cn/lnradiotvnetwork/live_liveDetail.do?flag=1&id=5'
        self.cmd['regular'] = ["playM3U8 = '(.*)'"]

        ['http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000123/index.m3u8', # 1
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000122/index.m3u8', # 2
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000126/index.m3u8', # 3
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000118/index.m3u8', # 4
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000120/index.m3u8', # 5
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000125/index.m3u8', # 6
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000121/index.m3u8', # 7
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000124/index.m3u8', # 8
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000112/index.m3u8', # 9
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000113/index.m3u8', # 10
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000114/index.m3u8', # 12
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000115/index.m3u8', # 11
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000116/index.m3u8', # 13
         'http://61.161.141.139:8112/Fenghuo/01000000000000000000000000000117/index.m3u8', # 14
         ]

    def CmdParser(self, js):
        name_map = {
            '123' : '辽宁卫视',   # 1
            '122' : '辽宁-都市',  # 2
            '126' : '辽宁-影视剧', # 3
            '118' : '辽宁-体育',  # 4
            '120' : '辽宁-生活',   # 5
            '125' : '辽宁-教育青少', # 6
            '121' : '辽宁-北方',    # 7
            '124' : '辽宁-宜佳购物', # 8
        }

        db = LivetvDB()
        playlist = js['data'].split("\n")
        for href in playlist:
            for x in re.findall('/01000000000000000000000000000(\w*)', href):
                if x in name_map:
                    albumName = name_map[x]
                    album = self.NewAlbum(albumName)
                    if not album:
                        continue

                    v = album.NewVideo()
                    v.order = self.order
                    v.name  = self.tvName

                    v.vid   = utils.getVidoId(href)
                    v.SetVideoUrlScript('default', 'lntv', [href])

                    v.info = utils.GetScript('lntv', 'get_channel',[href])

                    album.videos.append(v)
                    db.SaveAlbum(album)
                    break

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
