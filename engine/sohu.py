#! /usr/bin/python3
# -*- coding: utf-8 -*-

import traceback
import sys
import json
import re
import hashlib
import tornado.escape

from bs4 import BeautifulSoup as bs
from engine import VideoEngine, KolaParser, EngineCommands
from kola import autostr, autoint, log, Singleton
from kola import VideoBase, AlbumBase, VideoMenuBase, DB

#================================= 以下是搜狐视频的搜索引擎 =======================================
MAX_TRY = 3

global Debug
Debug = True

class SohuDB(DB, Singleton):
    def __init__(self):
        super().__init__()

    # 从数据库中找到 album
    def FindAlbumJson(self, playlistid='', albumName='', vid='', auto=False):
        playlistid = autostr(playlistid)
        vid = autostr(vid)
        if playlistid == '' and albumName == '' and vid == '':
            return None

        f = []
        if playlistid :   f.append({'playlistid'   : playlistid})
        if albumName :    f.append({'albumName'    : albumName})
        if vid :          f.append({'vid'          : vid})

        return self.album_table.find_one({"$or" : f})

    # 从数据库中找到album
    def GetAlbumFormDB(self, playlistid='', albumName='', vid='', auto=False):
        tv = None
        json = self.FindAlbumJson(playlistid, albumName, vid, auto)
        if json:
            tv = SohuAlbum()
            tv.LoadFromJson(json)
        elif auto:
            tv = SohuAlbum()
            if playlistid   : tv.playlistid   = playlistid
            if albumName    : tv.albumName    = albumName

        return tv

    def UpdateVideoVid(self, js, res=[]):
        if ('id' not in js) and ('vid' not in js):
            return

        try:
            video = SohuVideo()
            if 'id' in js:
                video.vid = autostr(js['id'])
            elif 'vid' in js:
                video.vid = autostr(js['vid'])
            else:
                return

            if 'highVid' in js:    video.highVid    = autostr(js['highVid'])
            if 'norVid' in js:     video.norVid     = autostr(js['norVid'])
            if 'oriVid' in js:     video.oriVid     = autostr(js['oriVid'])
            if 'superVid' in js:   video.superVid   = autostr(js['superVid'])
            if 'relativeId' in js: video.relativeId = autostr(js['relativeId'])

            if video.highVid or video.norVid or video.oriVid or video.superVid or video.relativeId:
                self.SaveVideo(video)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.UpdateVideoPid:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

# 搜狐节目列表
class ParserAlbumList(KolaParser):
    def __init__(self, url=None):
        super().__init__()
        if url:
            self.cmd['name']    = 'engine_parser'
            self.cmd['regular'] = ['(<li class="clear">|<p class="tit tit-p.*|<em class="pay"></em>|\t</li>)']
            self.cmd['source']  = url

    def CmdParser(self, js):
        db = SohuDB()
        ret = []
        try:
            if not js['data']: return ret

            needNextPage = True
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
                        album.vid = autostr(u[1])
                    elif u[0] == '_s_a':
                        album.playlistid = autostr(u[1])

                if needNextPage and db.FindAlbumJson(vid=album.vid):
                    needNextPage = False
                if album.vid and album.albumName and album.playlistid:
                    db._save_update_append(ret, album, key={'vid' : album.vid})

            if needNextPage:
                g = re.search('p10(\d+)', js['source'])
                if g:
                    current_page = int(g.group(1))
                    link = re.compile('p10\d+')
                    newurl = re.sub(link, 'p10%d' % (current_page + 1), js['source'])
                    ParserAlbumList(newurl).Execute()
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserVideoList:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
        return ret

