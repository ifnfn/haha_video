#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import sys
import time
import traceback

import tornado.escape

from kola import DB, autostr, autoint, autofloat, Singleton, utils
import kola

from .engines import VideoEngine, KolaParser, KolaAlias, EngineVideoMenu


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
            '冒险' : '冒险片',
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

        self.letv = LetvPrivate()

    def SaveToJson(self):
        if self.letv:
            self.private[self.engineName] = self.letv.Json()
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if self.engineName in self.private:
            self.letv.Load(self.private[self.engineName])

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        pass
        #if self.letv.playlistid:
        #    ParserPlayCount(self).Execute()

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

    def GetMenuAlbumList(self, cid,All=False):
        fields = {'engineList' : True,
                  'albumName': True,
                  'private'  : True,
                  'cid'      : True,
                  'vid'      : True}

        data = self.album_table.find({'engineList' : {'$in' : ['LetvEngine']}, 'cid' : cid}, fields)

        albumList = []
        for p in data:
            album = LetvAlbum()
            album.LoadFromJson(p)
            albumList.append(album)

        return albumList

    # 从数据库中找到album
    def GetAlbumFormDB(self, playlistid='', albumName='', auto=False):
        album = None
        json = self.FindAlbumJson(playlistid, albumName)
        if json:
            album = LetvAlbum()
            album.LoadFromJson(json)
        elif auto:
            album = LetvAlbum()
            if playlistid:
                album.letv.playlistid = playlistid
            if albumName:
                album.SetNameAndVid(albumName)

        return album

    def SaveAlbum(self, album, upsert=True):
        if album.albumName and album.letv.playlistid:
            self._save_update_append(None, album, key={'private.LetvEngine.playlistid' : album.letv.playlistid}, upsert=upsert)

