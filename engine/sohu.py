#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time

from bs4 import BeautifulSoup as bs
import tornado.escape

from kola import DB, Singleton, utils
import kola

from .engines import VideoEngine, KolaParser, KolaAlias, EngineVideoMenu


global Debug
Debug = True

class SohuAlias(KolaAlias):
    def __init__(self):
        self.alias = {
            #'内地' : '内地',
            '港剧' : '香港',
            '台剧' : '台湾',
            '美剧' : '美国',
            '韩剧' : '韩国',
            '英剧' : '英国',
            '泰剧' : '泰国',
            '日剧' : '日本',
            '其他' : '其他',
            '情景片' : '剧情片',
            '游戏竞技' : '游戏',
            '娱乐节目' : '娱乐'
        }

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

        self.sohu = SohuPrivate()

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
    def UpdateFullInfo(self):
        if self.sohu.playlistid:
            ParserAlbumFullInfo(self.sohu.playlistid, self.sohu.vid).AddCommand()

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        if self.sohu.playlistid:
            ParserAlbumCount(self).Execute()
            ParserAlbumScore(self).Execute()

class SohuDB(DB, Singleton):
    def __init__(self):
        super().__init__()

    def GetMenuAlbumList(self, cid,All=False):
        fields = {'engineList' : True,
                  'albumName': True,
                  'private'  : True,
                  'cid'      : True,
                  'vid'      : True}

        data = self.album_table.find({'engineList' : {'$in' : ['SohuEngine']}, 'cid' : cid}, fields)

        albumList = []
        for p in data:
            album = SohuAlbum()
            album.LoadFromJson(p)
            albumList.append(album)

        return albumList

    # 从数据库中找到 album
    def FindAlbumJson(self, playlistid='', albumName='', vid=''):
        playlistid = utils.autostr(playlistid)
        vid = utils.autostr(vid)
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
            if albumName:
                album.SetNameAndVid(albumName)

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
            self.cmd['cache']   = False

    def CmdParser(self, js):
        if not js['data']: return
        cid = js['cid']

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
                    vid = utils.autostr(u[1])
                elif u[0] == '_s_a':
                    playlistid = utils.autostr(u[1])

            Found = db.FindAlbumJson(playlistid=playlistid, vid=vid)
            if not Found:
                if not needNextPage:
                    needNextPage = True
                if playlistid and vid:
                    ParserAlbumFullInfo(playlistid, vid, cid).AddCommand()

        #needNextPage = True
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
    alias = SohuAlias()
    def __init__(self, playlistid=None, vid=None, cid=None):
        super().__init__()
        if playlistid and vid and cid:
            #self.cmd['source'] = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&pagesize=1&playlistid=%s&vid=%s' % (playlistid, vid)
            self.cmd['source'] = 'http://pl.hd.sohu.com/videolist?encoding=utf-8&pagesize=1&playlistid=%s&vid=%s' % (playlistid, vid)
            self.cmd['cid'] = cid

    # 解析节目的完全信息
    # http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5112241
    # sohu_album_fullinfo
    def CmdParser(self, js):
        db = SohuDB()
        cid = js['cid']

        json = tornado.escape.json_decode(js['data'])
        playlistid = utils.autostr(json['playlistid'])
        vid = utils.autostr(json['vid'])
        pid = utils.autostr(json['pid'])
        albumName = db.GetAlbumName(json['albumName'])
        if not albumName:
            return

        album = db.GetAlbumFormDB(playlistid=playlistid, albumName=albumName, vid=vid, auto=True)
        if album == None:
            return

        if 'cid' in json            : album.cid             = cid
        if 'playlistid' in json     : album.sohu.playlistid = playlistid
        if 'pid' in json            : album.sohu.pid        = pid
        if 'vid' in json            : album.sohu.vid        = vid

        if 'isHigh' in json         : album.isHigh         = json['isHigh']
        if 'area' in json           : album.area           = self.alias.Get(json['area'])
        if 'categories' in json     : album.categories     = ParserAlbumFullInfo.alias.GetList(json['categories'])
        if 'publishYear' in json    : album.publishYear    = utils.autoint(json['publishYear'])
        if 'updateTime' in json     : album.updateTime     = int(json['updateTime'] / 1000)

        # 图片
        if 'largeHorPicUrl' in json : album.largeHorPicUrl = json['largeHorPicUrl']
        if 'smallHorPicUrl' in json : album.smallHorPicUrl = json['smallHorPicUrl']
        if 'largeVerPicUrl' in json : album.largeVerPicUrl = json['largeVerPicUrl']
        if 'smallVerPicUrl' in json : album.smallVerPicUrl = json['smallVerPicUrl']
        if 'largePicUrl' in json    : album.largePicUrl    = json['largePicUrl']
        if 'smallPicUrl' in json    : album.smallPicUrl    = json['smallPicUrl']

        if 'albumDesc' in json      : album.albumDesc      = json['albumDesc']

        if 'mainActors' in json     : album.mainActors     = json['mainActors']
        if 'directors' in json      : album.directors      = json['directors']

        if 'videos' in json and json['videos']:
            video = json['videos'][0]
            if 'publishTime' in video:
                t = time.mktime(time.strptime(video['publishTime'],"%Y-%m-%d"))
                album.publishTime = t
        elif album.publishYear:
            Y = '%d-01-01' % (album.publishYear)
            t = time.mktime(time.strptime(Y,"%Y-%m-%d"))
            album.publishTime = t

        album.sohu.videoListUrl = utils.GetScript('sohu', 'get_videolist', [album.vid, album.sohu.playlistid, album.sohu.vid])

        db.SaveAlbum(album)

