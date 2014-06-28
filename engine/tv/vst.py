#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import base64

from kola import utils, LivetvMenu

from .common import PRIOR_WASU
from .livetvdb import LivetvParser, LivetvDB


class ParserVstLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = ''
        self.order = 1
        self.Alias = {
        }
        self.cmd['source'] = 'http://ott.52itv.cn/vst_tvlist?app=egreat&name=mygica%20TV%20MX%20box&ver=4.1.2&uuid=00000000-71b9-5e32-0033-c5870033c587&mac=000102030406'
        self.ExcludeName = ['山东']

    def GetChannel(self, name):
        channels = ['CCTV1 ']
        for p in list(channels):
            if re.findall(p, name):
                return name

    def CmdParser(self, js):
        data = js['data']
        data,_ = re.subn('[*]', '/', data)
        data,_ = re.subn('[!]', '+', data)
        data,_ = re.subn('[,]', '=', data)
        data = base64.decodebytes(data.encode()).decode()
        db = LivetvDB()

        playlist = data.split("\n")

        for ch_text in playlist:
            ch_list = ch_text.split(',')

            albumName = ch_list[0]

            if self.GetChannel(albumName) == None:
                continue

            hrefs = ch_list[1]
            iamge = ch_list[2]

            album  = self.NewAlbum(albumName)
            if album == None:
                continue

            album.largePicUrl = iamge
            order = 0
            for href in hrefs.split('#'):
                v = album.NewVideo()
                v.order = order
                v.name  = '源%d' % (order + 1)
                v.vid   = utils.getVidoId(href)
                v.SetVideoUrlScript('default', 'vst', [href])    
                album.videos.append(v)
                order = order + 1

            db.SaveAlbum(album)

class VstLiveTV(LivetvMenu):
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserVstLivetv]
