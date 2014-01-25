#! /usr/bin/python3
# -*- coding: utf-8 -*-

from xml.etree import ElementTree
from engine.tv import LivetvParser, LivetvDB
from kola import utils, LivetvMenu
from engine import City

class ParserCutvLivetv(LivetvParser):
    def __init__(self, station=None, tv_id=None):
        super().__init__()
        self.area = ''

        if station == 'all':
            self.cmd['step'] = 1
            self.cmd['source'] = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=tv_live'
        elif station and id:
            self.tvName = station

            self.cmd['step'] = 2
            self.cmd['station'] = station
            self.cmd['id'] = tv_id
            self.cmd['source'] = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=channel_prg_list&tv_id=' + utils.autostr(tv_id)

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
        city = City()
        self.area = city.GetCity(js['station'])
        root = ElementTree.fromstring(text)
        for p in root.findall('channel'):
            name = p.findtext('channel_name')
            album  = self.NewAlbum(name)
            album.categories = self.tvCate.GetCategories(album.albumName)
            album.area       = self.area

            album.channel_id  = p.findtext('channel_id')
            album.largePicUrl = p.findtext('thumb')

            url = p.findtext('mobile_url')
            v = album.NewVideo()
            v.priority = 2
            v.name     = "CUTV"
            v.SetVideoUrl('default', {'text' : url})

            x = url.split('/')
            if len(x) > 4:
                v.vid  = x[4]
                v.info = {
                    'script' : 'cutv',
                    'function' : 'get_channel',
                    'parameters' : [v.vid],
                }

            album.videos.append(v)
            db.SaveAlbum(album)

class CuLiveTV(LivetvMenu):
    '''
    联合电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserCutvLivetv]