# 搜狐节目
class ParserAlbumPage(KolaParser):
    def __init__(self, url=None):
        super().__init__()
        if url:
            self.cmd['name']    = 'engine_parser',
            self.cmd['regular'] = ['var ((pid = PLAYLIST_ID = playlistId|playlistId|playlistid|PLAYLIST_ID|pid|vid|cid|playAble|playable)\s*=\W*([\d,]+))'],

    # 从分页的页面上解析该页上的节目
    # videolist
    def CmdParser(self, js):
        db = SohuDB()
        ret = []
        try:
            if not js['data']: return ret

            needNextPage = True
            soup = bs(js['data'])#, from_encoding = 'GBK')
            playlist = soup.findAll('li')
            for a in playlist:
                text = a.prettify()
                x = re.findall('pay', text)
                if x:
                    continue

                album = self.NewAlbum()

                urls = re.findall('(href|title|_s_v|_s_a)="([\s\S]*?)"', text)
                for u in urls:
                    if u[0] == 'href':
                        album.albumPageUrl = self.command.GetUrl(u[1])
                    elif u[0] == 'title':
                        album.albumName = u[1]
                    elif u[0] == '_s_v':
                        album.vid = autostr(u[1])
                    elif u[0] == '_s_a':
                        album.playlistid = autostr(u[1])

                if needNextPage and db.FindAlbumJson(vid=album.vid):
                    needNextPage = False
                if album.vid and album.albumName and album.playlistid:
                    db._save_update_append(ret, album, key={'vid' : album.vid})

            if needNextPage:
                g = re.search('p10(\d+)', js['source'])
                if g:
                    current_page = int(g.group(1))
                    link = re.compile('p10\d+')
                    newurl = re.sub(link, 'p10%d' % (current_page + 1), js['source'])
                    ParserAlbumList(newurl).Execute()
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserVideoList:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
        return ret


