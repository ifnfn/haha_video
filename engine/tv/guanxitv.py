#! /usr/bin/python3
# -*- coding: utf-8 -*-

from xml.etree import ElementTree

from engine import GetUrl
from kola import utils, LivetvMenu

from .livetvdb import LivetvParser, LivetvDB


# 南宁电视台
class ParserNNLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '南宁电视台'
        self.order = 2
        self.cmd['source'] = 'http://user.nntv.cn/nnplatform/index.php?mod=api&ac=player&m=getLiveUrlXml&inajax=2&cid=104'
        self.area = '中国,广西,南宁'

    def CmdParser(self, js):
        db = LivetvDB()
        count = 0
        for i in ('101', '105', '104', '103', '106', '117', '109'): #  新闻综合 都市生活 影视娱乐 公共频道 广电购物 老友LIVE CCTV-1
            url = 'http://user.nntv.cn/nnplatform/index.php?mod=api&ac=player&m=getLiveUrlXml&inajax=2&cid=' + i
            text = GetUrl(url).decode()
            root = ElementTree.fromstring(text)

            album = None
            for p in root:
                if p.tag == 'title':
                    album  = self.NewAlbum(p.text)

            if album == None:
                return

            v = album.NewVideo()
            v.order = self.order
            v.name  = self.tvName

            v.vid  = utils.getVidoId(url)
            for p in root:
                if p.tag == 'url':
                    print(p.text)

                    if count == 0:
                        v.SetVideoUrl('default', {'text' : p.text})
                    else:
                        v.SetVideoUrl('url_%d' % count, {'text' : p.text})

                    count += 1

            if count == 0:
                return

            v.info = {
                'script' : 'nntv',
                'function' : 'get_channel',
                'parameters' : [i],
            }

            album.videos.append(v)
            db.SaveAlbum(album)

class GuangXiLiveTV(LivetvMenu):
    '''
    广西所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserNNLivetv]
