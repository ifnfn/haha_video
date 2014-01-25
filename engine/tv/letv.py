#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from urllib.parse import urljoin
from engine.tv import LivetvParser, LivetvDB
from kola import utils, LivetvMenu

# 乐视直播电视
class ParserLetvLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '乐视'

        #self.cmd['source']  = 'http://www.leshizhibo.com/channel/index.php'
        self.cmd['source']  = 'http://www.leshizhibo.com/'
        self.cmd['regular'] = ['<p class="channelimg">(.*)</p>']

    def CmdParser(self, js):
        db = LivetvDB()

        playlist = js['data'].split("</a>")

        for t in playlist:
            #print(t)
            x = re.findall('<a href=".*/channel/(.*)" target="_blank"><img src="(.*)" alt="(.*)" width', t)
            if x:
                vid = x[0][0]
                name = x[0][2]
                image = urljoin(js['source'], x[0][1])
                #print(name, vid, image)

                if name in ['中国教育一台', '中国教育三台', '中国教育二台', '游戏风云一套', '优漫卡通', '延边卫视', '星空卫视',
                            '五星体育', 'TVB翡翠台', '三沙卫视', '厦门卫视', 'NEOTV综合频道', '嘉佳卡通', '华娱卫视',
                            '湖北体育', '广东体育', 'CCTV女性时尚', 'CCTV电视指南', 'CCTV-5体育频道', '兵团卫视', '澳亚卫视',
                            ]:
                    continue
                album  = self.NewAlbum(name)
                album.largePicUrl = image
                album.categories  = self.tvCate.GetCategories(name)

                v = album.NewVideo()
                playUrl     = 'http://live.gslb.letv.com/gslb?stream_id=%s&ext=m3u8&sign=live_tv&format=1' % vid
                v.vid         = utils.getVidoId(playUrl)
                v.largePicUrl = x[0][2]
                v.priority    = 1
                v.name        = "乐视"

                v.SetVideoUrl('default', {
                    'script' : 'letvlive',
                    'parameters' : [playUrl]
                })

                v.info = {
                          'script' : 'letvlive',
                          'function' : 'get_channel',
                          'parameters' : [vid]}

                album.videos.append(v)
                db.SaveAlbum(album)

class LetvLiveTV(LivetvMenu):
    '''
    乐视电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserLetvLivetv]
