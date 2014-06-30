#! /usr/bin/python3
# -*- coding: utf-8 -*-

from xml.etree import ElementTree

from kola import utils

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB


class M2OLivetvParser(LivetvParser):
    def __init__(self):
        super().__init__()

        self.order = PRIOR_DEFTV
        self.baseUrl = ''
        self.channelIds = ()

    def Execute(self):
        for i in self.channelIds:
            self.cmd['source'] = 'http://%s/m2o/player/channel_xml.php?id=%d&url=%s' % (self.baseUrl, i, self.baseUrl)
            self.cmd['channel_id'] = i
            self.command.AddCommand(self.cmd)

        self.cmd = None
        self.command.Execute()

    def CmdParser(self, js):
        url = js['source']
        text = js['data']
        root = ElementTree.fromstring(text)

        albumName = root.attrib['name']
        if albumName == '':
            return

        ok = False
        for p in root:
            if p.tag == 'video':
                for item in p.getchildren():
                    if 'url' in item.attrib:
                        ok = True
                        break

        if ok == False:
            return

        album  = self.NewAlbum(albumName)

        if album == None:
            return

        v = album.NewVideo()
        v.order = self.order
        v.name  = self.tvName
        v.vid   = utils.getVidoId(url)

        v.SetVideoUrlScript('default', 'm2oplayer', [url])

        v.info = utils.GetScript('m2oplayer', 'get_channel',['http://%s/m2o/player/program_xml.php?channel_id=%d' % (self.baseUrl, js['channel_id'])])

        album.videos.append(v)
        LivetvDB().SaveAlbum(album)
