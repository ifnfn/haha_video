#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time, sys, traceback
import tornado.escape

from .engines import VideoEngine, KolaParser, KolaAlias, EngineCommands, EngineVideoMenu
from kola import DB, autostr, autoint, autofloat, Singleton, utils
import kola


#================================= 以下是搜狐视频的搜索引擎 =======================================
global Debug
Debug = True

class LetvAlias(KolaAlias):
    def __init__(self):
        self.alias = {
            '中国大陆' : '内地',
            # 电影
            '剧情' : '剧情片',
            '喜剧' : '喜剧片',
            '动作' : '动作片',
            '恐怖' : '恐怖片',
            '动画' : '动画片',
            '警匪' : '警匪片',
            '武侠' : '武侠片',
            '战争' : '战争片',
            '短片' : '其他',
            '爱情' : '爱情片',
            '科幻' : '科幻片',
            '奇幻' : '魔幻片',
            '犯罪' : '警匪片',
            '冒险' : '其他',
            '灾难' : '灾难片',
            '伦理' : '伦理片',
            '传记' : '传记片',
            '家庭' : '家庭片',
            '纪录' : '纪录片',
            '惊悚' : '惊悚片',
            '历史' : '历史片',
            '悬疑' : '悬疑片',
            '歌舞' : '歌舞片',
            '体育' : '其他',

            # 电视剧
            #'剧情' : '剧情片',
            #'伦理' : '伦理片',
            #'喜剧' : '喜剧片',
            '军旅' : '军旅片',
            #'奇幻' : '科幻片',
            #'动作' : '动作片',
            #'战争' : '战争片',
            #'武侠' : '武侠片',
            #'犯罪' : '警匪片',
            #'悬疑' : '悬疑片',
            '偶像' : '偶像片',
            '都市' : '都市片',
            #'历史' : '历史片',
            #'灾难' : '灾难片',
            #'古装' : '古装片',
            #'科幻' : '科幻片',
            '情景' : '剧情片',
            '生活' : '其他',
            '情感' : '其他',
            #'家庭' : '家庭片',
            '谍战' : '谍战片',
            '刑侦' : '刑侦片',
            '经典' : '其他',
        }

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

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        if self.sohu.playlistid:
            ParserPlayCount(self).Execute()

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
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['name'] = album.albumName
            self.cmd['source'] = 'http://stat.letv.com/vplay/queryMmsTotalPCount?pid=%d&vid=%d' % ( album.letv.playlistid, album.letv.vid)

    def CmdParser(self, js):
        if not js['data']: return

        db = LetvDB()
        album = LetvAlbum()
        album_js = DB().FindAlbumJson(albumName=js['name'])
        if album_js:
                album.LoadFromJson(album_js)

        json = tornado.escape.json_decode(js['data'])
        json['plist_play_count']
        album.videoScore       = autofloat(json['plist_score']) * 10                  # 推荐指数
        album.dailyIndexScore  = autofloat(json['plist_score']) * 10  # 每日指数
        if 'plist_play_count' in json:
            album.dailyPlayNum     = autoint(json['dayCount'])       # 每日播放次数

        db.SaveAlbum(album)

