#! /usr/bin/python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup as bs, Tag

from kola import utils, LivetvMenu

from .common import PRIOR_QQ
from .livetvdb import LivetvParser, LivetvDB


class PaserVideoPage(LivetvParser):
    def __init__(self, url=None, albumName=None):
        super().__init__()
        self.tvName = '腾讯'
        self.order = PRIOR_QQ
        self.Alias = {
        }

        if url and albumName:
            self.cmd['source']    = url[0]
            self.cmd['server']    = url[1]
            self.cmd['link']      = url[2]
            self.cmd['regular']   = ['<input type="hidden" id="zsurl" name="zsurl" value="(.*)"']
            self.cmd['albumName'] = albumName

    def CmdParser(self, js):
        print(js['data'], js['server'], js['link'])
        return
        db = LivetvDB()

        album  = self.NewAlbum(js['albumName'])
        if album == None:
            continue

        v = album.NewVideo()
        v.order = self.order
        v.name  = self.tvName

        playUrl = ''
        v.vid   = utils.getVidoId(playUrl)

        v.SetVideoUrlScript('default', 'qqtv', [playUrl])
        v.info = utils.GetScript('qqtv', 'get_channel', [])

        album.videos.append(v)
        db.SaveAlbum(album)


class PaserAlbumPage(LivetvParser):
    def __init__(self, url=None, albumName=None):
        super().__init__()
        self.tvName = '腾讯'
        self.order = PRIOR_QQ
        self.Alias = {
        }

        if url and albumName:
            self.cmd['source'] = url
            self.cmd['regular'] = ['(<div class="ppls">[\s\S]*?</ul>[\s\S]*?</div>)']
            #self.cmd['regular'] = ['(<a href="/tvp/.*</a>)']
            self.cmd['albumName'] = albumName

    def CmdParser(self, js):
        soup = bs(js['data'])  # , from_encoding = 'GBK')

        albumTag = soup.findAll('div', {'class': 'ppls'})
        for ch in albumTag:
            span = ch.findAll('span', {'class' : 'ppls_s'})
            if span:
                server_type = span[0].text.strip()

                if server_type in ['基本收视服务器：', '超速服务器：', 'M3U8专线服务器：', '极速服务器【节目可回放】：']:
                    for alink in ch.findAll('a', {'target' : '_blank'}):
                        href = 'http://www.wolidou.com' + alink.get('href')
                        name = alink.text
                        albumName = js['albumName']
                        #print(href, albumName, name)
                        PaserVideoPage((href, server_type, name), albumName).Execute()

class ParserAlbumList(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '腾讯'
        self.order = PRIOR_QQ
        self.Alias = {
        }
        self.cmd['source'] = 'http://www.wolidou.com/tvz/cctv/70_1.html'
        self.cmd['regular'] = ['(<div class="left">.*</div>)']

    def CmdParser(self, js):

        soup = bs(js['data'])  # , from_encoding = 'GBK')

        albumTag = soup.findAll('a')
        for ch in albumTag:
            href = 'http://www.wolidou.com' + ch.get('href')
            albumName = ''
            if type(ch.contents[0]) == Tag:
                albumName = ch.contents[0].get('alt')

            PaserAlbumPage(href, albumName).Execute()


class WolidouLiveTV(LivetvMenu):
    '''
    Wolidou 电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserAlbumList, PaserAlbumPage, PaserVideoPage]
