#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import sys
import time
import traceback

import tornado.escape

import kola

from .engines import VideoEngine, KolaParser, KolaAlias, EngineVideoMenu


global Debug
Debug = True

class PPtvAlias(KolaAlias):
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
            '音乐' : '音乐片',
            '记录' : '记录片',
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

alias = PPtvAlias()

class PPtvPrivate:
    def __init__(self):
        self.name =  'PPTV'
        self.channel_id = ''
        self.videoListUrl = {}

    def Json(self):
        json = {'name' : self.name}
        if self.channel_id   : json['channel_id'] = self.channel_id
        if self.videoListUrl : json['videoListUrl'] = self.videoListUrl

        return json

    def Load(self, js):
        if 'name' in js         : self.name         = js['name']
        if 'channel_id' in js   : self.channel_id   = js['channel_id']
        if 'videoListUrl' in js : self.videoListUrl = js['videoListUrl']

class PPtvAlbum(kola.AlbumBase):
    def __init__(self):
        self.engineName = 'PPtvEngine'
        super().__init__()

        self.pptv = PPtvPrivate()

    def SaveToJson(self):
        if self.pptv:
            self.private[self.engineName] = self.pptv.Json()
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if self.engineName in self.private:
            self.pptv.Load(self.private[self.engineName])

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        if self.pptv.channel_id:
            ParserPlayCount(self).Execute()

class PPtvDB(kola.DB, kola.Singleton):
    def __init__(self):
        super().__init__()
        self.albumNameAlias = {}   # 别名
        self.blackAlbumName = {}   # 黑名单

    # 从数据库中找到 album
    def FindAlbumJson(self, channel_id='', albumName=''):
        channel_id = kola.autostr(channel_id)
        if channel_id == '' and albumName == '':
            return None

        f = []
        if albumName  : f.append({'albumName'                     : albumName})
        if channel_id : f.append({'private.PPtvEngine.channel_id' : channel_id})

        return self.album_table.find_one({'engineList' : {'$in' : ['PPtvEngine']}, '$or' : f})

    def GetMenuAlbumList(self, cid, All=False):
        fields = {'engineList' : True,
                  'albumName': True,
                  'private'  : True,
                  'cid'      : True,
                  'vid'      : True}

        data = self.album_table.find({'engineList' : {'$in' : ['PPtvEngine']}, 'cid' : cid}, fields)

        albumList = []
        for p in data:
            album = PPtvAlbum()
            album.LoadFromJson(p)
            albumList.append(album)

        return albumList

    # 从数据库中找到album
    def GetAlbumFormDB(self, channel_id='', albumName='', auto=False):
        album = None
        json = self.FindAlbumJson(channel_id, albumName)
        if json:
            album = PPtvAlbum()
            album.LoadFromJson(json)
        elif auto:
            album = PPtvAlbum()
            if channel_id:
                album.pptv.channel_id = channel_id
            if albumName:
                album.SetNameAndVid(albumName)

        return album

    def SaveAlbum(self, album, upsert=True):
        if album.albumName and album.pptv.channel_id:
            self._save_update_append(None, album, key={'private.PPtvEngine.channel_id' : album.pptv.channel_id}, upsert=upsert)

