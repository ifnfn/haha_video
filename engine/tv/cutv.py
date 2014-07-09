#! /usr/bin/python3
# -*- coding: utf-8 -*-

from xml.etree import ElementTree

from kola import utils, LivetvMenu

from .common import PRIOR_CUTV
from .livetvdb import LivetvParser, LivetvDB


class ParserCutvLivetv(LivetvParser):
    def __init__(self, station=None, tv_id=None):
        super().__init__()
        self.order = PRIOR_CUTV
        self.area = ''

        self.ExcludeName = ['网络春晚', '济南', '邯郸', '西安', '南通', '南宁', '安阳', '大连', '鄂尔多斯']

        if station == None:
            self.cmd['step'] = 1
            self.cmd['source'] = 'http://ugc.cutv.com/api/tv_live_api.php?action=tv_live'
        elif station and id:
            self.tvName = station

            self.cmd['step'] = 2
            self.cmd['station'] = station
            self.cmd['id'] = tv_id
            self.cmd['source'] = 'http://ugc.cutv.com/api/tv_live_api.php?action=channel_prg_list&tv_id=' + utils.autostr(tv_id)

    def CmdParser(self, js):
        if js['step'] == 1:
            self.CmdParserAll(js)
        elif js['step'] == 2:
            self.CmdParserTV(js)

    def CmdParserAll(self, js):
        text = js['data']
        root = ElementTree.fromstring(text)
        for p in root.findall('tv'):
            ParserCutvLivetv(p.findtext('tv_name'), p.findtext('tv_id')).Execute()

    def CmdParserTV(self, js):
        db = LivetvDB()
        text = js['data']
        tv_id = js['id']

        self.area = self.city.GetCity(js['station'])
        root = ElementTree.fromstring(text)
        for p in root.findall('channel'):
            albumName = p.findtext('channel_name')
            channel_id = p.findtext('channel_id')

            album  = self.NewAlbum(albumName)
            if album == None:
                continue

            album.channel_id  = channel_id
            album.largePicUrl = p.findtext('thumb')

            v = album.NewVideo()
            v.name     = js['station']

            v.SetVideoUrlScript('default', 'cutv', [tv_id, channel_id])

            url = p.findtext('mobile_url')
            x = url.split('/')
            if len(x) > 4:
                v.vid  = x[4]
                v.info = utils.GetScript('cutv', 'get_channel',[v.vid])

            album.videos.append(v)
            db.SaveAlbum(album)

class CuLiveTV(LivetvMenu):
    '''
    联合电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserCutvLivetv]
