#! /usr/bin/python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup as bs, Tag

from kola import utils, LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB


class WolidouBaseParser(LivetvParser):
    def __init__(self, albumName=None, url=None):
        super().__init__()
        self.tvName = 'Other'
        self.order = PRIOR_DEFTV
        self.Alias = {
            "CCTV5+"          : "CCTV-5+ 体育",
            "高尔夫·网球"       : "CCTV-高尔夫",
            "CCTV1综合频道"     : "CCTV-1 综合",
            "CCTV2财经频道"     : "CCTV-2 财经",
            "CCTV3综艺频道"     : "CCTV-3 综艺",
            "CCTV4中文国际"     : "CCTV-4 (亚洲)",
            "CCTV6电影频道"     : "CCTV-6 电影",
            "CCTV7军事农业频道" : "CCTV-7 军事农业",
            "CCTV8电视剧频道"   : "CCTV-8 电视剧",
            "CCTV9记录频道"     : "CCTV-9 纪录",
            "CCTV10科学教育频道" : "CCTV-10 科教",
            "CCTV11戏曲频道"     : "CCTV-11 戏曲",
            "CCTV12社会与法频道" : "CCTV-12 社会与法",
            "CCTV13新闻频道"     : "CCTV-13 新闻",
            "CCTV14少儿频道"     : "CCTV-14 少儿",
            "CCTV15音乐频道"     : "CCTV-15 音乐",
            "CCTV News"         : "CCTV News",
            "中国教育电视台"     : "中国教育电视台",
            "国防军事频道"      : "CCTV-国防军事",
            "世界地理频道"      : "CCTV-世界地理",
            "风云音乐频道"      : "CCTV-风云音乐",
            "电视指南频道"      : "CCTV-电视指南",
            "发现之旅频道"      : "CCTV-发现之旅",
            "央视文化精品频道"   : "CCTV-文化精品",
            "中学生频道"        : "CCTV-中学生",
            "证券资讯频道"      : "CCTV-证券资讯",
            "风云剧场频道"      : "CCTV-风云剧场",
            "第一剧场频道"      : "CCTV-第一剧场",
            "女性时尚频道"      : "CCTV-女性时尚",
            "怀旧剧场频道"      : "CCTV-怀旧剧场",
            "风云足球频道"      : "CCTV-风云足球",
            "央视台球频道"      : "CCTV-台球",
        }

        self.cmd['regular']   = ['<input type="hidden" id="zsurl" name="zsurl" value="(.*)"']
        if url and albumName:
            self.cmd['source']    = url
            self.cmd['albumName'] = albumName

    def CmdParser(self, js):
        db = LivetvDB()

        albumName = js['albumName']
        if albumName[-2:] == '直播':
            albumName = albumName[:-2]
        album  = self.NewAlbum(js['albumName'])
        if album == None:
            return

        v = album.NewVideo()
        v.order = self.order
        v.name  = self.tvName

        playUrl = js['data']
        v.vid   = utils.getVidoId(playUrl)

        v.SetVideoUrlScript('default', 'wolidou', [playUrl])
        v.info = utils.GetScript('wolidou', 'get_channel', [])

        album.videos.append(v)
        db.SaveAlbum(album)


class PaserAlbumPage(LivetvParser):
    def __init__(self, url=None, albumName=None):
        super().__init__()

        if url and albumName:
            self.cmd['source'] = url
            self.cmd['regular'] = ['(<div class="ppls">[\s\S]*?</ul>[\s\S]*?</div>)']
            self.cmd['albumName'] = albumName

    def CmdParser(self, js):
        soup = bs(js['data'])  # , from_encoding = 'GBK')

        albumTag = soup.findAll('div', {'class': 'ppls'})
        for ch in albumTag:
            span = ch.findAll('span', {'class' : 'ppls_s'})
            if span:
                server_type = span[0].text.strip()

                for alink in ch.findAll('a', {'target' : '_blank'}):
                    name = alink.text
                    href = 'http://www.wolidou.com' + alink.get('href')
                    albumName = js['albumName']

                    if server_type in ['基本收视服务器：']:
                            if name == '直播地址2':
                                continue

                    elif server_type not in ['超速服务器：', 'M3U8专线服务器：']: # '极速服务器【节目可回放】：'
                        continue

                    WolidouBaseParser(albumName, href).Execute()

class ParserAlbumList(LivetvParser):
    def __init__(self, url=None):
        super().__init__()
        self.ExcludeName = []
        if url:
            self.cmd['source'] = url
            self.cmd['regular'] = ['(<div class="left">.*</div>|<li><a href="/.*</a></li>)']

    def CmdParser(self, js):
        soup = bs(js['data'])  # , from_encoding = 'GBK')

        albumTag = soup.findAll('a')
        for ch in albumTag:
            href = 'http://www.wolidou.com' + ch.get('href')

            if not ch.has_attr('target'):
                if ch.text == '下一页' and href != js['source']:
                    self.__class__(href).Execute()
                continue

            albumName = ''
            if type(ch.contents[0]) == Tag:
                albumName = ch.contents[0].get('alt')

            if albumName in self.ExcludeName:
                continue

            PaserAlbumPage(href, albumName).Execute()

# CCTV
class ParserCctvAlbumList(ParserAlbumList):
    def __init__(self, url='http://www.wolidou.com/tvz/cctv/70_1.html'):
        super().__init__(url)

# 卫视
class ParserWeishiAlbumList(ParserAlbumList):
    def __init__(self, url='http://www.wolidou.com/tvl/weishi/2_1.html'):
        super().__init__(url)

class WolidouBaseMenu(LivetvMenu):
    def __init__(self, name):
        super().__init__(name)
        #self.Parser = LiaoningLivetvParserWolidou
        self.parserClassList = [self.Parser]
        self.AlbumPage = []

    def UpdateAlbumList(self):
        for p in self.parserClassList:
            p().Execute()

        for albumName, url in self.AlbumPage:
            if type(url) == list:
                for u in url:
                    self.Parser(albumName, u).Execute()
            else:
                self.Parser(albumName, url).Execute()

class WolidouLiveTV(LivetvMenu):
    '''
    Wolidou 电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [
            ParserCctvAlbumList,
            #ParserWeishiAlbumList,
            PaserAlbumPage, WolidouBaseParser]