# 节目列表
class ParserAlbumList(KolaParser):
    alias = LetvAlias()
    def __init__(self, url=None, cid=0):
        super().__init__()
        if url and cid:
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

            try:
                album.albumName = db.GetAlbumName(a['name'])
                if not album.albumName:
                    continue
                album.vid = utils.genAlbumId(album.albumName)
                album.cid = js['cid']

                album.enAlbumName      = ''  # 英文名称

                if 'subname' in a:         album.subName     = a['subname']
                if 'areaName' in a:        album.area        = self.alias.Get(a['areaName'])                      # 地区
                if 'subCategoryName' in a: album.categories  = self.alias.GetStrings(a['subCategoryName'], ',')   # 类型
                if 'releaseDate' in a:     album.publishYear = time.gmtime(autoint(a['releaseDate']) / 1000).tm_year

                if 'vids' in a:
                    vids = a['vids']
                    if vids:
                        vids = vids.split(',')
                        if not vids[0]:
                            pass
                        album.letv.vid = vids[0]
                        album.albumPageUrl = 'http://www.letv.com/ptv/vplay/%s.html' % autostr(vids[0])
                elif 'vid' in a:
                    album.letv.vid = a['vid']
                    album.albumPageUrl     = 'http://www.letv.com/ptv/vplay/%s.html' % autostr(a['vid'])

                if 'poster20' in a:    album.largePicUrl      = a['poster20']                # 大图 post20 最大的
                if 'postS3' in a:      album.smallPicUrl      = a['postS3']                  # 小图 // postS1 小中大的，postS3 小中最小的
                if 'poster12' in a:    album.largeHorPicUrl   = a['poster12']                # 横大图
                if 'poster11' in a:    album.smallHorPicUrl   = a['poster11']                # 横小图
                if 'poster20' in a:    album.largeVerPicUrl   = a['poster20']                # 竖大图
                if 'postS2' in a:      album.smallVerPicUrl   = a['postS2']                  # 竖小图
                if 'duration' in a:    album.playLength       = autoint(a['duration']) * 60  # 时长
                if 'mtime' in a:       album.updateTime       = TimeStr(a['mtime'])          # 更新时间
                if 'description' in a: album.albumDesc        = a['description']             # 简介

                if 'rating' in a:
                    album.videoScore       = autofloat(a['rating']) * 10                  # 推荐指数
                    album.dailyIndexScore  = autofloat(a['rating']) * 10  # 每日指数

                if 'episodes' in a:                     album.totalSet         = autoint(a['episodes'])       # 总集数
                if 'nowEpisodes' in a:                  album.updateSet        = autoint(a['nowEpisodes'])    # 当前更新集
                if 'dayCount' in a:                     album.dailyPlayNum     = autoint(a['dayCount'])       # 每日播放次数
                if 'weekCount' in a:                    album.weeklyPlayNum    = autoint(a['weekCount'])      # 每周播放次数
                if 'monthCount' in a:                   album.monthlyPlayNum   = autoint(a['monthCount'])     # 每月播放次数
                if 'playCount' in a:                    album.totalPlayNum     = autoint(a['playCount'])      # 总播放次数
                if 'starring' in a and a['starring']:
                    if type(a['starring']) == dict:
                        album.mainActors       = [x for _, x in a['starring'].items()]
                    elif type(a['starring']) == str:
                        album.mainActors       = a['starring'].split(',')     # 主演
                if 'directory' in a and a['directory']: album.directors        = a['directory'].split(',')    # 导演
                if 'aid' in a:                          album.letv.playlistid  = a['aid']

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

