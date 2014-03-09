#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import utils

from .livetvdb import LivetvParser, LivetvDB
from xml.etree import ElementTree

class M2OLivetvParser(LivetvParser):
    def __init__(self):
        super().__init__()

        self.baseUrl = ''
        self.channelIds = ()

    def Execute(self):
        for i in self.channelIds:
            self.cmd['source'] = 'http://%s/m2o/player/channel_xml.php?id=%d' % (self.baseUrl, i)
            self.cmd['channel_id'] = i
            self.command.AddCommand(self.cmd)

        self.cmd = None
        self.command.Execute()

    def CmdParser(self, js):
        url = js['source']
        text = js['data']
        root = ElementTree.fromstring(text)

        name = root.attrib['name']
        if name == '':
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

        album  = self.NewAlbum(name)

        v = album.NewVideo()
        v.order = self.order
        v.name  = self.tvName

        v.vid   = utils.getVidoId(url)
        v.SetVideoUrlScript('default', 'hztv', [url])

        v.info = utils.GetScript('hztv', 'get_channel',['http://%s/m2o/player/program_xml.php?channel_id=%d' % (self.baseUrl, js['channel_id'])])

        album.videos.append(v)
        LivetvDB().SaveAlbum(album)
