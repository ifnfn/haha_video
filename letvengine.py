#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import traceback
import sys
import json
import re
import redis
import base64
import tornado.escape

from bs4 import BeautifulSoup as bs
from engine import VideoBase, AlbumBase, VideoMenuBase, VideoEngine, Template
from utils import autoint, json_get

logging.basicConfig()
log = logging.getLogger("crawler")

#================================= 以下是搜狐视频的搜索引擎 =======================================
SOHU_HOST = 'tv.sohu.com'
MAX_TRY = 3

# 更新节目的播放信息
class TemplateLiveTVInfo(Template):
    def __init__(self, menu):
        cmd = {
            'name'   : 'letv_livetv_list',
            'source' : 'http://www.letvlive.com',
            'regular' : [
                            '(<a href="tv.php.*</a>)',
                            '<h1 class="lm_1">(.*)</h1>'
            ]
        }
        super().__init__(menu.command, cmd)

class LetvVideo(VideoBase):
    def __init__(self, js = None):
        super().__init__(js)

    def GetVideoPlayUrl(self, definition=0):
        vid = self.GetVid(definition)
        if vid:
            return 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
        else:
            return ''

class LetvAlbum(AlbumBase):
    def __init__(self, parent):
        AlbumBase.__init__(self, parent)
        self.VideoClass = LetvVideo

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        if self.albumPageUrl:
            if self.playlistid:
                TemplateLiveTVInfo(self)
            #if self.vid:
            #    TemplateAlbumMvInfo(self, self.albumPageUrl)

class LetvVideoMenu(VideoMenuBase):
    def __init__(self, name, engine):
        VideoMenuBase.__init__(self, name, engine)
        self.homePage    = ''
        self.HomeUrlList = []
        self.albumClass  = LetvAlbum

    def GetFilterJson(self):
        ret = {}
        for k,v in list(self.filter.items()):
            ret[k] = [x for x in v]

        return ret

    def GetSortJson(self):
        ret = []
        for k in self.sort:
            ret.append(k)

        return ret

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            TemplateLiveTVInfo(self, url).Execute()

    def GetRealPlayer(self, text, definition, step):
        if step == '1':
            res = self._ParserRealUrlStep1(text)
        else:
            res = self._ParserRealUrlStep2(text)

        return json.dumps(res, indent=4, ensure_ascii=False)

# 直播电视
class LetvLiveTV(LetvVideoMenu):
    def __init__(self, name, engine):
        self.number = 200
        LetvVideoMenu.__init__(self, name, engine)
        self.homePage = 'http://tv.sohu.com/live/'
        self.cid = 200
        self.filter = {
            '类型': {
                '卫视台':1,
                '地方台':2,
                '央视台':3,
                '境外台':4,
            }
        }

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        if self.homePage != "":
            TemplateLiveTVInfo(self).Execute()

# Letv 搜索引擎
class LetvEngine(VideoEngine):
    def __init__(self, db, command):
        VideoEngine.__init__(self, db, command)

        self.engine_name = 'SohuEngine'
        self.albumClass = LetvAlbum
        self.videoClass = LetvVideo

        # 引擎主菜单
        self.menu = {
            '直播'   : LetvLiveTV
        }

        self.parserList = {
                   'letv_livetv_list' : self._CmdParserLiveTVList,
        }

    # 从分页的页面上解析该页上的节目
    # videolist
    def _CmdParserLiveTVList(self, js):
        ret = []

        text = js['data']

        playlist = js['data'].split("</a>")

        for t in playlist:
            #print(t)
            if re.findall('target="play"', t):
                href=''
                nameid=''
                text=''
                t += '</a>'
                urls = re.findall('(href|id)="([\s\S]*?)"', t)
                for u in urls:
                    if u[0] == 'href':
                        href = 'http://live.gslb.letv.com/gslb?ext=m3u8&sign=live_tv&format=1&stream_id=' + u[1]
                    elif u[0] == 'id':
                        nameid = u[1]

                urls = re.findall('>([\s\S]*?)</a>', t)
                if urls:
                    text = urls[0]
                print(href, nameid, text)

                album  = self.NewAlbum()
                album.cid         = 200
                album.vid         = nameid
                album.albumName   = text

                v = album.VideoClass()
                v.playlistid = album.playlistid
                v.pid = album.vid
                v.cid = album.cid
                v.vid = album.vid
                v.playUrl = 'http://live.tv.sohu.com/live/player_json.jhtml?encoding=utf-8&lid=%d&type=1' % album.playlistid
                album.videos.append(v)
                self._save_update_append(ret, album)

        pass

    def _save_update_append(self, sets, tv, _filter={}, upsert=True):
        if tv:
            self.db.SaveAlbum(tv, _filter, upsert)
            sets.append(tv)
