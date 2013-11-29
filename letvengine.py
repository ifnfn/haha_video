#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback
import re
import tornado.escape
import hashlib

from engine import VideoBase, AlbumBase, VideoMenuBase, VideoEngine, Template
from utils import log, autostr
import tv

#================================= 以下是视频的搜索引擎 =======================================

# 更新节目的播放信息
class TemplateLiveTVInfo(Template):
    def __init__(self, menu):
        cmd = {
            'name'   : 'letv_livetv_list',
            'source' : 'http://www.leshizhibo.com',
            'regular' : ["<dt>(<a title=.*</a>)</dt>"],
            'cache' : True
        }
        super().__init__(menu.command, cmd)

class LetvVideo(VideoBase):
    def __init__(self, js = None):
        super().__init__(js)

    def GetVideoPlayUrl(self, definition=0):
        pass

class LetvAlbum(AlbumBase):
    def __init__(self, parent):
        super().__init__(parent)
        self.albumPageUrl = ''

        self.VideoClass = LetvVideo

    def SaveToJson(self):
        ret = super().SaveToJson()
        pri = {}
        if self.albumPageUrl    : pri['albumPageUrl'] = self.albumPageUrl

        if pri:
            ret['private'] = pri

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if 'private' in json:
            pri = json['private']
            if 'albumPageUrl' in pri   : self.albumPageUrl = pri['albumPageUrl']
    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        if self.albumPageUrl:
            if self.playlistid:
                TemplateLiveTVInfo(self)

class LetvVideoMenu(VideoMenuBase):
    def __init__(self, name, engine):
        super().__init__(name, engine)
        self.homePage    = ''
        self.HomeUrlList = []
        self.albumClass  = LetvAlbum
        self.sort = {
            '周播放最多' : 7,
            '日播放最多' : 5,
            '总播放最多' : 1,
            '最新发布'   : 3,
            '评分最高'   : 4
        }

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            TemplateLiveTVInfo(self, url).Execute()

    def GetRealPlayer(self, text, definition, step, url=''):
        jdata = tornado.escape.json_decode(text)
        ret = {}
        try:
            ret['directPlayUrl'] = jdata['location']
            ret['name'] = jdata['desc']
            ret['publishTime'] = autostr(jdata['starttime'])
            print(ret)
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine._ParserRealUrlStep2: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return ret

# 直播电视
class LetvLiveTV(LetvVideoMenu):
    def __init__(self, name, engine):
        self.number = 200
        super().__init__(name, engine)
        self.homePage = 'http://www.leshizhibo.com/channel/index.php'
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
        super().__init__(db, command)
        self.tvCate = tv.TVCategory()
        self.engine_name = 'LetvEngine'
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

        playlist = js['data'].split("</a>")

        for t in playlist:
            #print(t)
            x = re.findall('<a title="(.*)" href=".*/channel/(.*)" target="_blank"><img alt=.* src="(.*)"><span class', t)
            if x:
                name = x[0][0]
                vid = x[0][1]
                print(name, x[0][1], x[0][2])

                album  = self.NewAlbum()
                album.cid         = 200
                album.vid         = hashlib.md5(name.encode()).hexdigest()[16:]
                album.playlistid  = ''
                album.pid         = ''
                album.albumName   = name
                album.categories = self.tvCate.GetCategories(name)

                v = self.NewVideo()
                v.playUrl = 'http://live.gslb.letv.com/gslb?stream_id=%s&ext=m3u8&sign=live_tv&format=1' % vid
                v.playlistid = album.playlistid
                v.pid = album.vid
                v.cid = album.cid
                v.vid = hashlib.md5(v.playUrl.encode()).hexdigest()[24:]
                v.largePicUrl = x[0][2]
                v.priority = 1
                v.name = "乐视"
                v.script = {
                    'script' : 'letv',
                    'parameters' : [v.playUrl]
                }

                album.videos.append(v)
                self._save_update_append(ret, album)

    def _save_update_append(self, sets, tv, _filter={}, upsert=True):
        if tv:
            self.db.SaveAlbum(tv, _filter, upsert)
            sets.append(tv)
