#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from bs4 import BeautifulSoup as bs, Tag
import tornado.escape

from kola import LivetvMenu

from .common import PRIOR_PPTV
from .livetvdb import LivetvParser


'http://web-play.pptv.com/web-m3u8-300162.m3u8?type=m3u8.web.pad&playback=0'

class ParserPPtvList(LivetvParser):
    def __init__(self, area_id=None):
        super().__init__()
        self.tvName = 'PPTV'
        self.order = PRIOR_PPTV

        if area_id:
            self.cmd['source'] = 'http://live.pptv.com/api/tv_list?area_id=%s&canBack=0' % area_id
            self.cmd['regular'] = ['\((.*)\)']

    def CmdParser(self, js):
        json = tornado.escape.json_decode(js['data'])
        if 'html' in json:
            soup = bs(json['html'])
            channels = soup.findAll('td', {'class' : 'show_channel'})
            for ch in channels:
                if type(ch) == Tag:
                    for t in ch.contents:
                        if t.name == 'a':
                            href = t.get('href')
                            channel_id = re.findall('/(\w*).html', href)
                            if channel_id:
                                channel_id = channel_id[0]

                            if not (t.text and channel_id):
                                continue

                            albumName = t.text
                            videoUrl = 'pptv://' + channel_id

                            album, _ = self.NewAlbumAndVideo(albumName, videoUrl)
                            self.db.SaveAlbum(album)

# PPTV 直播电视
class ParserPPtvLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = 'PPTV'
        self.order = PRIOR_PPTV

        self.cmd['source'] = 'http://live.pptv.com/list/tv_list'
        self.cmd['regular'] = ['(<a.*area_id ="\w*">.*</a>)']

    def CmdParser(self, js):
        soup = bs(js['data'])  # , from_encoding = 'GBK')
        albumTag = soup.findAll('a', { "href" : '#' })
        for a in albumTag:
            ParserPPtvList(a.get('area_id')).Execute()

class PPtvLiveTV(LivetvMenu):
    '''
    PPTV 电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserPPtvLivetv, ParserPPtvList]
