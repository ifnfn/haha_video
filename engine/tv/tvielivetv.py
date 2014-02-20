#! /usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.escape

from kola import utils

from .livetvdb import LivetvParser, LivetvDB


class ParserTVIELivetv(LivetvParser):
    def __init__(self, url):
        super().__init__()
        self.base_url = url
        self.cmd['source'] = 'http://' + self.base_url + '/api/getChannels'
        self.area = ''

    def CmdParser(self, js):
        db = LivetvDB()

        jdata = tornado.escape.json_decode(js['data'])

        for x in jdata['result']:
            #if 'group_names' in x and x['group_names'] == '':
            #    continue
            name = ''
            if 'name' in x: name = x['name']
            if 'display_name' in x: name = x['display_name']

            album = self.NewAlbum(name)

            v = album.NewVideo()
            v.order = self.order
            v.name = self.tvName

            playUrl = 'http://' + self.base_url + '/api/getCDNByChannelId/' + x['id']
            if self.base_url in ['api.cztv.com']:
                playUrl += '?domain=' + self.base_url

            v.vid = utils.getVidoId(playUrl)

            v.SetVideoUrl('default', {
                'script' : 'tvie',
                'parameters' : [playUrl]
            })

            v.info = {
                'script'     : 'tvie',
                'function'   : 'get_channel',
                'parameters' : ['http://%s/api/getEPGByChannelTime/%s' % (self.base_url, x['id'])]
            }

            album.videos.append(v)
            db.SaveAlbum(album)

    def GetCategories(self, name):
        return self.tvCate.GetCategories(name)

