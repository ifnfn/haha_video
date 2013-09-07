#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import traceback
import sys
import json
import re
# import BeautifulSoup as bs
from utils.BeautifulSoup import BeautifulSoup as bs
from utils.fetchTools import fetch_httplib2 as fetch
from pymongo import Connection
import ConfigParser

logging.basicConfig()
log = logging.getLogger("crawler")

COMMAND_HOST = 'http://127.0.0.1:9990/video/addcommand'
PARSER_HOST = 'http://127.0.0.1:9991/video/upload'

MAX_TRY = 3


# 命令管理器
class Commands:
    def __init__(self, host):
        self.cmdlist = {}
        self.commandHost = host

    # 注册解析器
    def AddTemplate(self, m):
        self.cmdlist[m['name']] = m

    def SendCommand(self, name, menu, url):
        if self.cmdlist.has_key(name):
            print "Add Command: ", url
            cmd = self.cmdlist[name]
            cmd['source'] = url
            cmd['menu'] = menu
            _, _, _, response = fetch(self.commandHost + '?' + name, 'POST', json.dumps(cmd))
            return response == ""
        return False

# 每个 Video 表示一个可以播放视频
class VideoBase:
    def __init__(self):
        self.data = {
            "smallPicUrl": "http://photocdn.sohu.com/20121119/vrss671283.jpg",
            "name": "十诫",
            "vid": 871321,
            "singerName": "",
            "playLength": 5749.6,
            "largePicUrl": "http://photocdn.sohu.com/20121119/vrsb671283.jpg",
            "publishTime": "2013-08-28",
            "pageUrl": "http://tv.sohu.com/20130828/n385287051.shtml",
            "subName": "",
            "singerIds": "",
            "order": "1",
            "showName": "十诫",
            "showDate": ""
        }

    # 获得播放视频源列表，返回m3u8
    def GetRealUrl(self, playurl):
        return ""