# 节目列表
class ParserShowList(KolaParser):
    alias = LetvAlias()
    def __init__(self, url=None, cid=0):
        super().__init__()
        if url and cid:
            self.cmd['source']  = url
            self.cmd['cid']     = cid

    def CmdParser(self, js):
        def TimeStr(t):
            return time.strftime('%Y-%m-%d', time.gmtime(autoint(t) / 1000))

        if not js['data']: return

        db = LetvDB()

        json = tornado.escape.json_decode(js['data'])
        for a in json['data_list']:
            albumName = db.GetAlbumName(a['name'])
            if not albumName:
                continue
            album = LetvAlbum()
            album_js = DB().FindAlbumJson(albumName=albumName)
            if album_js:
                    continue
            try:
                album.albumName = albumName
                album.vid = utils.genAlbumId(album.albumName)
                album.cid = js['cid']

                album.enAlbumName = ''  # 英文名称

                if 'images' in a:
                    images = a['images']

                    # 横大图
                    if   '970*300' in images: album.largeHorPicUrl = images['970*300']
                    elif '400*300' in images: album.largeHorPicUrl = images['400*300']
                    elif '220*145' in images: album.largeHorPicUrl = images['220*145']

                    # 横小图
                    if   '160*120' in images: album.smallHorPicUrl = images['160*120']
                    elif '130*80'  in images: album.smallHorPicUrl = images['130*80']
                    elif '120*90'  in images: album.smallHorPicUrl = images['120*90']
                    elif '132*99'  in images: album.smallHorPicUrl = images['132*99']
                    elif '128*96'  in images: album.smallHorPicUrl = images['128*96']

                    # 竖小图
                    if   '150*200' in images: album.smallVerPicUrl = images['150*200']
                    elif '96*128'  in images: album.smallVerPicUrl = images['96*128']
                    elif '90*120'  in images: album.smallVerPicUrl = images['90*120']

                    # 竖大图
                    if   '600*800' in images: album.largeVerPicUrl = images['600*800']
                    elif '300*400' in images: album.largeVerPicUrl = images['300*400']

                    album.largePicUrl      = album.largeVerPicUrl
                    album.smallPicUrl      = album.smallVerPicUrl

                if 'subname' in a:         album.subName        = a['subname']
                if 'areaName' in a:        album.area           = self.alias.Get(a['areaName'])                      # 地区
                if 'subCategoryName' in a: album.categories     = self.alias.GetStrings(a['subCategoryName'], ',')   # 类型
                if 'releaseDate' in a:     album.publishYear    = time.gmtime(autoint(a['releaseDate']) / 1000).tm_year
                if 'mtime' in a:           album.updateTime     = TimeStr(a['mtime'])      # 更新时间
                if 'description' in a:     album.albumDesc      = a['description']         # 简介
                if 'dayCount' in a:        album.dailyPlayNum   = autoint(a['dayCount'])   # 每日播放次数
                if 'weekCount' in a:       album.weeklyPlayNum  = autoint(a['weekCount'])  # 每周播放次数
                if 'monthCount' in a:      album.monthlyPlayNum = autoint(a['monthCount']) # 每月播放次数
                if 'playCount' in a:       album.totalPlayNum   = autoint(a['playCount'])  # 总播放次数
                if 'rating' in a:
                    album.videoScore       = autofloat(a['rating']) * 10                  # 推荐指数
                    album.dailyIndexScore  = autofloat(a['rating']) * 10  # 每日指数

                if 'vids' in a:
                    vids = a['vids']
                    if vids:
                        vids = vids.split(',')
                        if not vids[0]:
                            pass
                        album.letv.vid = vids[0]
                        album.albumPageUrl = 'http://www.letv.com/ptv/vplay/%s.html' % autostr(vids[0])
                elif 'vid' in a:
                    album.letv.vid = a['vid']
                    album.albumPageUrl     = 'http://www.letv.com/ptv/vplay/%s.html' % autostr(a['vid'])

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
                ParserShowList(newurl, js['cid']).Execute()


class LetvVideoMenu(EngineVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.albumClass = LetvAlbum
        self.DBClass = LetvDB

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            ParserAlbumList(url, self.cid).Execute()

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

# 动漫
class LetvComic(LetvVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 3
        self.HomeUrlList = ['http://list.letv.com/apin/chandata.json?c=5&d=1&md=&o=20&p=1&s=1']

# 记录片
class LetvDocumentary(LetvVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 4
        self.HomeUrlList = ['http://list.letv.com/api/chandata.json?c=16&d=2&md=&o=1&p=1&t=119']

# 综艺
class LetvShow(LetvVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 5
        self.HomeUrlList = ['http://list.letv.com/apin/chandata.json?c=11&d=1&md=&o=20&p=1&s=3']

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            ParserShowList(url, self.cid).Execute()

# Letv 搜索引擎
class LetvEngine(VideoEngine):
    def __init__(self):
        super().__init__()

        self.engine_name = 'LetvEngine'
        self.albumClass = LetvAlbum

        # 引擎主菜单
        self.menu = [
            LetvMovie('电影'),
            LetvTV('电视剧'),
            LetvComic('动漫'),
            LetvDocumentary('记录片'),
            LetvShow('综艺')
        ]

        self.parserList = [
            ParserAlbumList(),
            ParserShowList(),
            ParserPlayCount(),
        ]
