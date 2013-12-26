#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from bs4 import BeautifulSoup as bs
import tornado.escape

import engine
from engine import VideoEngine, KolaParser
from kola import DB, autostr, autoint, Singleton, utils
import kola


#================================= 以下是搜狐视频的搜索引擎 =======================================
global Debug
Debug = True

class SohuVideo(kola.VideoBase):
    def SaveToJson(self):
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)

class SohuPrivate:
    def __init__(self):
        self.name =  '搜狐'
        self.playlistid = ''
        self.vid = ''
        self.pid = ''
        self.videoListUrl = {}

    def Json(self):
        json = {'name' : self.name}
        if self.playlistid   : json['playlistid'] = self.playlistid
        if self.vid          : json['vid'] = self.vid
        if self.pid          : json['vid'] = self.pid
        if self.videoListUrl : json['videoListUrl'] = self.videoListUrl

        return json

    def Load(self, js):
        if 'name' in js         : self.name         = js['name']
        if 'playlistid' in js   : self.playlistid   = js['playlistid']
        if 'pid' in js          : self.pid          = js['pid']
        if 'vid' in js          : self.vid          = js['vid']
        if 'videoListUrl' in js : self.videoListUrl = js['videoListUrl']

class SohuAlbum(kola.AlbumBase):
    def __init__(self):
        self.engineName = 'SohuEngine'
        super().__init__()
        self.albumPageUrl = ''

        self.sohu = SohuPrivate()

        self.videoClass = SohuVideo

    def SaveToJson(self):
        if self.sohu:
            self.private[self.engineName] = self.sohu.Json()
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if self.engineName in self.private:
            self.sohu.Load(self.private[self.engineName])

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        if self.sohu.playlistid:
            ParserAlbumFullInfo(self.sohu.playlistid, self.sohu.vid).AddCommand()
        #if self.sohu.vid:
        #    ParserAlbumMvInfo(self, self.albumName).AddCommand()

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        if self.sohu.playlistid:
            ParserAlbumScore(self).Execute()

class SohuDB(DB, Singleton):
    def __init__(self):
        super().__init__()

    def GetMenuAlbumList(self, cid,All=False):
        fields = {'engineList' : True,
                              'albumName': True,
                              'private': True,
                              'cid': True,
                              'vid': True}

        data = self.album_table.find({'engineList' : {'$in' : ['SohuEngine']}, 'cid' : cid}, fields)

        albumList = []
        for p in data:
            album = SohuAlbum()
            album.LoadFromJson(p)
            albumList.append(album)

        return albumList

    # 从数据库中找到 album
    def FindAlbumJson(self, playlistid='', albumName='', vid=''):
        playlistid = autostr(playlistid)
        vid = autostr(vid)
        if playlistid == '' and albumName == '' and vid == '':
            return None

        f = []
        if albumName :    f.append({'albumName'                     : albumName})
        if playlistid :   f.append({'private.SohuEngine.playlistid' : playlistid})
        if vid :          f.append({'private.SohuEngine.vid'        : vid})

        #return self.album_table.find_one({'$or' : f})
        return self.album_table.find_one({'engineList' : {'$in' : ['SohuEngine']}, '$or' : f})

    # 从数据库中找到album
    def GetAlbumFormDB(self, playlistid='', albumName='', vid='', auto=False):
        album = None
        json = self.FindAlbumJson(playlistid, albumName, vid)
        if json:
            album = SohuAlbum()
            album.LoadFromJson(json)
        elif auto:
            album = SohuAlbum()
            if playlistid   : album.sohu.playlistid = playlistid
            if vid          : album.sohu.vid        = vid
            if albumName    : album.mName = albumName

        return album

    def SaveAlbum(self, album, upsert=True):
        if album.sohu.vid and album.albumName and album.sohu.playlistid:
            self._save_update_append(None, album, key={'private.SohuEngine.vid' : album.sohu.vid}, upsert=upsert)

# 搜狐节目列表
class ParserAlbumList(KolaParser):
    def __init__(self, url=None, cid=0):
        super().__init__()
        if url:
            self.cmd['regular'] = ['(<li class="clear">|<p class="tit tit-p.*|<em class="pay"></em>|\t</li>)']
            self.cmd['source']  = url
            self.cmd['cid']     = cid

    def CmdParser(self, js):
        if not js['data']: return

        db = SohuDB()
        needNextPage = False
        soup = bs(js['data'])#, from_encoding = 'GBK')
        playlist = soup.findAll('li')
        for a in playlist:
            text = a.prettify()
            x = re.findall('pay', text)
            if x:
                continue

            vid = ''
            playlistid = ''

            urls = re.findall('(_s_v|_s_a)="([\s\S]*?)"', text)
            for u in urls:
                if u[0] == '_s_v':
                    vid = autostr(u[1])
                elif u[0] == '_s_a':
                    playlistid = autostr(u[1])

            if (not needNextPage) and (not db.FindAlbumJson(playlistid=playlistid, vid=vid)):
                needNextPage = True
            if playlistid and vid:
                ParserAlbumFullInfo(playlistid, vid).AddCommand()

        needNextPage = True
        if needNextPage:
            g = re.search('p10(\d+)', js['source'])
            if g:
                current_page = int(g.group(1))
                link = re.compile('p10\d+')
                newurl = re.sub(link, 'p10%d' % (current_page + 1), js['source'])
                ParserAlbumList(newurl, js['cid']).AddCommand()

        self.command.Execute()