class ParserAlbumScore(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['source'] = 'http://vote.biz.itc.cn/count_v77_t2_i%s_b_c.json' % album.sohu.playlistid
            self.cmd['pid'] = album.sohu.playlistid
            self.cmd['cache'] = False

    def CmdParser(self, js):
        playlistid = js['pid']
        text = re.findall('.*=({[\s\S]*})', js['data'])
        if text:
            data = tornado.escape.json_decode(text[0])
            db = SohuDB()
            album = db.GetAlbumFormDB(playlistid=playlistid)
            if album == None:
                return []

            totalCount = data['totalCount_77']
            totalScore = data['totalScore_77']
            if totalCount == 0:
                album.Score = totalScore
            else:
                album.Score = totalScore * 1.0 / totalCount
            db.SaveAlbum(album, upsert=False)

# http://count.vrs.sohu.com/count/query.action?videoId=1268037
# 搜狐节目指数
class ParserAlbumCount(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['source'] = 'http://index.tv.sohu.com/index/switch-aid/%s' % album.sohu.playlistid
            self.cmd['json']   =  [
                    'attachment.album',
                    'attachment.index'
                ]
            self.cmd['cache'] = False

    def CmdParser(self, js):
        data = tornado.escape.json_decode(js['data'])
        if 'album' in data and 'index' in data:
            album_js = data['album']
            index = data['index']
            if album_js and index:
                playlistid = ''
                if 'id' in album_js:
                    playlistid = utils.autostr(album_js['id'])
                if not playlistid:
                    return []

                db = SohuDB()
                album = db.GetAlbumFormDB(playlistid=playlistid)
                if album == None:
                    return []

                if 'dailyPlayNum' in index:
                    album.dailyPlayNum    = utils.autoint(index['dailyPlayNum'])   # 每日播放次数
                if 'weeklyPlayNum' in index:
                    album.weeklyPlayNum   = utils.autoint(index['weeklyPlayNum'])  # 每周播放次数
                if 'monthlyPlayNum' in index:
                    album.monthlyPlayNum  = utils.autoint(index['monthlyPlayNum']) # 每月播放次数
                if 'totalPlayNum' in index:
                    album.totalPlayNum    = utils.autoint(index['totalPlayNum'])   # 总播放资料

                db.SaveAlbum(album, upsert=False)

class SohuVideoMenu(EngineVideoMenu):
    def __init__(self, name):
        super().__init__(name)

        if hasattr(self, 'number'):
            self.HomeUrlList = ['http://so.tv.sohu.com/list_p1%d_p20_p3_p40_p5_p6_p73_p80_p9_2d1_p101_p11.html' % self.number]
        else:
            self.HomeUrlList = []

        self.albumClass = SohuAlbum
        self.DBClass = SohuDB

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            ParserAlbumList(url, self.cid).Execute()

# 电影
class SohuMovie(SohuVideoMenu):
    def __init__(self, name):
        self.number = 100
        super().__init__(name)
        self.cid = 1

# 电视
class SohuTV(SohuVideoMenu):
    def __init__(self, name):
        self.number = 101
        super().__init__(name)
        self.cid = 2

# 动漫
class SohuComic(SohuVideoMenu):
    def __init__(self, name):
        self.number = 115
        super().__init__(name)
        self.cid = 3

# 记录片
class SohuDocumentary(SohuVideoMenu):
    def __init__(self, name):
        self.number = 107
        super().__init__(name)
        self.cid = 4

# 综艺
class SohuShow(SohuVideoMenu):
    def __init__(self, name):
        self.number = 106
        super().__init__(name)
        self.cid = 5

# 教育
class SohuEdu(SohuVideoMenu):
    def __init__(self, name):
        self.number = 119
        super().__init__(name)

# 新闻
class SohuNew(SohuVideoMenu):
    def __init__(self, name):
        self.number = 122
        super().__init__(name)

# 娱乐
class SohuYule(SohuVideoMenu):
    def __init__(self, name):
        self.number = 112
        super().__init__(name)

# 旅游
class SohuTour(SohuVideoMenu):
    def __init__(self, name):
        self.number = 131
        super().__init__(name)

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
           SohuComic('动漫'), # 动漫
           SohuDocumentary('纪录片'), # 纪录片
           #SohuEdu('教育'), # 教育
           #SohuTour('旅游'), # 旅游
           SohuShow('综艺'), # 综艺
           #SohuNew('新闻') # 新闻
           #SohuYule('娱乐'), # 娱乐
        ]

        self.parserList = [
            ParserAlbumList(),
            ParserAlbumFullInfo(),
            ParserAlbumScore(),
            ParserAlbumCount(),
        ]
