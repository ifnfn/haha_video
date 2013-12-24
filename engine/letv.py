#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time, sys, traceback
import tornado.escape

from engine import VideoEngine, KolaParser
from kola import DB, autostr, autoint, Singleton, utils
import kola


#================================= 以下是搜狐视频的搜索引擎 =======================================
global Debug
Debug = True

class LetvVideo(kola.VideoBase):
    def SaveToJson(self):
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)

    def SetVideoScript(self, name, vid, func_name='kola_main'):
        url = {
            'script'     : 'letv',
            'parameters' : [autostr(vid), autostr(self.cid)]
        }
        if func_name and func_name != 'kola_main':
                url['function'] = func_name

        self.SetVideoUrl(name, url)

class LetvPrivate:
    def __init__(self):
        self.name =  '乐视'
        self.playlistid = ''
        self.vid = ''
        self.videoListUrl = {}

    def Json(self):
        json = {'name' : self.name}
        if self.playlistid   : json['playlistid'] = self.playlistid
        if self.vid          : json['vid'] = self.vid
        if self.videoListUrl : json['videoListUrl'] = self.videoListUrl

        return json

    def Load(self, js):
        if 'name' in js         : self.name         = js['name']
        if 'playlistid' in js   : self.playlistid   = js['playlistid']
        if 'vid' in js          : self.vid          = js['vid']
        if 'videoListUrl' in js : self.videoListUrl = js['videoListUrl']

class LetvAlbum(kola.AlbumBase):
    def __init__(self):
        self.engineName = 'LetvEngine'
        super().__init__()
        self.albumPageUrl = ''

        self.letv = LetvPrivate()

        self.videoClass = LetvVideo

    def SaveToJson(self):
        if self.letv:
            self.private[self.engineName] = self.letv.Json()
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if self.engineName in self.private:
            self.letv.Load(self.private[self.engineName])

    def UpdateFullInfoCommand(self):
        pass

class LetvDB(DB, Singleton):
    def __init__(self):
        super().__init__()
        self.albumNameAlias = {}   # 别名
        self.blackAlbumName = {}   # 黑名单


    # 从数据库中找到 album
    def FindAlbumJson(self, playlistid='', albumName=''):
        playlistid = autostr(playlistid)
        if playlistid == '' and albumName == '':
            return None

        f = []
        if albumName :    f.append({'albumName'                     : albumName})
        if playlistid :   f.append({'private.LetvEngine.playlistid' : playlistid})

        #return self.album_table.find_one({'$or' : f})
        return self.album_table.find_one({'engineList' : {'$in' : ['LetvEngine']}, '$or' : f})

    # 从数据库中找到album
    def GetAlbumFormDB(self, playlistid='', albumName='', auto=False):
        album = None
        json = self.FindAlbumJson(playlistid, albumName)
        if json:
            album = LetvAlbum()
            album.LoadFromJson(json)
        elif auto:
            album = LetvAlbum()
            if playlistid   : album.letv.playlistid = playlistid
            if albumName    : album.mName = albumName

        return album

    def SaveAlbum(self, album, upsert=True):
        if album.albumName and album.letv.playlistid:
            self._save_update_append(None, album, key={'private.LetvEngine.playlistid' : album.letv.playlistid}, upsert=upsert)

class ParserPlayCount(KolaParser):
    def __init__(self):
        super().__init__()
        self.cmd['name'] = 'engine_parser'
        self.cmd['source'] = 'http://stat.letv.com/vplay/queryMmsTotalPCount?mid=3574083&pid=92280&platform=101&cid=2&vid=2209753'