# 更新节目的完整信息
class ParserAlbumFullInfo(KolaParser):
    def __init__(self, playlistid=None, vid=None):
        super().__init__()
        if playlistid and vid:
            self.cmd['source'] = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&pagesize=1&playlistid=%s&vid=%s' % (playlistid, vid)

    # 解析节目的完全信息
    # http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5112241
    # sohu_album_fullinfo
    def CmdParser(self, js):
        db = SohuDB()

        json = tornado.escape.json_decode(js['data'])
        playlistid = autostr(json['playlistid'])
        vid = autostr(json['vid'])
        pid = autostr(json['pid'])
        albumName = db.GetAlbumName(json['albumName'])
        if not albumName:
            return

        album = db.GetAlbumFormDB(playlistid=playlistid, vid=vid)
        if album == None:
            album = SohuAlbum()
            album_js = DB().FindAlbumJson(albumName=albumName)
            if album_js:
                    album.LoadFromJson(album_js)

        album.albumName       = albumName
        album.vid             = utils.genAlbumId(album.albumName)

        if 'albumPageUrl' in json   : album.albumPageUrl    = json['albumPageUrl']
        if 'cid' in json            : album.cid             = autoint(json['cid'])
        if 'playlistid' in json     : album.sohu.playlistid = playlistid
        if 'pid' in json            : album.sohu.pid        = pid
        if 'vid' in json            : album.sohu.vid        = vid

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
        #if 'totalSet' in json       : album.totalSet       = json['totalSet']
        #if 'updateSet' in json      : album.updateSet      = json['updateSet']

        if 'mainActors' in json     : album.mainActors     = json['mainActors']
        if 'directors' in json      : album.directors      = json['directors']

        album.sohu.videoListUrl = {
            'script': 'sohu',
            'function' : 'get_videolist',
            'parameters' : [album.vid, album.sohu.playlistid, album.sohu.vid]
        }

        db.SaveAlbum(album)

# 更新节目的完整信息
class ParserAlbumMvInfo(KolaParser):
    def __init__(self, album=None, albumName=None):
        super().__init__()

        if album and albumName:
            self.cmd['regular']   = ['var video_album_videos_result=(\{.*.\})']
            self.cmd['source']    = 'http://search.vrs.sohu.com/mv_i%s.json' % album.sohu.vid
            self.cmd['albumName'] = albumName

    # 通过 vid 获得节目更多的信息
    # http://search.vrs.sohu.com/mv_i1268037.json
    # sohu_album_mvinfo
    # sohu_sohu_album_mvinfo_mini
    def CmdParser(self, js):
        db = SohuDB()

        text = tornado.escape.to_basestring(js['data'])
        json = tornado.escape.json_decode(text)

        albumName = ''
        playlistid = ''
        if 'albumName' in js:
            albumName = js['albumName']

        if 'playlistId' in json :
            playlistid = autostr(json['playlistId'])

        album = db.GetAlbumFormDB(playlistid=playlistid, albumName=albumName) #, vid=vid)
        if album == None:
            return

        if 'videos' in json and json['videos']:
            video = json['videos'][0]

            if 'isHigh' in video          : album.isHigh = str(video['isHigh'])
            if 'videoScore' in video      : album.videoScore = str(video['videoScore'])

            db.SaveAlbum(album, upsert=False)

# 搜狐节目指数
class ParserAlbumScore(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['source'] = 'http://index.tv.sohu.com/index/switch-aid/%s' % album.sohu.playlistid
            self.cmd['json']   =  [
                    'attachment.album',
                    'attachment.index'
                ]

    def CmdParser(self, js):
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

                db.SaveAlbum(album, upsert=False)

# http://count.vrs.sohu.com/count/query.action?videoId=1268037
# 更新热门节目信息
class ParserAlbumHotList(KolaParser):
    def __init__(self, url=None):
        super().__init__()
        if url:
            self.cmd['source'] = url

    def CmdParser(self, js):
        db = SohuDB()

        js = tornado.escape.json_decode(js['data'])

        album = None
        if 'r' in js:
            for p in js['r']:
                if 'aid' in p:
                    album = db.GetAlbumFormDB(playlistid=p['aid'])
                    if album:
                        album.UpdateFullInfoCommand()
                        album.UpdateScoreCommand()

class SohuVideoMenu(kola.VideoMenuBase):
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

    def UpdateAllScore(self):
        for album in SohuDB().GetMenuAlbumList(self.cid):
            album.UpdateScoreCommand()

        engine.EngineCommands().Execute()

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
        self.menu = [
            SohuMovie('电影'), # 电影
            SohuTV('电视剧'), # 电视剧
           #SohuShow('综艺'), # 综艺
           #SohuYule('娱乐'), # 娱乐
           #SohuComic('动漫'), # 动漫
           #SohuDocumentary('纪录片'), # 纪录片
           #SohuEdu('教育'), # 教育
           #SohuTour('旅游'), # 旅游
           #SohuNew('新闻') # 新闻
        ]

        self.parserList = [
            ParserAlbumList(),
            ParserAlbumFullInfo(),
            ParserAlbumMvInfo(),
            ParserAlbumScore(),
            ParserAlbumHotList(),
        ]
