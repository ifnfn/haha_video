#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from engine.tv import LivetvParser, LivetvDB
from kola import LivetvMenu, GetNameByUrl

# 文本导入
class ParserTextLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.cmd['source'] = 'http://files.cloudtv.bz/media/20130927.txt'

    def CmdParser(self, js):
        db = LivetvDB()
        text = js['data']
        text = text.replace('（华侨直播）', '')
        text = text.replace('【夜猫】', '')
        text = text.replace('[腾讯]', '')
        playlist = text.split('\n')

        tv = {}
        for t in playlist:
            t = t.strip()
            if t[0:1] != '#':
                v = re.findall('(.*)((http://|rtmp://|rtsp://).*)', t)
                if v and len(v[0]) >= 2:
                    key = v[0][0].strip()
                    value = v[0][1].strip()
                    if key not in tv:
                        tv[key] = []
                    x = {}
                    x['name'], x['order'] = GetNameByUrl(value)
                    x['directPlayUrl'] = value

                    if x not in tv[key]:
                        tv[key].append(x)
        for k,v in list(tv.items()):
            if k and v:
                v.sort(key=lambda x:x['order'])
                album  = self.NewAlbum()
                album.vid         = k
                album.playlistid  = k
                album.albumName   = k
                album.categories  = self.tvCate.GetCategories(album.albumName)
                album.sources     = v
                album.totalSet    = len(v)
                db.SaveAlbum(album)

class TextLiveTV(LivetvMenu):
    '''
    文本电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserTextLivetv]
