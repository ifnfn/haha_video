#! /usr/bin/python3
# -*- coding: utf-8 -*-

from xml.etree import ElementTree

from kola import utils, LivetvMenu, GetUrl

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser


# 南宁电视台
class ParserNNLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '南宁电视台'
        self.area = '中国,广西,南宁'
        self.order = PRIOR_DEFTV

        self.cmd['source'] = 'http://user.nntv.cn/nnplatform/index.php?mod=api&ac=player&m=getLiveUrlXml&inajax=2&cid=104'

    def CmdParser(self, js):
        count = 0
        for i in ('101', '105', '104', '103', '106', '117', '109'): #  新闻综合 都市生活 影视娱乐 公共频道 广电购物 老友LIVE CCTV-1
            url = 'http://user.nntv.cn/nnplatform/index.php?mod=api&ac=player&m=getLiveUrlXml&inajax=2&cid=' + i
            text = GetUrl(url).decode()
            root = ElementTree.fromstring(text)

            album = None
            for p in root:
                if p.tag == 'title':
                    alubmName = p.text
                    album  = self.NewAlbum(alubmName)

            if album == None:
                return

            v = album.NewVideo()

            v.vid  = utils.getVidoId(url)
            for p in root:
                if p.tag == 'url':
                    if count == 0:
                        v.SetVideoUrl('default', {'text' : p.text})
                    else:
                        v.SetVideoUrl('url_%d' % count, {'text' : p.text})

                    count += 1

            if count == 0:
                return

            v.info = utils.GetScript('nntv', 'get_channel', [i])

            album.videos.append(v)
            self.db.SaveAlbum(album)

class GuangXiLiveTV(LivetvMenu):
    '''
    广西所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserNNLivetv]