class ParserPlayCount(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['name']       = album.albumName
            self.cmd['source']     = 'http://sns.video.pptv.com/tvideo/fcgi-bin/batchgetplaymount?id=%s&otype=json' % album.pptv.channel_id
            self.cmd['channel_id'] = album.pptv.channel_id
            self.cmd['cache']      = False

    def CmdParser(self, js):
        text = re.findall('QZOutputJson=({[\s\S]*});', js['data'])
        if not text:
            return

        json = tornado.escape.json_decode(text[0])
        if json['msg'] != 'success':
            return

        db = PPtvDB()
        album = db.GetAlbumFormDB(channel_id=js['channel_id'])
        if album == None:
            return

        for v in json['node']:
            if v['id'] == js['channel_id']:
                if 'all' in v: album.totalPlayNum = v['all']
                if 'yest' in v: album.dailyPlayNum = v['yest']
                db.SaveAlbum(album)

# 节目列表
class ParserAlbumList(KolaParser):
    def __init__(self, url=None, cid=None):
        super().__init__()
        if url and cid:
            self.cmd['source']    = url
            self.cmd['cid']       = cid

    def CmdParser(self, js):
        def Time(t):
            return int(kola.autoint(t) / 1000)
            return time.strftime('%Y-%m-%d', time.gmtime(kola.autoint(t) / 1000))

        json = tornado.escape.json_decode(js['data'])
        if (json['err'] != 0) or ('data' not in json) or ('channel_list' not in json['data']):
            return

        db = PPtvDB()
        for a in json['data']['channel_list']:
            if 'basic' not in a:
                continue

            basic = a['basic']

            if basic['isPay'] != '0':
                continue


            try:
                album = db.GetAlbumFormDB(albumName=basic['title'], auto=True)
                if not album:
                    return

                album.cid = js['cid']

                if 'basic' in a:
                    basic = a['basic']
                    if 'durationSeconds' in basic:
                        album.playLength = basic['durationSeconds']
                    if 'views_week' in basic:
                        album.dailyPlayNum = basic['views_week'] / 7
                        album.weeklyPlayNum = basic['views_week']
                    if 'views_total' in basic:
                        album.totalPlayNum = basic['views_total']

                if 'dynamic' in a:
                    if 'score' in a['dynamic']:
                        album.Score = a['dynamic']['score']

                if 'info' in a:
                    info = a['info']
                    if 'actors' in info:
                        album.mainActors = []
                        for actor in info['actors']:
                            album.mainActors.append(actor['name'])
                    if 'directors' in info:
                        album.directors = []
                        for actor in info['directors']:
                            album.directors.append(actor['name'])
                    if 'areas' in info:
                        album.area = info['areas']
                    if 'extendDescription' in info:
                        album.albumDesc = info['extendDescription']

                if 'img_url' in a:
                    album.largePicUrl      = a['img_url']                     # 大图
                    album.smallPicUrl      = a['img_url']                     # 小图
                    album.largeHorPicUrl   = a['img_url']                     # 横大图
                    album.smallHorPicUrl   = a['img_url']                     # 横小图
                    album.largeVerPicUrl   = a['img_url']                     # 竖大图
                    album.smallVerPicUrl   = a['img_url']                     # 竖小图
                '''
                if 'rating' in a:      album.Score            = kola.autofloat(a['rating'])                       # 推荐指数
                if 'subCategoryName' in a: album.categories  = self.alias.GetStrings(a['subCategoryName'], ',')   # 类型
                if 'mtime' in a:       album.updateTime       = Time(a['mtime'])                                  # 更新时间
                if 'releaseDate' in a: album.publishYear      = time.gmtime(kola.autoint(a['releaseDate']) / 1000).tm_year
                if 'ctime' in a:       album.publishTime      = Time(a['ctime'])                                  # 更新时间
                if 'episodes' in a:    album.totalSet         = kola.autoint(a['episodes'])       # 总集数
                if 'nowEpisodes' in a: album.updateSet        = kola.autoint(a['nowEpisodes'])    # 当前更新集
                '''

                if 'channel_id' in a:
                    album.pptv.channel_id = a['channel_id']

                album.pptv.videoListUrl = kola.GetScript('pptv', 'get_videolist', [album.cid, album.pptv.channel_id])

                db.SaveAlbum(album)
            except:
                t, v, tb = sys.exc_info()
                print("ProcessCommand playurl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))

class PPtvVideoMenu(EngineVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.albumClass = PPtvAlbum
        self.DBClass = PPtvDB

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            ParserAlbumList(url, self.cid).Execute()

# 电影
class PPtvMovie(PPtvVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 1
        self.HomeUrlList = ['http://list.pptv.com/api/1------1---1.json?action=getListChannel&filter=channel_list']

# 电视
class PPtvTV(PPtvVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 2
        self.HomeUrlList = []

# 动漫
class PPtvComic(PPtvVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 3
        self.HomeUrlList = []

# 记录片
class PPtvDocumentary(PPtvVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 4
        self.HomeUrlList = []

# 综艺
class PPtvShow(PPtvVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 5
        self.HomeUrlList = []

# PPtv 搜索引擎
class PPtvEngine(VideoEngine):
    def __init__(self):
        super().__init__()

        self.engine_name = 'PPtvEngine'
        self.albumClass = PPtvAlbum

        # 引擎主菜单
        self.menu = [
            PPtvMovie('电影'),
            #PPtvTV('电视剧'),
            #PPtvComic('动漫'),
            #PPtvDocumentary('记录片'),
            #PPtvShow('综艺')
        ]

        self.parserList = [
            ParserAlbumList(),
            ParserPlayCount(),
        ]