class ParserPlayCount(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['name'] = album.albumName
            self.cmd['source'] = 'http://stat.letv.com/vplay/queryMmsTotalPCount?pid=%s&vid=%s' % ( album.letv.playlistid, album.letv.vid)

    def CmdParser(self, js):
        if not js['data']: return

        db = LetvDB()
        album = db.GetAlbumFormDB(albumName=js['name'])
        if album == None:
            return

        json = tornado.escape.json_decode(js['data'])
        if 'plist_score' in json:
            album.Score       = autofloat(json['plist_score'])  # 推荐指数
        if 'plist_play_count' in json:
            play_count = autoint(json['plist_play_count'])      # 每日播放次数
            if play_count > album.dailyPlayNum:
                album.totalPlayNum = play_count
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
        def Time(t):
            return int(autoint(t) / 1000)
            return time.strftime('%Y-%m-%d', time.gmtime(autoint(t) / 1000))

        if not js['data']: return

        db = LetvDB()

        json = tornado.escape.json_decode(js['data'])
        for a in json['data_list']:
            try:
                album = db.GetAlbumFormDB(albumName=a['name'], auto=True)
                if not album:
                    continue

                album.cid = js['cid']

                album.enAlbumName      = ''  # 英文名称

                if 'subname' in a:         album.subName     = a['subname']
                if 'areaName' in a:        album.area        = self.alias.Get(a['areaName'])                      # 地区
                if 'subCategoryName' in a: album.categories  = self.alias.GetStrings(a['subCategoryName'], ',')   # 类型

                if 'vids' in a:
                    vids = a['vids']
                    if vids:
                        vids = vids.split(',')
                        if not vids[0]:
                            pass
                        album.letv.vid = vids[0]
                elif 'vid' in a:
                    album.letv.vid = a['vid']
                    #album.albumPageUrl     = 'http://www.letv.com/ptv/vplay/%s.html' % autostr(a['vid'])

                if 'poster20' in a:    album.largePicUrl      = a['poster20']                # 大图 post20 最大的
                if 'postS3' in a:      album.smallPicUrl      = a['postS3']                  # 小图 // postS1 小中大的，postS3 小中最小的
                if 'poster12' in a:    album.largeHorPicUrl   = a['poster12']                # 横大图
                if 'poster11' in a:    album.smallHorPicUrl   = a['poster11']                # 横小图
                if 'poster20' in a:    album.largeVerPicUrl   = a['poster20']                # 竖大图
                if 'postS2' in a:      album.smallVerPicUrl   = a['postS2']                  # 竖小图
                if 'duration' in a:    album.playLength       = autoint(a['duration']) * 60  # 时长
                if 'mtime' in a:       album.updateTime       = Time(a['mtime'])             # 更新时间
                if 'releaseDate' in a: album.publishYear      = time.gmtime(autoint(a['releaseDate']) / 1000).tm_year
                if 'ctime' in a:       album.publishTime      = Time(a['ctime'])         # 更新时间
                if 'description' in a: album.albumDesc        = a['description']             # 简介
                if 'rating' in a:      album.Score            = autofloat(a['rating'])       # 推荐指数
                if 'episodes' in a:    album.totalSet         = autoint(a['episodes'])       # 总集数
                if 'nowEpisodes' in a: album.updateSet        = autoint(a['nowEpisodes'])    # 当前更新集
                if 'dayCount' in a:    album.dailyPlayNum     = autoint(a['dayCount'])       # 每日播放次数
                if 'weekCount' in a:   album.weeklyPlayNum    = autoint(a['weekCount'])      # 每周播放次数
                if 'monthCount' in a:  album.monthlyPlayNum   = autoint(a['monthCount'])     # 每月播放次数
                if 'playCount' in a:   album.totalPlayNum     = autoint(a['playCount'])      # 总播放次数
                if 'aid' in a:         album.letv.playlistid  = a['aid']
                if 'directory' in a and a['directory']: album.directors        = a['directory'].split(',')    # 导演

                if 'starring' in a and a['starring']:
                    if type(a['starring']) == dict:
                        album.mainActors       = [x for _, x in a['starring'].items()]
                    elif type(a['starring']) == str:
                        album.mainActors       = a['starring'].split(',')     # 主演

                album.letv.videoListUrl = utils.GetScript('letv', 'get_videolist', [album.letv.playlistid, album.letv.vid])

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
        def Time(t):
            return int(autoint(t) / 1000)
            return time.strftime('%Y-%m-%d', time.gmtime(autoint(t) / 1000))

        if not js['data']: return

        db = LetvDB()

        json = tornado.escape.json_decode(js['data'])
        for a in json['data_list']:
            try:
                album = db.GetAlbumFormDB(albumName=a['name'], auto=True)
                if not album:
                    continue

                album.cid = js['cid']

                album.enAlbumName = ''  # 英文名称

                if 'images' in a:
                    images = a['images']

                    # 横大图
                    if   '400*300' in images: album.largeHorPicUrl = images['400*300']
                    elif '220*145' in images: album.largeHorPicUrl = images['220*145']
                    elif '970*300' in images: album.largeHorPicUrl = images['970*300'] # 不要太大啦！

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
                    if   '300*400' in images: album.largeVerPicUrl = images['300*400']
                    elif '600*800' in images: album.largeVerPicUrl = images['600*800'] # 不要太大啦！
                    elif '150*200' in images: album.smallVerPicUrl = images['150*200']

                    album.largePicUrl      = album.largeVerPicUrl
                    album.smallPicUrl      = album.smallVerPicUrl

                if 'subname' in a:         album.subName        = a['subname']
                if 'areaName' in a:        album.area           = self.alias.Get(a['areaName'])                      # 地区
                if 'subCategoryName' in a: album.categories     = self.alias.GetStrings(a['subCategoryName'], ',')   # 类型

                #tm = time.gmtime(autoint(a['releaseDate']) / 1000)
                #print(tm)
                if 'releaseDate' in a:     album.publishYear    = time.gmtime(Time(a['releaseDate'])).tm_year
                if 'mtime' in a:           album.updateTime     = Time(a['mtime'])         # 更新时间
                if 'ctime' in a:           album.publishTime    = Time(a['ctime'])         # 更新时间
                if not album.publishTime:
                    album.publishTime = Time(a['releaseDate'])

                if 'description' in a:     album.albumDesc      = a['description']         # 简介
                if 'dayCount' in a:        album.dailyPlayNum   = autoint(a['dayCount'])   # 每日播放次数
                if 'weekCount' in a:       album.weeklyPlayNum  = autoint(a['weekCount'])  # 每周播放次数
                if 'monthCount' in a:      album.monthlyPlayNum = autoint(a['monthCount']) # 每月播放次数
                if 'playCount' in a:       album.totalPlayNum   = autoint(a['playCount'])  # 总播放次数
                if 'rating' in a:          album.Score          = autofloat(a['rating'])   # 推荐指数

                if 'vids' in a:
                    vids = a['vids']
                    if vids:
                        vids = vids.split(',')
                        if not vids[0]:
                            pass
                        album.letv.vid = vids[0]
                elif 'vid' in a:
                    album.letv.vid = a['vid']

                if 'aid' in a:
                    album.letv.playlistid = a['aid']

                album.letv.videoListUrl = utils.GetScript('letv', 'get_videolist', [album.letv.playlistid, album.letv.vid])

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

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            ParserShowList(url, self.cid).Execute()

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
