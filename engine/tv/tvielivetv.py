#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape

from kola import utils
import re
from urllib.parse import quote

from .common import PRIOR_UCTV
from .livetvdb import LivetvParser, LivetvDB


class ParserTVIELivetv(LivetvParser):
    def __init__(self, url):
        super().__init__()
        self.base_url = url
        self.order = PRIOR_UCTV
        self.area = ''

        self.cmd['source'] = 'http://' + self.base_url + '/api/getChannels'
        self.Referer = ''

    def CmdParser(self, js):
        db = LivetvDB()

        jdata = tornado.escape.json_decode(js['data'])

        for x in jdata['result']:
            if 'group_names' in x and x['group_names'] == 'audio':
                continue
            alubmName = ''
            if 'name' in x: alubmName = x['name']
            if 'display_name' in x: alubmName = x['display_name']

            album = self.NewAlbum(alubmName)
            if album == None:
                continue

            v = album.NewVideo()
            v.order = self.order
            v.name = self.tvName

            url = 'http://' + self.base_url + '/api/getCDNByChannelId/' + x['id']
            if self.base_url in ['api.cztv.com']:
                url += '?domain=' + self.base_url

            v.vid = utils.getVidoId(url)

            url = re.sub('^http://', 'tvie://', url)

            if self.Referer:
                if url.find("?", 0) > 0:
                    url += "&referer=" + quote(self.Referer)
                else:
                    url += "?referer=" + quote(self.Referer)

            v.SetUrl(url)

            album.videos.append(v)
            db.SaveAlbum(album)

    def GetCategories(self, name):
        return self.tvCate.GetCategories(name)