# 节目列表
class ParserAlbumList(KolaParser):
    def __init__(self, url=None, cid=0):
        super().__init__()
        if url and cid:
            self.cmd['name']    = 'engine_parser'
            self.cmd['source']  = url
            self.cmd['cid']     = cid

    def CmdParser(self, js):
        def TimeStr(t):
            return time.strftime('%Y-%m-%d', time.gmtime(autoint(t) / 1000))

        if not js['data']: return

        db = LetvDB()

        json = tornado.escape.json_decode(js['data'])
        for a in json['data_list']:
            album = LetvAlbum()
            album_js = DB().FindAlbumJson(albumName=a['name'])
            if album_js:
                    album.LoadFromJson(album_js)

            if a['aid'] == '86913':
                pass

            album.albumName       = db.GetAlbumName(a['name'])
            if not album.albumName:
                continue
            try:
                album.vid = utils.genAlbumId(album.albumName)
                album.cid = js['cid']

                album.subName          = a['subname']
                album.enAlbumName      = ''                                          # 英文名称
                album.area             = a['areaName']                               # 地区
                album.categories       = a['subCategoryName'].split(',')             # 类型
                album.publishYear      = time.gmtime(autoint(a['releaseDate']) / 1000).tm_year

                vids = a['vids']
                if vids:
                    vids = vids.split(',')
                    if not vids[0]:
                        pass
                    album.letv.vid = vids[0]
                    album.albumPageUrl     = 'http://www.letv.com/ptv/vplay/%s.html' % autostr(vids[0])

                album.largePicUrl      = a['poster20']                               # 大图 post20 最大的
                album.smallPicUrl      = a['postS3']                                 # 小图 // postS1 小中大的，postS3 小中最小的
                album.largeHorPicUrl   = a['poster12']                               # 横大图
                album.smallHorPicUrl   = a['poster11']                               # 横小图
                album.largeVerPicUrl   = a['postS1']                                 # 竖大图
                album.smallVerPicUrl   = a['postS3']                                 # 竖小图

                album.playLength       = autoint(a['duration']) * 60                 # 时长
                album.updateTime       = TimeStr(a['mtime'])                         # 更新时间
                album.albumDesc        = a['description']                            # 简介
                album.videoScore       = a['rating']                                 #

                if 'episodes' in a:
                    album.totalSet = autoint(a['episodes'])                          # 总集数
                if 'nowEpisodes' in a:
                    album.updateSet = autoint(a['nowEpisodes'])                      # 当前更新集
                album.dailyPlayNum     = a['dayCount']                               # 每日播放次数
                album.weeklyPlayNum    = a['weekCount']                              # 每周播放次数
                album.monthlyPlayNum   = a['monthCount']                             # 每月播放次数
                album.totalPlayNum     = a['playCount']                              # 总播放次数
                album.dailyIndexScore  = a['rating']                                 # 每日指数

                album.mainActors       = a['starring'].split(',')                    # 主演
                album.directors        = a['directory'].split(',')                   # 导演

                if 'aid' in a:
                    album.letv.playlistid = a['aid']

                album.letv.videoListUrl = {
                    'script'     : 'letv',
                    'function'   : 'get_videolist',
                    'parameters' : [album.letv.playlistid, album.letv.vid]
                }

                db.SaveAlbum(album)
            except:
                t, v, tb = sys.exc_info()
                print("ProcessCommand playurl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))

        if len(json['data_list']) > 0:
            g = re.search('p=(\d+)', js['source'])
            if g:
                current_page = int(g.group(1))
                link = re.compile('p=\d+')
                newurl = re.sub(link, 'p=%d' % (current_page + 1), js['source'])
                ParserAlbumList(newurl, js['cid']).Execute()

class LetvVideoMenu(kola.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.albumClass = LetvAlbum

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            ParserAlbumList(url, self.cid).Execute()

    def UpdateHotList(self):
        pass

# 电影
class LetvMovie(LetvVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 1
        self.HomeUrlList = ['http://list.letv.com/api/chandata.json?c=1&ph=1&s=1&o=20&p=1',
                            'http://list.letv.com/api/chandata.json?c=1&ph=1&s=2&o=20&p=1']

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 电视
class LetvTV(LetvVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 2
        self.HomeUrlList = ['http://list.letv.com/api/chandata.json?c=2&o=20&p=2&s=1']

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass


# Letv 搜索引擎
class LetvEngine(VideoEngine):
    def __init__(self):
        super().__init__()

        self.engine_name = 'LetvEngine'
        self.albumClass = LetvAlbum

        # 引擎主菜单
        self.menu = {
            '电影'   : LetvMovie,
            '电视剧' : LetvTV,
        }

        self.parserList = {
            ParserAlbumList(),
        }