# 一个节目，表示一部电影、电视剧集
class AlbumBase:
    def __init__(self, parent):
        self.parent = parent
        self.command = parent.command

        self.albumName = ""
        self.albumPageUrl = ""
        self.pid = ""
        self.vid = ""
        self.cid = 0              # 菜单ID
        self.playlist_id  = ""
        self.area = ""            # 地区
        self.categories = []      # 类型
        self.publishYear = ""     # 发布年份
        self.isHigh      = 0      # 是否是高清

        self.largePicUrl = ""     # 大图片网址
        self.smallPicUrl = ""     # 小图片网址
        self.largeHorPicUrl = ''
        self.smallHorPicUrl = ''
        self.largeVerPicUrl = ''
        self.smallVerPicUrl = ''

        self.albumDesc = ""
        self.videoScore = ""

        self.defaultPageUrl  = "" # 当前播放集
        self.filmType        = "" # "TV" or ""
        self.totalSet        = "" # 总集数
        self.updateSet       = "" # 当前更新集
        self.dailyPlayNum    = 0  # 每日播放次数
        self.weeklyPlayNum   = 0  # 每周播放次数
        self.monthlyPlayNum  = 0  # 每月播放次数
        self.totalPlayNum    = 0  # 总播放资料
        self.dailyIndexScore = 0  # 每日指数

        self.mainActors = []
        self.actors = []
        self.directors = []

        self.data = {}
        '''
        self.data = {
            "playlistid": "",
            "vid": "",
            "pid": "",
            "albumPageUrl": "",
            "cid": 1,
            "albumName": "",
            "updateTime": 0,
            "isdl": 1,
            "size": 1,
            "fee": 0,
            "updateSet": 1,
            "smallPicUrl": "",
            "largeHorPicUrl": "",
            "smallHorPicUrl": "",
            "largePicUrl": "",
            "largeVerPicUrl": "",
            "smallVerPicUrl": "",
            "defaultPageUrl": "",
            "albumDesc": "",
            "publishYear": 0,
            "totalSet": 0,
            "updateNotification": "",
            "area": "",
            "mainActors": [
            ],
            "actors": [
            ],
            "categories": [
#                "剧情片",
            ],
            "directors": [
#                "塞西尔·B·戴米尔"
            ],
            "videos": [
                {
                    "smallPicUrl": "http://photocdn.sohu.com/20121119/vrss671283.jpg",
                    "name": "十诫",
                    "vid": 871321,
                    "singerName": "",
                    "playLength": 5749.6,
                    "largePicUrl": "http://photocdn.sohu.com/20121119/vrsb671283.jpg",
                    "publishTime": "2013-08-28",
                    "pageUrl": "http://tv.sohu.com/20130828/n385287051.shtml",
                    "subName": "",
                    "singerIds": "",
                    "order": "1",
                    "showName": "十诫",
                    "showDate": ""
                }
            ],
           "index": {
                "monthlyIndexRatio": 0.0,
                "monthlySearchNum": 0,
                "monthlyPlayRatio": 0,
                "totalIndexAveScore": 0,
                "totalIndexAveDays": 0,
                "monthlySearchRatio": 0,
                "totalSearchNum": 0,
                "monthlyIndexAveScore": 0,
                "dailySearchNum": 0,
                "dailyPlayNum": 0,
                "weeklyIndexAveScore": 0.0,
                "dailyIndexScore": 0.0,
                "dailyIndexRatio": 0.0,
                "createTime": 0,
                "totalPlayNum": 0,
                "dailySearchRatio": 0,
                "weeklyPlayRatio": 0.0,
                "dailyPlayRatio": 0.0,
                "weeklyIndexRatio": 0.0,
                "weeklySearchRatio":-0.0,
                "weeklyPlayNum": 0,
                "weeklySearchNum": 0,
                "albumChannelType": 0,
                "monthlyPlayNum": 0
            },
        }
        '''
        self.videos = []

    def SaveToJson(self):
        ret = {}
        ret['cid'] = self.cid

        if self.albumName != ''   : ret['albumName'] = self.albumName
        if self.albumPageUrl != '': ret['albumPageUrl'] = self.albumPageUrl
        if self.pid != ''         : ret['pid'] = self.pid
        if self.vid != ''         : ret['vid'] = self.vid
        if self.playlist_id != '' : ret['playlistid'] = self.playlist_id
        if self.isHigh != ''      : ret['isHigh'] = self.isHigh

        if self.area != ''        : ret['area'] = self.area
        if self.categories != []  : ret['categories'] = self.categories
        if self.publishYear != '' : ret['publishYear'] = self.publishYear

        if self.defaultPageUrl != '' : ret['defaultPageUrl'] = self.defaultPageUrl
        if self.albumDesc != ''      : ret['albumDesc'] = self.albumDesc
        if self.videoScore != ''     : ret['videoScore'] = self.videoScore
        if self.totalSet != ""       : ret['totalSet'] = self.totalSet
        if self.updateSet != ""      : ret['updateSet'] = self.updateSet

        # 图片
        if self.largeHorPicUrl != '' : ret['largeHorPicUrl'] = self.largeHorPicUrl
        if self.smallHorPicUrl != '' : ret['smallHorPicUrl'] = self.smallHorPicUrl
        if self.largeVerPicUrl != '' : ret['largeVerPicUrl'] = self.largeVerPicUrl
        if self.smallVerPicUrl != '' : ret['smallVerPicUrl'] = self.smallVerPicUrl

        if self.mainActors != []     : ret['mainActors'] = self.mainActors
        if self.actors != []         : ret['actors'] = self.actors
        if self.directors != []      : ret['directors'] = self.directors

        ret['index'] = {
            'dailyPlayNum'  : self.dailyPlayNum,     # 每日播放次数
            'weeklyPlayNum' : self.weeklyPlayNum,    # 每周播放次数
            'monthlyPlayNum': self.monthlyPlayNum,   # 每月播放次数
            'totalPlayNum'  : self.totalPlayNum,     # 总播放资料
            'totalPlayNum'  : self.dailyIndexScore,  # 每日指数
        }

        return ret

    def LoadFromJson(self, json):
        self.data = json

        # From DataBase
        if json.has_key('albumName')      : self.albumName = json['albumName']
        if json.has_key('albumPageUrl')   : self.albumPageUrl = json['albumPageUrl']
        if json.has_key('pid')            : self.pid = json['pid']
        if json.has_key('PId')            : self.pid = json['PId']
        if json.has_key('vid')            : self.vid = json['vid']
        if json.has_key('playlist_id')    : self.playlistid = json['playlist_id']
        if json.has_key('playlistid')     : self.playlistid = json['playlistid']
        if json.has_key('cid')            : self.playlistid = json['cid']
        if json.has_key('isHigh')         : self.isHigh = json['isHigh']

        if json.has_key('area')           : self.area = json['area']
        if json.has_key('categories')     : self.categories = json['categories']
        if json.has_key('publishYear')    : self.publishYear = json['publishYear']

        if json.has_key('defaultPageUrl') : self.defaultPageUrl = json['defaultPageUrl']

        # 图片
        if json.has_key('largeHorPicUrl') : self.largeHorPicUrl = json['largeHorPicUrl']
        if json.has_key('smallHorPicUrl') : self.smallHorPicUrl = json['smallHorPicUrl']
        if json.has_key('largeVerPicUrl') : self.largeVerPicUrl = json['largeVerPicUrl']
        if json.has_key('smallVerPicUrl') : self.smallVerPicUrl = json['smallVerPicUrl']

        if json.has_key('albumDesc')      : self.albumDesc = json['albumDesc']
        if json.has_key('videoScore')     : self.videoScore = json['videoScore']
        if json.has_key('totalSet')       : self.totalSet = json['totalSet']

        if json.has_key('mainActors')     : self.mainActors = json['mainActors']
        if json.has_key('actors')         : self.actors = json['actors']
        if json.has_key('directors')      : self.directors = json['directors']

        if json.has_key('index'):
            index = json['index']
            if index:
                if index.has_key('dailyPlayNum')   : self.dailyPlayNum    = index['dailyPlayNum']    # 每日播放次数
                if index.has_key('weeklyPlayNum')  : self.weeklyPlayNum   = index['weeklyPlayNum']   # 每周播放次数
                if index.has_key('monthlyPlayNum') : self.monthlyPlayNum  = index['monthlyPlayNum']  # 每月播放次数
                if index.has_key('totalPlayNum')   : self.totalPlayNum    = index['totalPlayNum']    # 总播放资料
                if index.has_key('dailyIndexScore'): self.dailyIndexScore = index['dailyIndexScore'] # 每日指数

        # 如果有视频数据
        if json.has_key('videos'):
            self.videos = []
            for v in json['videos']:
                video = SohuVideo(v)
                self.videos.append(video)
            del json['videos']
        self.data.update(json)

    # 发送节目信息更新命令
    def UpdateCommand(self):
        pass

    def SaveToDB(self, db):
        if self.albumName != "" and self.albumPageUrl != "":
            db.update({'albumName': self.albumName}, {"$set" : self.SaveToJson()}, upsert=True, multi=True)

# 一级分类菜单
class VideoMenuBase:
    def __init__(self, name, engine, url):
        self.command = engine.command
        self.filter = {}
        self.name = name
        self.url = url
        self.HotList = []
        self.engine = engine
        self.parserList = {}
        self.albumClass = AlbumBase

    def Reset(self):
        self.HotList = []

    # 根据 ID 从数据库中加载节目
    def GetAlbumById(self, playlist_id, auto = False):
        tv = None
        json = self.engine.album_table.find_one({'playlist_id': playlist_id})
        if json:
            tv = self.albumClass(self)
            tv.LoadFromJson(json)
        elif auto:
            tv = self.albumClass(self)
            tv.playlist_id = playlist_id

        return tv

    def GetAlbumByUrl(self, url, auto = False):
        tv = None
        json = self.engine.album_table.find_one({'albumPageUrl': url})
        if json:
            tv = self.albumClass(self)
            tv.LoadFromJson(json)
        elif auto:
            tv = self.albumClass(self)
            tv.albumPageUrl = url

        return tv

    def GetAlbumByAlbumName(self, albumName, auto = False):
        tv = None
        json = self.engine.album_table.find_one({'albumName': albumName})
        if json:
            tv = self.albumClass(self)
            tv.LoadFromJson(json)
        elif auto:
            tv = self.albumClass(self)
            tv.albumName = albumName

        return tv

    # 更新该菜单下所有节目完全信息
    def UpdateAllAlbumFullInfo(self):
        pgs = self.engine.album_table.find({'cid': self.cid},
                                                    fields = {'albumName': True,
                                                              'albumPageUrl': True,
                                                              'PId': True,
                                                              'vid': True,
                                                              'playlistid': True}
                                                    )
        for p in pgs:
            album = self.albumClass(self)
            album.LoadFromJson(p)
            album.UpdateCommand()

    # 更新热门节目表
    def UpdateHotList(self):
        self.HotList = []
        self.engine.UpdateHotList(self)

    # 更新本菜单节目网址，并提交命令服务器
    def UploadAlbumList(self):
        pass

    # 解析菜单网页解析
    def ParserHtml(self, name, js):
        ret = []
        if self.parserList.has_key(name):
            ret = self.parserList[name](js)
            for p in ret:
                p.SaveToDB(self.engine.album_table)

        return ret

    # 更新所有节目信息
    def UpdateAllAlbumInfo(self):
        pass

