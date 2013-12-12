#! /usr/bin/python3
# -*- coding: utf-8 -*-

import traceback
import sys
import json
import re
import tornado.escape

from bs4 import BeautifulSoup as bs
from engine import VideoEngine, KolaParser
from kola import autostr, autoint, log, Singleton
from kola import VideoBase, AlbumBase, VideoMenuBase, DB
from kola import utils

#================================= 以下是搜狐视频的搜索引擎 =======================================

global Debug
Debug = True

class SohuVideo(VideoBase):
    def GetVideoPlayUrl(self, definition=0):
        if self.vid:
            return 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % self.vid
        else:
            return ''

    def SaveToJson(self):
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)

    def SetVideoScript(self, name, vid, func_name='kola_main'):
        url = {
            'script'       : 'sohu',
            'parameters' : ['http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid, autostr(self.cid)]
        }
        if func_name and func_name != 'kola_main':
                url['function'] = func_name

        self.SetVideoUrl(name, url)

class SohuAlbum(AlbumBase):
    def __init__(self):
        super().__init__()
        self.albumPageUrl = ''
        self.engineList = []
        self.engineList.append('SohuEngine')
        self.sohu = {
            'vid' : '',
            'playlistid' : ''
        }

        self.videoClass = SohuVideo

    def SaveToJson(self):
        if self.sohu:
            self.private['sohu'] = self.sohu
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if 'sohu' in self.private:
            self.sohu = self.private['sohu']

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        if self.sohu['playlistid']:
            ParserAlbumFullInfo(self).AddCommand()
        if self.sohu['vid']:
            ParserAlbumMvInfo(self, self.albumName).AddCommand()

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        if self.sohu['playlistid']:
            ParserAlbumScore(self).Execute()

    # 更新节目播放信息
    def UpdateAlbumPlayInfoCommand(self):
        if self.sohu['vid'] != '':
            ParserAlbumPlayInfo(self).AddCommand()

    def GetVideoPlayUrl(self):
        vid = self.sohu['vid']
        if vid:
            return 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
        else:
            return ''

class SohuDB(DB, Singleton):
    def __init__(self):
        super().__init__()

    # 从数据库中找到 album
    def FindAlbumJson(self, playlistid='', albumName='', vid=''):
        playlistid = autostr(playlistid)
        vid = autostr(vid)
        if playlistid == '' and albumName == '' and vid == '':
            return None

        f = []
        if albumName :    f.append({'albumName'               : albumName})
        if playlistid :   f.append({'private.sohu.playlistid' : playlistid})
        if vid :          f.append({'private.sohu.vid'        : vid})

        return self.album_table.find_one({"$or" : f})

    # 从数据库中找到album
    def GetAlbumFormDB(self, playlistid='', albumName='', vid='', auto=False):
        album = None
        json = self.FindAlbumJson(playlistid, albumName, vid)
        if json:
            album = SohuAlbum()
            album.LoadFromJson(json)
        elif auto:
            album = SohuAlbum()
            if playlistid   : album.sohu['playlistid'] = playlistid
            if vid          : album.sohu['vid']        = vid
            if albumName    : album.mName = albumName

        return album

# 搜狐节目列表
class ParserAlbumList(KolaParser):
    def __init__(self, url=None, cid=0):
        super().__init__()
        if url:
            self.cmd['name']    = 'engine_parser'
            self.cmd['regular'] = ['(<li class="clear">|<p class="tit tit-p.*|<em class="pay"></em>|\t</li>)']
            self.cmd['source']  = url
            self.cmd['cid']     = cid

    def CmdParser(self, js):
        db = SohuDB()
        ret = []

        if not js['data']: return ret

        needNextPage = False
        soup = bs(js['data'])#, from_encoding = 'GBK')
        playlist = soup.findAll('li')
        for a in playlist:
            text = a.prettify()
            x = re.findall('pay', text)
            if x:
                continue

            album = SohuAlbum()

            urls = re.findall('(href|title|_s_v|_s_a)="([\s\S]*?)"', text)
            for u in urls:
                if u[0] == 'href':
                    album.albumPageUrl = self.command.GetUrl(u[1])
                elif u[0] == 'title':
                    album.albumName = u[1]
                elif u[0] == '_s_v':
                    album.sohu['vid'] = autostr(u[1])
                elif u[0] == '_s_a':
                    album.sohu['playlistid'] = autostr(u[1])

            if album.albumName:
                album.vid = utils.genAlbumId(album.albumName)
            else:
                continue

            album.cid = js['cid']
            #if (not needNextPage) and (not db.FindAlbumJson(vid=album.sohu['vid'])):
            #    needNextPage = True

            if album.sohu['vid'] and album.albumName and album.sohu['playlistid']:
                db._save_update_append(ret, album, key={'vid' : album.vid})

        needNextPage = True
        if needNextPage:
            g = re.search('p10(\d+)', js['source'])
            if g:
                current_page = int(g.group(1))
                link = re.compile('p10\d+')
                newurl = re.sub(link, 'p10%d' % (current_page + 1), js['source'])
                ParserAlbumList(newurl, js['cid']).Execute()

        return ret

# 更新节目的完整信息
class ParserAlbumFullInfo(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['name']    = 'engine_parser'
            self.cmd['source'] = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=%s&vid=%s' % (album.sohu['playlistid'], album.sohu['vid'])

    # 解析节目的完全信息
    # http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5112241
    # sohu_album_fullinfo
    def CmdParser(self, js):
        db = SohuDB()

        ret = []

        json = tornado.escape.json_decode(js['data'])
        playlistid = autostr(json['playlistid'])
        vid = autostr(json['vid'])
        pid = autostr(json['pid'])

        album = db.GetAlbumFormDB(playlistid=playlistid, vid=vid)
        if album == None:
            return ret

        if 'cid' in json            : album.cid            = autoint(json['cid'])
        if 'playlistid' in json     : album.sohu['playlistid'] = playlistid
        if 'pid' in json            : album.sohu['pid']        = pid
        if 'vid' in json            : album.sohu['vid']        = vid

        if 'isHigh' in json         : album.isHigh         = json['isHigh']
        if 'area' in json           : album.area           = json['area']
        if 'categories' in json     : album.categories     = json['categories']
        if 'publishYear' in json    : album.publishYear    = json['publishYear']
        if 'updateTime' in json     : album.updateTime     = json['updateTime']

        # 图片
        if 'largeHorPicUrl' in json : album.largeHorPicUrl = json['largeHorPicUrl']
        if 'smallHorPicUrl' in json : album.smallHorPicUrl = json['smallHorPicUrl']
        if 'largeVerPicUrl' in json : album.largeVerPicUrl = json['largeVerPicUrl']
        if 'smallVerPicUrl' in json : album.smallVerPicUrl = json['smallVerPicUrl']
        if 'largePicUrl' in json    : album.largePicUrl    = json['largePicUrl']
        if 'smallPicUrl' in json    : album.smallPicUrl    = json['smallPicUrl']

        if 'albumDesc' in json      : album.albumDesc      = json['albumDesc']
        if 'totalSet' in json       : album.totalSet       = json['totalSet']
        if 'updateSet' in json      : album.updateSet      = json['updateSet']

        if 'mainActors' in json     : album.mainActors     = json['mainActors']
        if 'directors' in json      : album.directors      = json['directors']

        if 'videos' in json:
            for video in json['videos']:
                if 'vid' in video and 'vid' in album.sohu:
                    if autostr(video['vid']) == album.sohu['vid'] and album.sohu['vid']:
                        if 'playLength' in video  : album.playLength =  video['playLength']
                        if 'publishTime' in video : album.publishTime = video['publishTime']

                v = album.NewVideo()
                v.LoadFromJson(video)
                v.SetVideoScript('default', v.vid)

                # 兼容旧版本
                v.script = {
                    'script' : 'sohu',
                    'parameters' : [v.GetVideoPlayUrl(), autostr(album.cid)]
				}

                album.videos.append(v)
        if vid:
            db._save_update_append(ret, album, key={'vid' : album.vid}, upsert=False)

        return ret

# 总播放次数，(如果没有指数的话）
class ParserAlbumTotalPlayNum(KolaParser):
    def __init__(self, album=None):
        super().__init__()

        if album:
            self.cmd['name']   = 'engine_parser'
            self.cmd['source'] = 'http://count.vrs.sohu.com/count/query.action?videoId=%s,' % album.sohu['vid']

    # album_total_playnum
    def CmdParser(self, js):
        db = SohuDB()
        ret = []

        data = tornado.escape.to_basestring(js['data'])
        text = re.findall('var count=(\S+?);', data)
        if text:
            data = tornado.escape.json_decode(text[0])
            for v in data['videos']:
                vid = autostr(v['videoid'])
                album = db.GetAlbumFormDB(vid=vid, auto=False)
                if album == None:
                    return []

                album.totalPlayNum = v['count']
                db._save_update_append(ret, album)

        return ret

# 更新节目的完整信息
class ParserAlbumMvInfo(KolaParser):
    def __init__(self, album=None, albumName=None):
        super().__init__()

        if album and albumName:
            self.cmd['name']      = 'engine_parser'
            self.cmd['regular']   = ['var video_album_videos_result=(\{.*.\})']
            self.cmd['source']    = 'http://search.vrs.sohu.com/mv_i%s.json' % album.sohu['vid']
            self.cmd['albumName'] = albumName

    # 通过 vid 获得节目更多的信息
    # http://search.vrs.sohu.com/mv_i1268037.json
    # sohu_album_mvinfo
    # sohu_sohu_album_mvinfo_mini
    def CmdParser(self, js):
        db = SohuDB()
        ret = []

        text = tornado.escape.to_basestring(js['data'])
        if self.name == 'ParserAlbumMvInfoMini':
            text = '{' + text + '}'
        json = tornado.escape.json_decode(text)

        albumName = ''
        playlistid = ''
        if 'albumName' in js:
            albumName = js['albumName']

        if 'playlistId' in json :
            playlistid = autostr(json['playlistId'])

        album = db.GetAlbumFormDB(playlistid=playlistid, albumName=albumName) #, vid=vid)
        if album == None:
            return ret

        if 'videos' in json and json['videos']:
            video = json['videos'][0]

            if 'isHigh' in video          : album.isHigh = str(video['isHigh'])
            if 'videoScore' in video      : album.videoScore = str(video['videoScore'])

#                 for video in json['videos']:
#                     v = album.newVideo()
#                     v.LoadFromJson(video)
#
#                     tv.videos.append(v)
        if album.sohu['playlistid']:
            db._save_update_append(ret, album, upsert=False)

        return ret

# 更新节目的完整信息, 只是通过vid 拿到 playlistid
class ParserAlbumMvInfoMini(ParserAlbumMvInfo):
    def __init__(self, album=None, alubmName=None):
        super().__init__(album, alubmName)
        self.cmd['regular'] =  ['("playlistId":\w+)'],

# 搜狐节目指数
class ParserAlbumScore(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['name']   = 'engine_parser'
            self.cmd['source'] = 'http://index.tv.sohu.com/index/switch-aid/%s' % album.sohu['playlistid']
            self.cmd['json']   =  [
                    'attachment.album',
                    'attachment.index'
                ]

    def CmdParser(self, js):
        ret = []

        data = tornado.escape.json_decode(js['data'])
        if 'album' in data and 'index' in data:
            js = data['album']
            index = data['index']
            if js and index:
                playlistid = ''
                if 'id' in js:
                    playlistid = autostr(js['id'])
                if not playlistid:
                    return []

                db = SohuDB()
                album = db.GetAlbumFormDB(playlistid=playlistid)
                if album == None:
                    return []

                if 'dailyPlayNum' in index:
                    album.dailyPlayNum    = index['dailyPlayNum']    # 每日播放次数
                if 'weeklyPlayNum' in index:
                    album.weeklyPlayNum   = index['weeklyPlayNum']   # 每周播放次数
                if 'monthlyPlayNum' in index:
                    album.monthlyPlayNum  = index['monthlyPlayNum']  # 每月播放次数
                if 'totalPlayNum' in index:
                    album.totalPlayNum    = index['totalPlayNum']    # 总播放资料
                if 'dailyIndexScore' in index:
                    album.dailyIndexScore = index['dailyIndexScore'] # 每日指数

                db._save_update_append(ret, album, upsert=False)

        return ret

# http://count.vrs.sohu.com/count/query.action?videoId=1268037
# 更新热门节目信息
class ParserAlbumHotList(KolaParser):
    def __init__(self, url=None):
        super().__init__()
        if url:
            self.cmd['name']   = 'engine_parser'
            self.cmd['source'] = url

    def CmdParser(self, js):
        db = SohuDB()
        ret = []

        js = tornado.escape.json_decode(js['data'])

        album = None
        if 'r' in js:
            for p in js['r']:
                if 'aid' in p:
                    album = db.GetAlbumFormDB(playlistid=p['aid'])
                    if album:
                        album.UpdateFullInfoCommand()
                        album.UpdateScoreCommand()
                        ret.append(album)

        return ret

# 更新节目的播放信息
class ParserAlbumPlayInfo(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['name']   = 'engine_parser'
            self.cmd['source'] = album.GetVideoPlayUrl()
            self.cmd['cid']    = album.cid
            self.cmd['json'] = [
                    'data.highVid',
                    'data.norVid',
                    'data.oriVid',
                    'data.superVid',
                    'data.relativeId',
                    'id'
                ]

    def CmdParser(self, js):
        db = SohuDB()

        data = tornado.escape.json_decode(js['data'])
        if ('id' not in data) and ('vid' not in data) and ('cid' not in js):
            return

        cid = js['cid']
        vid = ''
        if 'id' in data:
            vid = autostr(data['id'])
        elif 'vid' in js:
            vid = autostr(data['vid'])

        if vid and cid:
            video = SohuVideo()
            video.vid = vid
            video.cid = cid
        else:
            return

        video.SetVideoScript('default', vid)
        if 'highVid' in data:
            video.highVid    = autostr(data['highVid'])
            video.SetVideoScript('high', video.highVid)
        if 'norVid' in data:
            video.norVid     = autostr(data['norVid'])
            video.SetVideoScript('normal', video.norVid)
        if 'oriVid' in data:
            video.oriVid     = autostr(data['oriVid'])
            video.SetVideoScript('original', video.oriVid)
        if 'superVid' in data:
            video.superVid   = autostr(data['superVid'])
            video.SetVideoScript('super', video.superVid)
        if 'relativeId' in data:
            video.relativeId = autostr(data['relativeId'])
            video.SetVideoScript('relative', video.relativeId)

        if video.highVid or video.norVid or video.oriVid or video.superVid or video.relativeId:
            db.SaveVideo(video)

class SohuVideoMenu(VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)

        if hasattr(self, 'number'):
            self.HomeUrlList = ['http://so.tv.sohu.com/list_p1%d_p20_p3_p40_p5_p6_p73_p80_p9_2d1_p101_p11.html' % self.number]
        else:
            self.HomeUrlList = []

        self.albumClass = SohuAlbum

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            ParserAlbumList(url, self.cid).Execute()

    def UpdateHotList(self):
        # http://so.tv.sohu.com/iapi?v=4&c=115&t=1&sc=115101_115104&o=3&encode=GBK
        fmt = 'http://so.tv.sohu.com/iapi?v=%d&c=%d&sc=%s&o=3'
        v = 4
        if self.number == 100:
            v = 2
        sc = ''
        if '类型' in self.filter:
            for (_, v) in list(self.filter['类型'].items()):
                sc = sc + v + '_'
        url = fmt % (v, self.number, sc)

        ParserAlbumHotList(url).Execute()

    def UpdateHotList2(self):
        # http://so.tv.sohu.com/jsl?c=100&area=5&cate=100102_100122&o=1&encode=GBK
        fmt = 'http://so.tv.sohu.com/jsl?c=%d&cate=%s&o=1'
        sc = ''
        if '类型' in self.filter:
            for (_, v) in list(self.filter['类型'].items()):
                sc += v + '_'
        url = fmt % (v, self.number, sc)

        ParserAlbumHotList(url).Execute()

# 电影
class SohuMovie(SohuVideoMenu):
    def __init__(self, name):
        self.number = 100
        super().__init__(name)
        self.cid = 1

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 电视
class SohuTV(SohuVideoMenu):
    def __init__(self, name):
        self.number = 101
        super().__init__(name)
        self.cid = 2

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 动漫
class SohuComic(SohuVideoMenu):
    def __init__(self, name):
        self.number = 115
        super().__init__(name)

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 综艺
class SohuShow(SohuVideoMenu):
    def __init__(self, name):
        self.number = 106
        super().__init__(name)

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 记录片
class SohuDocumentary(SohuVideoMenu):
    def __init__(self, name):
        self.number = 107
        super().__init__(name)

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 教育
class SohuEdu(SohuVideoMenu):
    def __init__(self, name):
        self.number = 119
        super().__init__(name)

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 新闻
class SohuNew(SohuVideoMenu):
    def __init__(self, name):
        self.number = 122
        super().__init__(name)

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 娱乐
class SohuYule(SohuVideoMenu):
    def __init__(self, name):
        self.number = 112
        super().__init__(name)

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 旅游
class SohuTour(SohuVideoMenu):
    def __init__(self, name):
        self.number = 131
        super().__init__(name)

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# Sohu 搜索引擎
class SohuEngine(VideoEngine):
    def __init__(self):
        super().__init__()

        self.engine_name = 'SohuEngine'
        self.albumClass = SohuAlbum

        # 引擎主菜单
        self.menu = {
            '电影'   : SohuMovie,
            '电视剧' : SohuTV,
           # '综艺'   : SohuShow,
           # '娱乐'   : SohuYule,
           # '动漫'   : SohuComic,
           # '纪录片' : SohuDocumentary,
           # '教育'   : SohuEdu,
           # '旅游'   : SohuTour,
           # '新闻'   : SohuNew
        }

        self.parserList = {
            ParserAlbumList(),
            ParserAlbumFullInfo(),
            ParserAlbumTotalPlayNum(),
            ParserAlbumMvInfo(),
            ParserAlbumMvInfoMini(),
            ParserAlbumScore(),
            ParserAlbumHotList(),
            ParserAlbumPlayInfo(),
        }