# 更新节目的完整信息
class ParserAlbumFullInfo(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['name']    = 'engine_parser'
            self.cmd['source'] = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=%s&vid=%s' % (album.playlistid, album.vid)

    # 解析节目的完全信息
    # http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5112241
    # sohu_album_fullinfo
    def CmdParser(self, js):
        db = SohuDB()

        ret = []
        try:
            json = tornado.escape.json_decode(js['data'])

            album = SohuAlbum()

            if 'cid' in json            : album.cid            = autoint(json['cid'])
            if 'playlistid' in json     : album.playlistid     = autostr(json['playlistid'])
            if 'pid' in json            : album.pid            = autostr(json['pid'])
            if 'vid' in json            : album.vid            = autostr(json['vid'])

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
                    if 'vid' in video and video['vid'] == autostr(album.vid) and album.vid:
                        if 'playLength' in video  : album.playLength =  video['playLength']
                        if 'publishTime' in video : album.publishTime = video['publishTime']

                    v = album.VideoClass()
                    v.playlistid = album.playlistid
                    v.pid = album.vid
                    v.cid = album.cid
                    v.LoadFromJson(video)
                    v.script = {
                        'script' : 'sohu',
                        'parameters' : [v.GetVideoPlayUrl(), autostr(album.cid)]
                    }

                    album.videos.append(v)
            if album.vid:
                db._save_update_append(ret, album, key={'vid' : album.vid}, upsert=False)
            else:
                print(album.vid)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumFullInfo:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

# 总播放次数，(如果没有指数的话）
class ParserAlbumTotalPlayNum(KolaParser):
    def __init__(self, album=None):
        super().__init__()

        if album:
            self.cmd['name']   = 'engine_parser'
            self.cmd['source'] = 'http://count.vrs.sohu.com/count/query.action?videoId=%s,' % album.vid

    # album_total_playnum
    def CmdParser(self, js):
        db = SohuDB()
        ret = []
        try:
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
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu._CmdParserAlbumTotalPlayNum:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

# 更新节目的完整信息
class ParserAlbumMvInfo(KolaParser):
    def __init__(self, album=None, source_url=None):
        super().__init__()

        if album and source_url:
            self.cmd['name']    = 'engine_parser'
            self.cmd['regular'] = ['var video_album_videos_result=(\{.*.\})']
            self.cmd['source'] = 'http://search.vrs.sohu.com/mv_i%s.json' % album.vid
            self.cmd['homePage'] = source_url

    # 通过 vid 获得节目更多的信息
    # http://search.vrs.sohu.com/mv_i1268037.json
    # sohu_album_mvinfo
    # sohu_sohu_album_mvinfo_mini
    def CmdParser(self, js):
        db = SohuDB()
        ret = []
        try:
            text = tornado.escape.to_basestring(js['data'])
            if js['name'] == 'sohu_album_mvinfo_mini':
                text = '{' + text + '}'
            json = tornado.escape.json_decode(text)

            if 'homePage' in js:
                album = SohuAlbum()
                album.albumPageUrl = js['homePage']
            else:
                return []

            if 'playlistId' in json :
                album.playlistid = autostr(json['playlistId'])

            if 'videos' in json and json['videos']:
                video = json['videos'][0]

                if 'isHigh' in video          : album.isHigh = str(video['isHigh'])
                if 'videoScore' in video      : album.videoScore = str(video['videoScore'])

#                 for video in json['videos']:
#                     v = tv.VideoClass()
#                     v.playlistid = tv.playlistid
#                     v.pid = tv.pid
#                     v.LoadFromJson(video)
#
#                     tv.videos.append(v)
            if album.playlistid:
                db._save_update_append(ret, album, upsert=False)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumMvInfo: %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret


# 更新节目的完整信息, 只是通过vid 拿到 playlistid
class ParserAlbumMvInfoMini(ParserAlbumMvInfo):
    def __init__(self, album=None, source_url=None):
        super().__init__(album, source_url)
        self.cmd['regular'] =  ['("playlistId":\w+)'],


# 搜狐节目指数
class ParserAlbumScore(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['name']   = 'engine_parser'
            self.cmd['source'] = 'http://index.tv.sohu.com/index/switch-aid/%s' % album.playlistid
            self.cmd['json']   =  [
                    'attachment.album',
                    'attachment.index'
                ]

    def CmdParser(self, js):
        db = SohuDB()
        ret = []
        try:
            data = tornado.escape.json_decode(js['data'])
            if 'album' in data:
                js = data['album']
                if js:
                    album = SohuAlbum()
                    if 'id' in js:
                        album.playlistid = autostr(js['id'])
                        if not album.playlistid:
                            return []

                    if 'index' in data:
                        index = data['index']
                        if index:
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
        except:
            print(js['source'])
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumScore:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

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
        try:
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
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserHotInfoByIapi  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret


# 更新节目的播放信息
class ParserAlbumPlayInfo(KolaParser):
    def __init__(self, url=None):
        super().__init__()
        if url:
            self.cmd['name']   = 'engine_parser'
            self.cmd['source'] = url
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
        ret = []
        try:
            data = tornado.escape.json_decode(js['data'])
            db.UpdateVideoVid(data)
        except:
            print(js['source'])
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu._CmdParserAlbumPlayInfo:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret


class SohuVideo(VideoBase):
    def __init__(self, js = None):
        super().__init__(js)

    def GetVideoPlayUrl(self, definition=0):
        vid = self.GetVid(definition)
        if vid:
            return 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
        else:
            return ''

    def SaveToJson(self):
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)

class SohuAlbum(AlbumBase):
    def __init__(self):
        super().__init__()
        self.albumPageUrl = ''
        self.engineList = []
        self.engineList.append('SohuEngine')

        self.VideoClass = SohuVideo

    def SaveToJson(self):
        if self.albumPageUrl: self.private['albumPageUrl'] = self.albumPageUrl
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if 'albumPageUrl' in self.private: self.albumPageUrl = self.private['albumPageUrl']

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        if self.albumPageUrl:
            if self.playlistid:
                ParserAlbumFullInfo(self).AddCommand()
            #if self.vid:
            #    ParserAlbumMvInfo(self, self.albumPageUrl).AddCommand()

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        if self.playlistid:
            ParserAlbumScore(self).Execute()

    # 更新节目主页
    def UpdateAlbumPageCommand(self):
        if self.albumPageUrl:
            ParserAlbumPage(self.albumPageUrl).Execute()

    # 更新节目播放信息
    def UpdateAlbumPlayInfoCommand(self):
        url = self.GetVideoPlayUrl()
        if url != '':
            ParserAlbumPlayInfo(url).AddCommand()

    def GetVideoPlayUrl(self, definition=0):
        vid = self.vid
        if vid:
            return 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
        else:
            return ''

class SohuVideoMenu(VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.command = EngineCommands()

        self.homePage = ''
        self.HomeUrlList = []
        if hasattr(self, 'number'):
            self.HomeUrlList = ['http://so.tv.sohu.com/list_p1%d_p20_p3_p40_p5_p6_p73_p80_p9_2d1_p101_p11.html' % self.number]

        self.albumClass = SohuAlbum

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            ParserAlbumList(url).Execute()

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


    def _ParserRealUrlStep3(self, text, url):
        db = SohuDB()
        try:
            ret = tornado.escape.json_decode(text)
            if type(ret) == str:
                ret = tornado.escape.json_decode(ret)

            db.UpdateVideoVid(ret)
            if 'sets' in ret:
                max_duration = 0.0
                m3u8 = ''
                video_count = len(ret['sets'])
                for u in ret['sets']:
                    new      = u['new']
                    url_tmp  = u['url']
                    duration = float(u['duration'])

                    start, _, _, key, _, _, _, _ = url_tmp.split('|')
                    u_tmp = '%s%s?key=%s' % (start[:-1], new, key)

                    if video_count == 1:
                        return u_tmp
                    m3u8 += '#EXTINF:%.0f\n%s\n' % (duration, u_tmp)
                    if duration > max_duration:
                        max_duration = duration

                m3u8 = '#EXTM3U\n#EXT-X-TARGETDURATION:%.0f\n%s#EXT-X-ENDLIST\n' % (max_duration, m3u8)

                name = hashlib.md5(m3u8.encode()).hexdigest()[16:]
                self.db.SetVideoCache(name, m3u8)

                return url + name
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine._ParserRealUrlStep2: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return ''

# 电影
class SohuMovie(SohuVideoMenu):
    def __init__(self, name):
        self.number = 100
        super().__init__(name)
        self.cid = 1
        self.homePage = 'http://tv.sohu.com/movieall/'

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 电视
class SohuTV(SohuVideoMenu):
    def __init__(self, name):
        self.number = 101
        super().__init__(name)
        self.cid = 2

        self.homePage = 'http://tv.sohu.com/tvall/'

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 动漫
class SohuComic(SohuVideoMenu):
    def __init__(self, name):
        self.number = 115
        super().__init__(name)
        self.homePage = 'http://tv.sohu.com/comicall/'

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 综艺
class SohuShow(SohuVideoMenu):
    def __init__(self, name):
        self.number = 106
        super().__init__(name)
        self.homePage = ''

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 记录片
class SohuDocumentary(SohuVideoMenu):
    def __init__(self, name):
        self.number = 107
        super().__init__(name)
        self.homePage = ''

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 教育
class SohuEdu(SohuVideoMenu):
    def __init__(self, name):
        self.number = 119
        super().__init__(name)
        self.homePage = ''

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
    def __init__(self, command):
        super().__init__(command)

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
            ParserAlbumPage(),
            ParserAlbumFullInfo(),
            ParserAlbumTotalPlayNum(),
            ParserAlbumMvInfo(),
            ParserAlbumMvInfoMini(),
            ParserAlbumScore(),
            ParserAlbumHotList(),
            ParserAlbumPlayInfo(),
        }