class VideoEngine:
    def __init__(self):
        self.engine_name = 'EngineBase'
        self.config = ConfigParser.ConfigParser()
        self.cmd_host = COMMAND_HOST
        self.parser_host = PARSER_HOST
        try:
            self.config.read("conf/engine.conf")
            if self.config.has_section('global'):
                if self.config.has_option('global', 'command_host'):
                    host = self.confg.get('global', 'command_host')
                    if host != '':
                        self.cmd_host = host

                if self.config.has_option('global', 'parser_host'):
                    host = self.confg.get('global', 'parser_host')
                    if host == '':
                        self.parser_host = host
        except:
            t, v, tb = sys.exc_info()
            log.error("VideoEngine.__init__:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        self.command = Commands(self.cmd_host)
        self.con = Connection('localhost', 27017)
        self.db = self.con.kola
        self.album_table = self.db.album

    # 获取节目一级菜单, 返回分类列表
    def GetMenu(self, times = 0):
        return []

    # 生成所有分页网址, 返回网址列表
    def GetHtmlList(self, playurl, times = 0):
        return []

    # 获取真实播放节目源地址
    def GetRealPlayUrl(self, playurl, times = 0):
        return []

    # 更新一级菜单首页热门节目表
    def UpdateHotList(self, menu, times = 0):
        pass

    # 获取节目的播放列表
    def GetAlbumPlayList(self, album, times = 0):
        pass

    # 将 BeautifulSoup的节目 tag 转成节目单
    def ParserAlbum(self, tag, album):
        return False

#================================= 以下是搜狐视频的搜索引擎 =======================================
SOHU_HOST = 'tv.sohu.com'

class SohuVideo(VideoBase):
    def __init__(self, v):
        pass

class SohuAlbum(AlbumBase):
    def __init__(self, parent):
        AlbumBase.__init__(self, parent)

    # 发送节目信息更新命令
    def UpdateCommand(self):
        if self.playlist_id != "":
            # 更新节目完整信息
            url = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=%s' % self.playlist_id
            self.command.SendCommand('album_fullinfo', self.parent.name, url)

            # 更新节目指数信息
            url = 'http://index.tv.sohu.com/index/switch-aid/%s' % self.playlist_id
            self.command.SendCommand('album_score', self.parent.name, url)

class SohuVideoMenu(VideoMenuBase):
    def __init__(self, name, engine, url):
        VideoMenuBase.__init__(self, name, engine, url)
        self.homePage = ''
        self.number = 0
        self.parserList = {
                   'videolist'     : self.CmdParserVideoList,
                   'album'         : self.CmdParserAlbum,
                   'album_score'   : self.CmdParserAlbumScore,
                   'videoall'      : self.CmdParserTVAll,
                   'albumlist_hot' : self.CmdParserHotInfoByIapi,
                   'album_full'    : self.CmdParserAlbumFullInfo,
                   'album_mvinfo'  : self.CmdParserAlbumMvInfo,
        }
        self.albumClass = SohuAlbum
        self.filter_year = [
                   {'{2013':''},
                   {'2012':''},
                   {'2011':''},
                   {'2010':''},
                   {'00年代':''},
                   {'90年代':''},
                   {'80年代':''},
                   {'更早':''}
        ]
        self.key = {
            '类型' : 'p2',
            '产地' : 'p3',
            '地区' : 'p3',
            '年份' : 'p4',
            '篇幅' : 'p5',
            '年龄' : 'p6',
            '排序' : 'p7',
            '状态' : 'p9',
            '页号' : 'p10',
            '语言' : 'p11',
        }

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        if self.homePage != "":
            self.command.SendCommand('videoall', self.name, self.homePage)

    # 获取所有节目列表的别一种方法，该方法备用
    def UpdateProgrameList2(self):
        for url in self.HomeUrlList:
            for page in self.engine.GetHtmlList(url):
                self.command.SendCommand('videolist', self.name, page)

    def UpdateHotInfo(self):
        # http://so.tv.sohu.com/iapi?v=4&c=115&t=1&sc=115101_115104&o=3&encode=GBK
        fmt = 'http://so.tv.sohu.com/iapi?v=%d&c=%d&sc=%s&o=3'
        v = 4
        if self.number == 100:
            v = 2
        sc = ''
        if self.filter.has_key('类型'):
            for (_, v) in self.filter['类型'].items():
                sc = sc + v + '_'
        url = fmt % (v, self.number, sc)

        self.command.SendCommand('albumlist_hot', self.name, url)

    def UpdateHotInfo2(self):
        # http://so.tv.sohu.com/jsl?c=100&area=5&cate=100102_100122&o=1&encode=GBK
        fmt = 'http://so.tv.sohu.com/jsl?c=%d&cate=%s&o=1'
        sc = ''
        if self.filter.has_key('类型'):
            for (_, v) in self.filter['类型'].items():
                sc += v + '_'
        url = fmt % (v, self.number, sc)

        self.command.SendCommand('albumlist_hot', self.name, url)

    # 解析热门节目
    # http://so.tv.sohu.com/iapi?v=4&c=115&t=1&sc=115101_115104&o=3
    # albumlist_hot
    def CmdParserHotInfoByIapi(self, js):
        ret = []
        try:
            text = js['data']
            js = json.loads(text)
            if js.has_key('r'):
                for p in js['r']:
                    if p.has_key('url'):
                        tv = self.GetAlbumByUrl(p['url'])
                        if tv:
                            tv.UpdateCommand()
                            ret.append(tv)
                    if p.has_key('aurl'):
                        tv = self.GetAlbumByUrl(p['aurl'])
                        if tv:
                            tv.UpdateCommand()
                            ret.append(tv)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserHotInfoByIapi  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

    # 通过 vid 获得节目信息
    # http://search.vrs.sohu.com/mv_i1268037.json
    # album_mvinfo
    def CmdParserAlbumMvInfo(self, js):
        ret = []
        try:
            text = js['data']
            g = re.search('var video_album_videos_result=(\{.*.\})', text)
            if g:
                playlist_id = ''
                a = json.loads(g.group(1))
                if a.has_key('playlistId'):
                    playlist_id = str(a['playlistId'])
                else:
                    return []

                if a.has_key('videos') and str(a['videos']) > 0:
                    tv = None
                    video = a['videos'][0]
                    if video.has_key('videoAlbumName'):
                        tv = self.GetAlbumByAlbumName(video['videoAlbumName'], False)
                    if tv == None:
                        return []

                    tv.playlist_id = playlist_id

                    if video.has_key('isHigh')          : tv.isHigh = str(video['isHigh'])
                    if video.has_key('albumDesc')       : tv.albumDesc = video['albumDesc']

                    if video.has_key('AlbumYear')       : tv.publishYear = str(video['AlbumYear'])
                    if video.has_key('videoScore')      : tv.videoScore = str(video['videoScore'])
                    if video.has_key('videoArea')       : tv.area = video['videoArea']
                    if video.has_key('videoMainActor')  : tv.mainActors = video['videoMainActor'].split(';') # 主演
                    if video.has_key('videoActor')      : tv.actors = video['videoActor'].split(';') # 演员
                    if video.has_key('videoDirector')   : tv.directors = video['videoDirector'].split(';') # 导演

                    if video.has_key('videoAlbumContCategory'):
                        tv.categories = video['videoAlbumContCategory'].split(';')

                    ret.append(tv)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumMvInfo: %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析节目的完全信息
    # http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5112241
    # album_full
    def CmdParserAlbumFullInfo(self, js):
        ret = []
        try:
            text = js['data']
            js = json.loads(text)
            p = self.GetAlbumById(js['playlistid'], True)

            p.LoadFromJson(js)
            p.SaveToDB(self.engine.album_table)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumFullInfo:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析所有节目列表
    # http://tv.sohu.com/tvall
    # videoall
    def CmdParserTVAll(self, js):
        ret = []
        '''
        test = [
                'http://tv.sohu.com/s2011/ajyh/',
                'http://store.tv.sohu.com/view_content/movie/5008825_704321.html',
                'http://tv.sohu.com/20120517/n343417005.shtml',
                'http://tv.sohu.com/s2012/zlyeye/',
                'http://store.tv.sohu.com/5009508/706684_1772.html'
                ]
        '''
        try:
            text = js['data']
            soup = bs(text)
            playlist = soup.findAll('li')
            for a in playlist:
                text = re.findall('<a href="(\S*)"\s+target="_blank">\s*(\S*)\s*</a>', a.prettify())
                if text:
                    (url, album) = text[0]

                    if url != "" and album != "":
                        '''
                        if url in test:
                            pass
                        else:
                            continue
                        '''
                        tv = self.albumClass(self)
                        if tv.albumName == "":
                            tv.albumName = album
                        tv.albumPageUrl = url
                        ret.append(tv)
                        self.command.SendCommand('album', self.name, tv.albumPageUrl)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
        return ret

    # 解析节目基本信息
    # http://tv.sohu.com/20120517/n343417005.shtml
    # album
    def CmdParserAlbum(self, js):
        # str: [('vid', '580058'), ('pid', '385367871'), ('playlistId', '1008605'), ('tag', '\xca\xae\xb6\xfe\xc5\xad\xba\xba\xa3\xa81957\xa3\xa9')]
        ret = []
        try:
            text = js['data']
            tv = self.GetAlbumByUrl(js['source'], False)
            if tv == None:
                return []

            t = re.findall('\(\'(vid|pid|playlistId|tag|PLAYLIST_ID)\',\s*\'(\S+?)\'\)', text)
            if t:
                for u in t:
                    if u[0] == 'pid':
                        tv.pid = u[1]
                    elif u[0] == 'vid':
                        tv.vid = u[1]
                    elif u[0] == 'playlistId' or u[0] == 'PLAYLIST_ID':
                        tv.playlist_id = u[1]
                    elif u[0] == 'tag' and tv.albumName == "":
                        tv.albumName = u[1]

                # 如果得不到 playlistId 的话
                if tv.playlist_id == "" and tv.vid != "":
                    url = 'http://search.vrs.sohu.com/mv_i%s.json' % tv.vid
                    if 'pid.json' in url:
                        print text
                    self.command.SendCommand("album_mvinfo", self.name, url)
    #            tv.UpdateCommand() # 更新节目信息
                ret.append(tv)

        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbum:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析节目指数信息
    # http://index.tv.sohu.com/index/switch-aid/1012657
    # album_score
    def CmdParserAlbumScore(self, js):
        ret = []
        try:
            text = js['data'] + '}'

            data = json.loads(text)
            if data.has_key('album'):
                album = data['album']
                if album:
                    pid = album['PId']
                    tv = self.GetAlbumById(pid)
                    if tv == None:
                        return ret
                    tv.albumName = album['albumName']

                    if data.has_key('album'):
                        index = data['index']
                        if index:
                            tv.dailyPlayNum = int(index['dailyPlayNum'])  # 每日播放次数
                            tv.dailyIndexScore = float(index['dailyIndexScore'])  # 每日指数
                    ret.append(tv)

            print "AlbumInfo: albumName=", tv.albumName, \
                        "dailyPlayNum=", tv.dailyPlayNum, \
                        "dailyIndexScore=", tv.dailyIndexScore
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumScore:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 从分页的页面上解析该页上的节目 （过时的）
    def CmdParserVideoList(self, js):
        ret = []
        try:
            text = js['data']
            soup = bs(text)
            playlist = soup.findAll('a')

            for tag in playlist:
                tv = self.albumClass(self)
                if self.engine.ParserAlbum(tag, tv):
    #                tv.UpdateCommand() # 更新节目信息
                    ret.append(tv)
                elif tv.albumPageUrl != "":
                    # 如果无法直接解析出节目信息，则进入详细页面解析, 重新解析
                    print "No Found:", tv.albumPageUrl
                    self.command.SendCommand('album', self.name, tv.albumPageUrl)

                # print ("title:%s" % tv.playlist_id, ": ", self.db.hgetall("title:%s" % tv.playlist_id)['title'])
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserVideoList:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
        return ret

# 电影
class SohuMovie(SohuVideoMenu):
    def __init__(self, name, engine, url):
        SohuVideoMenu.__init__(self, name, engine, url)
        self.HomeUrlList = [
            #'http://so.tv.sohu.com/list_p1100_p20_p3_p42013_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            #'http://so.tv.sohu.com/list_p1100_p20_p3_p42012_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            #'http://so.tv.sohu.com/list_p1100_p20_p3_p42011_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            #'http://so.tv.sohu.com/list_p1100_p20_p3_p42010_p5_p6_p73_p80_p9_2d0_p101_p11.html'
            #'http://so.tv.sohu.com/list_p1100_p20_p3_p411_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            #'http://so.tv.sohu.com/list_p1100_p20_p3_p490_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            #'http://so.tv.sohu.com/list_p1100_p20_p3_p480_p5_p6_p73_p80_p9_2d0_p101_p11.html',
            'http://so.tv.sohu.com/list_p1100_p20_p3_p41_p5_p6_p73_p80_p9_2d0_p103_p11.html'
        ]
        self.number = 100
        self.cid = 1
        self.homePage = 'http://tv.sohu.com/movieall/'
        self.filter = {
            '年份' : self.filter_year,
            '类型' : [
                {'爱情' : '100100'},
                {'战争' : '100101'},
                {'喜剧' : '100102'},
                {'科幻' : '100103'},
                {'恐怖' : '100104'},
                {'动画' : '100105'},
                {'动作' : '100106'},
                {'风月' : '100107'},
                {'剧情' : '100108'},
                {'歌舞' : '100109'},
                {'纪录' : '100110'},
                {'魔幻' : '100111'},
                {'灾难' : '100112'},
                {'悬疑' : '100113'},
                {'传记' : '100114'},
                {'警匪' : '100116'},
                {'伦理' : '100117'},
                {'惊悚' : '100118'},
                {'谍战' : '100119'},
                {'历史' : '100120'},
                {'武侠' : '100121'},
                {'青春' : '100122'},
                {'文艺' : '100123'}
            ],
            '产地' : [
                {'内地'  : '5'},
                {'香港'  : '27'},
                {'台湾'  : '28'},
                {'日本'  : '3'},
                {'韩国'  : '4'},
                # {'欧洲' : '2'},
                {'美国'  : '12'},
                {'英国'  : '17'},
                {'法国'  : '18'},
                {'德国'  : '19'},
                {'意大利': '20'},
                {'西班牙': '21'},
                {'俄罗斯': '24'},
                {'加拿大': '25'},
                {'印度'  : '22'},
                {'泰国'  : '23'},
                {'其他'  : ''}]
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 电视
class SohuTV(SohuVideoMenu):
    def __init__(self, name, engine, url):
        SohuVideoMenu.__init__(self, name, engine, url)
        self.number = 101
        self.cid = 2
        self.homePage = 'http://tv.sohu.com/tvall/'
        self.filter = {
            '年份' : self.filter_year,
            '类型' : [
                {'偶像'   : '101100'},
                {'家庭'   : '101101'},
                {'历史'   : '101102'},
                {'年代'   : '101103'},
                {'言情'   : '101104'},
                {'武侠'   : '101105'},
                {'古装'   : '101106'},
                {'都市'   : '101107'},
                {'农村'   : '101108'},
                {'军旅'   : '101109'},
                {'刑侦'   : '101110'},
                {'喜剧'   : '101111'},
                {'悬疑'   : '101112'},
                {'情景'   : '101113'},
                {'传记'   : '101114'},
                {'科幻'   : '101115'},
                {'动画'   : '101116'},
                {'动作'   : '101117'},
                {'真人秀' : '101118'},
                {'栏目'   : '101119'},
                {'谍战'   : '101120'},
                {'伦理'   : '101121'},
                {'战争'   : '101122'},
                {'神话'   : '101123'},
                {'惊悚'   : '101124'},
            ],
            '产地' : [
                {'内地' : '5'},
                {'港剧' : '6'},
                {'台剧' : '7'},
                {'美剧' : '9'},
                {'韩剧' : '8'},
                {'英剧' : '10'},
                {'泰剧' : '11'},
                {'日剧' : '15'},
                {'其他' : ''}
            ]
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 动漫
class SohuComic(SohuVideoMenu):
    def __init__(self, name, engine, url):
        SohuVideoMenu.__init__(self, name, engine, url)
        self.number = 115
        self.homePage = 'http://tv.sohu.com/comicall/'
        self.filter = {
            '年份' : self.filter_year,
            '篇幅' : [
                {'剧场版' : '1'},
                {'TV版'   : '2'},
                {'花絮'   : '3'},
                {'OVA'    : '5'},
                {'其他'   : '3'},
            ],
            '类型' : [
                {'历史'   : '115100'},
                {'搞笑'   : '115101'},
                {'战斗'   : '115102'},
                {'冒险'   : '115103'},
                {'魔幻'   : '115104'},
                {'励志'   : '115105'},
                {'益智'   : '115106'},
                {'童话'   : '115107'},
                {'体育'   : '115108'},
                {'神话'   : '115110'},
                {'青春'   : '115111'},
                {'悬疑'   : '115112'},
                {'真人'   : '115113'},
                {'亲子'   : '115114'},
                {'恋爱'   : '115118'},
                {'科幻'   : '115123'},
                {'治愈'   : '115124'},
                {'日常'   : '115125'},
                {'神魔'   : '115126'},
                {'百合'   : '115127'},
                {'耽美'   : '115128'},
                {'校园'   : '115129'},
                {'后宫'   : '115130'},
                {'美少女' : '115131'},
                {'竞技'   : '115132'},
                {'机战'   : '1151233'},
            ],
            '产地' : [
                {'大陆' : '1'},
                {'日本' : '2'},  # 7
                {'美国' : '3'},
                {'韩国' : '5'},
                {'香港' : '6'},
                {'欧洲' : ''},  # 英国8 加拿大 11 俄罗期 13
                {'其他' : ''},
            ],
            '年龄' : [
                {'5岁以下'   : '0'},
                {'5岁-12岁'  : '1'},
                {'13岁-18岁' : '2'},
                {'18岁以上'  : '3'},
            ]
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 综艺
class SohuShow(SohuVideoMenu):
    def __init__(self, name, engine, url):
        SohuVideoMenu.__init__(self, name, engine, url)
        self.number = 106
        self.homePage = ''
        self.filter = {
            '类型' : [
                {'访谈'     : '106100'},
                {'时尚'     : '106101'},
                {'游戏竞技' : '106102'},
                {'KTV'      : '106103'},
                {'交友'     : '106104'},
                {'选秀'     : '106105'},
                {'音乐'     : '106106'},
                {'曲艺'     : '106107'},
                {'养生'     : '106109'},
                {'脱口秀'   : '106110'},
                {'歌舞'     : '106111'},
                {'娱乐节目' : '106112'},
                {'真人秀'   : '106113'},
                {'其他'     : '106118'}
            ],
            '产地' : [
                {'内地' : '5'},
                {'港台' : '14'},
                {'欧美' : ''},  # 15?
                {'日韩' : '16'},
                {'其他' : ''},
            ]
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 记录片
class SohuDocumentary(SohuVideoMenu):
    def __init__(self, name, engine, url):
        SohuVideoMenu.__init__(self, name, engine, url)
        self.number = 107
        self.homePage = ''
        self.filter = {
            '类型': [
                  {'人物':'107100'},
                  {'历史':'107101'},
                  {'自然':'107102'},
                  {'军事':'107103'},
                  {'社会':'107104'},
                  {'幕后':'107105'},
                  {'财经':'107106'},
                  {'搜狐视频大视野':'107107'},
                  {'剧情':'107108'},
                  {'旅游':'107109'},
                  {'科技':'107110'},
                  {'文化':'107111'},
            ]
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 教育
class SohuEdu(SohuVideoMenu):
    def __init__(self, name, engine, url):
        SohuVideoMenu.__init__(self, name, engine, url)
        self.number = 119
        self.homePage = ''
        self.filter = {
            '类型': [
                {'公开课':'119100'},
                {'考试辅导':'119101'},
                {'职业培训':'119102'},
                {'外语学习':'119103'},
                {'幼儿教育':'119104'},
                {'乐活':'119105'},
                {'职场管理':'119106'},
                {'中小学教育':'119107'}
            ]
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 新闻
class SohuNew(SohuVideoMenu):
    def __init__(self, name, engine, url):
        SohuVideoMenu.__init__(self, name, engine, url)
        self.number = 122
        self.filter = {
            '类型':[
                {'国内':'122204'},
                {'国际':'122205'},
                {'军事':'122101'},
                {'科技':'122106'},
                {'财经':'122104'},
                {'社会':'122102'},
                {'生活':'122999'},
            ],
            '范围':[
                {'今天':'86400'},
                {'本周':'604800'},
                {'本月':'2592000'},
            ]
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 娱乐
class SohuYule(SohuVideoMenu):
    def __init__(self, name, engine, url):
        SohuVideoMenu.__init__(self, name, engine, url)
        self.number = 112
        self.filter = {
            '类型':[
                {'明星':'112103'},
                {'电影':'112100'},
                {'电视':'112101'},
                {'音乐':'112102'},
                {'戏剧':'112202'},
                {'动漫':'112201'},
                {'其他':'112203'},
            ],
            '范围':[
                {'今天':'86400'},
                {'本周':'604800'},
                {'本月':'2592000'},
            ]
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 旅游
class SohuTour(SohuVideoMenu):
    def __init__(self, name, engine, url):
        SohuVideoMenu.__init__(self, name, engine, url)
        self.number = 131
        self.filter = {
            '类型': [
                {'自驾游':'131100'},
                {'攻略':'131101'},
                {'交通住宿':'131102'},
                {'旅游资讯':'131103'},
                {'国内游':'131104'},
                {'境外游':'131105'},
                {'自然':'131106'},
                {'人文':'131107'},
                {'户外':'131108'},
                {'美食':'131109'},
                {'节庆活动':'131110'},
            ]
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# Sohu 搜索引擎
class SohuEngine(VideoEngine):
    def __init__(self):
        VideoEngine.__init__(self)

        self.engine_name = 'SohuEngine'
        self.base_url = 'http://so.tv.sohu.com'

        # 引擎主菜单
        self.menu = {
            '电影'   : SohuMovie,
            '电视剧' : SohuTV,
            '综艺'   : None,  # SohuShow,
            '娱乐'   : None,  # SohuYule,
            '动漫'   : None,  # SohuComic,
            '纪录片' : None,  # SohuDocumentary,
            '教育'   : None,  # SohuEdu,
            '旅游'   : None,  # SohuTour,
            '新闻'   : None,  # SohuNew
        }

        # 搜狐节目列表
        self.command.AddTemplate({
            'name'    : 'videoall',
            'source'  : 'http://tv.sohu.com/tvall',
            'menu'    : '电影',
            'dest'    : self.parser_host,
        })

        # 搜狐节目列表(过时的)
        self.command.AddTemplate({
            'name'    : 'videolist',
            'source'  : 'http://so.tv.sohu.com/list_p1100_p20_p3_p41_p5_p6_p73_p80_p9_2d0_p103_p11.html',
            'menu'    : '电影',
            'dest'    : self.parser_host,
            'regular' : [
                '(<a class="pic" target="_blank" title=".+/></a>)',
                '(<p class="tit tit-p">.+</a>)'
            ],
        })

        # 搜狐节目
        self.command.AddTemplate({
            'name'    : 'album',
            'source'  : 'http://tv.sohu.com/20110222/n279464056.shtml',
            'menu'    : '电影',
            'dest'    : self.parser_host,
            'regular' : [
                'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\s*(.+?);'
            ],
        })

        # 搜狐节目指数
        self.command.AddTemplate({
            'name'    : 'album_score',
            'source'  : 'http://index.tv.sohu.com/index/switch-aid/1012657',
            'menu'    : '电影',
            'dest'    : self.parser_host,
            'regular' : [
                '({"index":\S+?),"asudIncomes'
            ],
        })

        # 更新热门节目信息
        self.command.AddTemplate({
            'name'    : 'albumlist_hot',
            'source'  : 'http://so.tv.sohu.com/iapi?v=4&c=115&t=1&sc=115101_115104&o=3',
            'menu'    : '电影',
            'dest'    : self.parser_host,
        })

        # 更新节目的完整信息
        self.command.AddTemplate({
            'name'    : 'album_full',
            'source'  : 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5112241',
            'menu'    : '电影',
            'dest'    : self.parser_host,
        })

        # 更新节目的完整信息
        self.command.AddTemplate({
            'name'    : 'album_mvinfo',
            'source'  : 'http://search.vrs.sohu.com/mv_i1268037.json',
            'menu'    : '电影',
            'dest'    : self.parser_host,
        })

    def GetMenu(self, times=0):
        ret = {}
        playurl = 'http://tv.sohu.com'

        if times > MAX_TRY:
            return ret

        try:
            _, _, _, response = fetch(playurl)
            soup = bs(response)
            playlist = soup.findAll('dt')
            for a in playlist:
                urls = re.findall('(href|title)="(\S+)"', a.prettify())
                if len(urls) > 1:
                    menu_name = urls[1][1]
                    if (menu_name in self.menu):
                        u = urls[0][1]

                        if self.menu[menu_name]:
                            t = self.menu[menu_name](menu_name, self, u)
                            ret[menu_name.decode('utf-8')] = t
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine.GetMenu:  %s, %s,%s, %s' % (playurl, t, v, traceback.format_tb(tb)))
            return self.GetMenu(times + 1)

        return ret

    def GetHtmlList(self, playurl, times=0):
        ret = []
        count = 0
        if times > MAX_TRY:
            return ret
        try:
            print playurl
            _, _, _, response = fetch(playurl)

            soup = bs(response)
            data = soup.findAll('span', {'class' : 'c-red'})
            if data and len(data) > 1:
                count = int(data[1].contents[0])
                count = (count + 20 - 1) / 20
                if count > 200:
                    count = 200

            current_page = 0
            g = re.search('p10(\d+)', playurl)
            if g:
                current_page = int(g.group(1))

            for i in range(1, count + 1):
                if i != current_page:
                    link = re.compile('p10\d+')
                    newurl = re.sub(link, 'p10%d' % i, playurl)
                    print newurl
                    ret.append(newurl)
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine.GetHtmlList:  %s, %s,%s,%s' % (playurl, t, v, traceback.format_tb(tb)))
            return self.GetHtmlList(playurl, times + 1)

        return ret;

    def GetSoHuInfo(self, host, prot, tfile, new, times=0):
        if times > MAX_TRY:
            return
        try:
            url = 'http://%s/?prot=%s&file=%s&new=%s' % (host, prot, tfile, new)
            _, _, _, response = fetch(url)
            start, _, host, key, _, _, _, _ = response.split('|')
            return '%s%s?key=%s' % (start[:-1], new, key)
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine.GetSoHuInfo %s,%s,%s' % (t, v, traceback.format_tb(tb)))
            return self.GetSoHuInfo(host, prot, tfile, new, times + 1)

    def GetRealUrl(self, playurl, times=0):
        res = []
        if times > MAX_TRY:
            return res
        try:
            _, _, _, response = fetch(playurl)
            vid = re.search('vid="(\d+)', response).group(1)
            newurl = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
            # print newurl
            _, _, _, response = fetch(newurl)
            jdata = json.loads(response)
            host = jdata['allot']
            prot = jdata['prot']
            urls = []
            data = jdata['data']
            # title = data['tvName']
            # size = sum(data['clipsBytes'])
            for tfile, new in zip(data['clipsURL'], data['su']):
                urls.append(self.GetSoHuInfo(host, prot, tfile, new))
            if len(urls) == 1:
                url = urls[0]
                res.append(['', url])
            else:
                for url in urls:
                    res.append(['', url])
            return res
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine.GetRealUrl playurl:  %s, %s,%s,%s' % (playurl, t, v, traceback.format_tb(tb)))
            return self.GetRealUrl(playurl, times + 1)

    # 失效的，不再使用
    def UpdateHotList(self, menu, times=0):
        ret = []
        if times > MAX_TRY:
            return ret
        try:
            _, _, _, response = fetch(menu.url)
            soup = bs(response)

            playlist = soup.findAll('script')
            for a in playlist:
                urls = re.search('focslider', a.prettify())
                if urls:
                    data = re.findall('data: *([\s\S]*])', a.prettify()\
                                      .replace('http:', 'httx:')\
                                      .replace('p:', '"p":')\
                                      .replace('httx:', 'http:')\
                                      .replace('p1:', '"p1":')\
                                      .replace('l:', '"l":')\
                                      .replace('t:', '"t":')\
                                      .replace('\'', '"')\
                                      .replace('\n', '')\
                                      .replace('\t', '')\
                                      .replace(' ', '')\
                                      .replace('#', '0x')\
                                      .replace('bgcolor', '"bgcolor"'))
                    if data:
                        x = json.loads(data[0])
                        for a in x:
                            one = {}
                            one['large_image'] = a['p']
                            one['small_image'] = a['p1']
                            one['url'] = a['l']
                            one['title'] = a['t']
                            menu.HotList.append(one)
                            print a['t']

        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine.UpdateHotList playurl:  %s, %s,%s,%s' % (menu.url, t, v, traceback.format_tb(tb)))
            self.UpdateHotList(menu, times + 1)

    def ParserAlbum(self, tag, album):
        ret = False
        if tag == None or album == None:
            return False

        x = tag.findNext('a', {'class' : 'pic'})
        if x:
            # 取节目的 playlist_id, pid, vid
            urls = re.findall('(href|img src)="(\S+)"', x.prettify())
            for u in urls:
                if u[0] == 'href':
                    album.albumPageUrl = u[1]
                    try:
                        ids = re.search('(\d+)_(\d+)', u[1])
                        if ids:
                            album.pid = ids.group(1)
                            album.vid = ids.group(2)
                            ret = True
                    except:
                        t, v, tb = sys.exc_info()
                        log.error('SohuGetVideoList:  %s, %s,%s,%s' % (album.albumPageUrl, t, v, traceback.format_tb(tb)))
                elif u[0] == 'img src':
                    newid = re.findall('(vrsab_ver|vrsab)([0-9]+)', u[1])
                    if len(newid) > 0:
                        album.playlist_id = newid[0][1]
                        ret = True

            # 取节目的标题
            x = tag.findNext('p', {'class' : 'tit tit-p'}).contents[0]
            if x:
                album.albumName = x.contents[0]

        return ret

    # 获取节目的播放列表
    def GetAlbumPlayList(self, album, times=0):
        if times > MAX_TRY or album.albumPageUrl == '':
            return

        try:
            if album.playlist_id == '' :
                _, _, _, response = fetch(album.albumPageUrl)
                if response == None:
                    print 'error url: ', album.albumPageUrl
                    return

                pid = re.findall('(var PLAYLIST_ID|playlistId)\s*="(\d+)', response)
                if pid:
                    album.playlist_id = pid[0][1]
                else:
                    # 多部电视情况
                    return
            newurl = 'http://hot.vrs.sohu.com/vrs_videolist.action?playlist_id=%s' % album.playlist_id
            # print newurl
            _, _, _, response = fetch(newurl)
            oflvo = re.search('var vrsvideolist \= (\{.*.\})', response.decode('gb18030')).group(1)

            if not oflvo:
                return

            jdata = json.loads(oflvo.decode('utf-8'))
            album.videolist = jdata['videolist']

        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine.GetAlbumPlayList:  %s, %s,%s,%s' % (album.albumPageUrl, t, v, traceback.format_tb(tb)))
            self.GetAlbumPlayList(album, times + 1)

def test():
    url = 'http://tv.sohu.com/20130517/n376295917.shtml'
    url = 'http://tv.sohu.com/20110222/n279464056.shtml'
#    url = 'http://v.tv.sohu.com/20100618/n272893884.shtml'
#    url = 'http://tv.sohu.com/20101124/n277876671.shtml'
#    url = 'http://tv.sohu.com/s2010/72jzk/'
#    url = 'http://tv.sohu.com/s2011/7film/'
    _, _, _, response = fetch(url)
#    a = str(re.findall('var (playlistId|pid|vid|tag)\s*=\s*"(.+)";', response))
    a = re.findall('var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\s*"(.+?)";', response)
    print a
    return
    a = re.findall('(<p class="tit tit-p">.+</a>)', response)
    print a
    #print str(a)
    x = ""
    for i in a:
    #    print str(i)
        x += str(i)
    print x
    return
    url = 'http://search.vrs.sohu.com/mv_i101040.json'
    _, _, _, response = fetch(url)
    oflvo = re.search('var video_album_videos_result=(\{.*.\})', response).group(1)
    a = json.loads(oflvo)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return
    print re.findall('\(\'(vid|pid|playlistId|tag|PLAYLIST_ID)\',\s*\'(\S+?)\'\)', x)
    return

    url = 'http://tv.sohu.com/tvall'
    _, _, _, response = fetch(url)
    soup = bs(response)
    playlist = soup.findAll('li')
    for a in playlist:
        xx = re.findall('<a href="(\S*)"\s+target="_blank">\s*(\S*)\s*</a>', a.prettify())
        if xx:
            print xx[0][0], xx[0][1]

    return
    url = 'http://search.vrs.sohu.com/mv_i1268037,1268084,1268132.json'
    _, _, _, response = fetch(url)
    oflvo = re.search('var video_album_videos_result=(\{.*.\})', response).group(1)
    a = json.loads(oflvo)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return

    url = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5211206'
    url = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5497903'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return

    # url ='http://search.vrs.sohu.com/v?id=1268036&pageSize=200000&pageNum=1'
    url = 'http://search.vrs.sohu.com/v?id=1268037&pid=5497903&pageNum=1&pageSize=50&isgbk=true&var=video_similar_search_result'
    _, _, _, response = fetch(url)
    oflvo = re.search('var video_similar_search_result=(\{.*.\})', response).group(1)
    a = json.loads(oflvo)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return

    url = 'http://search.vrs.sohu.com/avs_i1268037_pr380470620_o2_n_p1000_chltv.sohu.com.json'
    _, _, _, response = fetch(url)
    oflvo = re.search('var video_album_videos_result=(\{.*.\})', response).group(1)
    a = json.loads(oflvo)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return

    url = 'http://so.tv.sohu.com/iapi?v=2&c=100'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return

    url = 'http://so.tv.sohu.com/iapi?v=4&c=101&t=1&area=%u5185%u5730&o=3&pagenum=1&pagesize=3'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return

    url = 'http://index.tv.sohu.com/index/switch-aid/1012657'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return

    x = str(re.findall('({"index":\S+?),"asudIncomes', response))
    print x
    return
    x = str(re.findall('({"index":{\S+?),"asudIncomes', response)[0]) + '}'
    print x
    a = json.loads(x)
    print json.dumps(a, ensure_ascii=False, indent=4)

    return
    print re.findall('("album":\S+?)}\,', response)
    return
    print re.findall('"PId":(\d+)\,', response)
    print re.findall('"albumName":"(.*?),', response)
    return

    x = re.findall('var (playlistId|pid|vid|tag)\s*=\s"(.+)";', response)
    x.extend(re.findall('h1 class="color3"><a href=.*>(.*)</a>', response))
    print str(x)
    return

    url = 'http://so.tv.sohu.com/list_p1101_p2_p3_p4_p5_p6_p7_p8_p9.html'
    _, _, _, response = fetch(url)
    x = re.findall('(<a class="pic" target="_blank" title=".+/></a>)', response)
    for a in x:
        print a
    x = re.findall('(<p class="tit tit-p">.+</a>)', response)
    for a in x:
        print a
    return
    x.extend(re.findall('<p class="tit tit-p">', response))
    print str(x)
    return

    _, _, _, response = fetch(url)
    url = 'http://tv.sohu.com/s2012/xxdyxmmw/'
    _, _, _, response = fetch(url)
    x = re.findall('var (playlistId|pid|vid)s*="(\d+)', response)
    x.extend(re.findall('h1 class="color3"><a href=.*>(.*)</a>', response))
    print str(x)

    return

    url = 'http://index.tv.sohu.com/index/switch-aid/5497903'
    url = 'http://index.tv.sohu.com/index/switch-aid/243'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return

    url = 'http://so.tv.sohu.com/iapi?v=4&c=101&t=1&area=%u5185%u5730&o=3&pagenum=1&pagesize=3'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return

    url = 'http://so.tv.sohu.com/jsl?c=100&cate=100100_100107&o=1&pageSize=1'
    _, _, _, response = fetch(url)
    a = json.loads(response)
    print json.dumps(a, ensure_ascii=False, indent=4)
    return


if __name__ == '__main__':
    test()
