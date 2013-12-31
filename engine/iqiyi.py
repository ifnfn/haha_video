#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time, sys, traceback
import tornado.escape
from bs4 import BeautifulSoup as bs
from xml.etree import ElementTree

from engine import VideoEngine, KolaParser
from kola import DB, autostr, autoint, Singleton, utils
import kola


#================================= 以下是搜狐视频的搜索引擎 =======================================
global Debug
Debug = True

class QiyiVideo(kola.VideoBase):
    def SaveToJson(self):
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)

    def SetVideoScript(self, name, vid, func_name='kola_main'):
        url = {
            'script'     : 'qiyi',
            'parameters' : [autostr(vid), autostr(self.cid)]
        }
        if func_name and func_name != 'kola_main':
                url['function'] = func_name

        self.SetVideoUrl(name, url)

class QiyiPrivate:
    def __init__(self):
        self.name =  '爱奇艺'
        self.vid = ''
        self.albumid = ''
        self.tvid = ''
        self.videoListUrl = {}

    def Json(self):
        json = {'name' : self.name}
        if self.vid          : json['vid']          = self.vid
        if self.albumid      : json['albumid']      = self.albumid
        if self.tvid         : json['tvid']         = self.tvid
        if self.videoListUrl : json['videoListUrl'] = self.videoListUrl

        return json

    def Load(self, js):
        if 'name' in js         : self.name         = js['name']
        if 'vid' in js          : self.vid          = js['vid']
        if 'albumid' in js      : self.albumid      = js['albumid']
        if 'tvid' in js         : self.tvid         = js['tvid']
        if 'videoListUrl' in js : self.videoListUrl = js['videoListUrl']

class QiyiAlbum(kola.AlbumBase):
    def __init__(self):
        self.engineName = 'QiyiEngine'
        super().__init__()
        self.albumPageUrl = ''

        self.qiyi = QiyiPrivate()

        self.videoClass = QiyiVideo

    def SaveToJson(self):
        if self.qiyi:
            self.private[self.engineName] = self.qiyi.Json()
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if self.engineName in self.private:
            self.qiyi.Load(self.private[self.engineName])

    def UpdateFullInfoCommand(self):
        pass

class QiyiDB(DB, Singleton):
    def __init__(self):
        super().__init__()
        self.albumNameAlias = {}   # 别名
        self.blackAlbumName = {}   # 黑名单


    # 从数据库中找到 album
    def FindAlbumJson(self, tvid='', albumName=''):
        tvid = autostr(tvid)
        if tvid == '' and albumName == '':
            return None

        f = []
        if albumName : f.append({'albumName'               : albumName})
        if tvid      : f.append({'private.QiyiEngine.tvid' : tvid})

        #return self.album_table.find_one({'$or' : f})
        return self.album_table.find_one({'engineList' : {'$in' : ['QiyiEngine']}, '$or' : f})

    # 从数据库中找到album
    def GetAlbumFormDB(self, tvid='', albumName='', auto=False):
        album = None
        json = self.FindAlbumJson(tvid, albumName)
        if json:
            album = QiyiAlbum()
            album.LoadFromJson(json)
        elif auto:
            album = QiyiAlbum()
            if tvid   : album.qiyi.tvid = tvid
            if albumName    : album.mName = albumName

        return album

    def SaveAlbum(self, album, upsert=True):
        if album.albumName and album.qiyi.vid:
            self._save_update_append(None, album, key={'private.QiyiEngine.vid' : album.qiyi.tvid}, upsert=upsert)

class ParserAlbumXml(KolaParser):
    def __init__(self, url=None):
        super().__init__()
        if url:
            self.cmd['source'] = url

    def CmdParser(self, js):
        def GetKey(node, key):
            tmp = node.find(key)
            if tmp:
                return tmp.text
            else:
                return ''

        db = QiyiDB()
        root = ElementTree.fromstring(js['data'])
        video = root.find('video')

        albumName = db.GetAlbumName(GetKey(video, 'albumName'))
        if not albumName:
            return

        album = QiyiAlbum()
        album_js = DB().FindAlbumJson(albumName=albumName)
        if album_js:
                album.LoadFromJson(album_js)

        album.albumName       = albumName
        album.vid             = utils.genAlbumId(album.albumName)
        album.area            = GetKey(video, 'area')
        album.mainActors      = GetKey(video, 'mainActor').strip(' ')
        album.directors       = GetKey(video, 'directors').strip(' ')
        album.playLength      = GetKey(video, 'totalDuration')
        album.qiyi.vid        = GetKey(video, 'vid')

        db.SaveAlbum(album, upsert=True)

class ParserAlbumJsonAVList(KolaParser):
    def __init__(self, albumid=None, tvid=None, albumUrl=None):
        super().__init__()
        if albumid and tvid and albumUrl:
            self.cmd['source']  = 'http://cache.video.qiyi.com/avlist/%s/' % albumid
            self.cmd['albumid'] = albumid
            self.cmd['tvid'] = tvid
            self.cmd['aurl'] = albumUrl

    def CmdParser(self, js):
        text = re.findall('videoListC=([\s\S]*)', js['data'])
        if text:
            text = text[0]
        json = tornado.escape.json_decode(text)
        if json['code'] != 'A00000':
            ParserAlbumPage(js['aurl']).Execute()
            return

        #album = js['albumid']
        tvid = js['tvid']
        videoid = ''

        for v in json['data']['vlist']:
            videoid = v['vid']
            break

        if videoid and tvid:
            ParserAlbumJson(tvid, videoid).Execute()
            #ParserAlbumXml('http://cache.video.qiyi.com/v/%s' % videoid).Execute()


class ParserAlbumJsonA(KolaParser):
    def __init__(self, albumid=None, tvid=None, videoid=None, ar=None, tg=None):
        super().__init__()
        if albumid and tvid and videoid:
            self.cmd['source']  = 'http://cache.video.qiyi.com/a/%s' % albumid
            self.cmd['tvid']    = tvid
            self.cmd['videoid'] = videoid
            self.cmd['albumid'] = albumid
            self.cmd['ar']      = ar
            self.cmd['tg']      = tg

    def CmdParser(self, js):
        def TimeStr(t):
            return time.strftime('%Y-%m-%d', time.gmtime(autoint(t) / 1000))

        try:
            db = QiyiDB()

            text = re.findall('AlbumInfo=([\s\S]*)', js['data'])
            if text:
                text = text[0]
            json = tornado.escape.json_decode(text)
            if json['code'] != 'A00000':
                return

            json = json['data']
            albumName = db.GetAlbumName(json['tvName'])
            if not albumName:
                return

            album = QiyiAlbum()
            album_js = DB().FindAlbumJson(albumName=albumName)
            if album_js:
                    album.LoadFromJson(album_js)

            album.albumName = albumName
            album.vid = utils.genAlbumId(album.albumName)
            album.cid = json['albumType']

            album.area             = js['ar']                                  # 地区
            album.categories       = js['tg'].split(' ')                       # 类型

            album.publishYear      = autoint(json['tvYear']) // 10000          # 年

            album.albumPageUrl     = json['purl']                              # 'vu'
            album.largePicUrl      = json['tvPictureUrl']                      # 大图 post20 最大的

            if 'episodeCounts' in json:
                album.totalSet = autoint(json['episodeCounts'])                # 总集数
            #if 'currentMaxEpisode' in json:
            #   album.updateSet = autoint(json['currentMaxEpisode'])           # 当前更新集

            if 'tvDesc' in json:     album.albumDesc      = json['tvDesc']     # 简介
            if 'mainActors' in json: album.mainActors     = json['mainActors'] # 主演
            if 'actors' in json:     album.directors      = json['actors']     # 导演

            album.totalPlayNum     = autoint(json['playCounts'])               # 总播放次数
            album.updateTime       = TimeStr(json['pubTime'])                  # 更新时间

            album.qiyi.vid     = js['videoid']
            album.qiyi.albumid = js['albumid']
            album.qiyi.tvid    = js['tvid']


            album.qiyi.videoListUrl = {
                'script'     : 'qiyi',
                'function'   : 'get_videolist',
                'parameters' : [album.qiyi.albumid, album.qiyi.vid, album.qiyi.tvid, album.cid, album.albumName]
            }

            db.SaveAlbum(album)
        except:
            t, v, tb = sys.exc_info()
            print("ProcessCommand playurl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))

# 补充地区与类型
class ParserAlbumJson(KolaParser):
    def __init__(self, tvid=None, videoid=None):
        super().__init__()
        if tvid and videoid:
            self.cmd['source'] = 'http://cache.video.qiyi.com/vi/%s/%s/' % (tvid, videoid)

    def CmdParser(self, js):
        json = tornado.escape.json_decode(js['data'])
        ar = json['ar']
        tg = json['tg']
        aid = json['aid']
        vid = json['vid']
        tvid = json['tvid']

        ParserAlbumJsonA(aid, tvid, vid, ar, tg).Execute()

class ParserAlbumPage(KolaParser):
    def __init__(self, url=None):
        super().__init__()
        if url:
            self.cmd['source']  = url
            self.cmd['regular'] = ['(data-player-videoid.*|data-player-tvid.*|data-player-albumid)']

    def CmdParser(self, js):
        if not js['data']: return

        vlist = re.findall('(videoid|tvid|albumid)="(.*)"', js['data'])
        for u in vlist:
            if u[0] == 'videoid':
                videoid = u[1]
            elif u[0] == 'tvid':
                tvid = u[1]
#            elif u[0] == 'albumid':
#                albumid = u[1]
        if videoid and tvid:
            ParserAlbumJson(tvid, videoid).Execute()
            #ParserAlbumXml('http://cache.video.qiyi.com/v/%s' % videoid).Execute()

# 节目列表
class ParserAlbumList(KolaParser):
    def __init__(self, cid=0, page=1):
        super().__init__()
        if cid and page:
            self.cmd['source']  = 'http://list.iqiyi.com/www/%d/-6---------0--2-2-%d-1---.html' % (cid, page)
            self.cmd['regular'] = ['(<a  class="pic_list imgBg1"[\s\S]*?</a>)']
            #self.cmd['regular'] = ['class="imgBg1 pic_list" (href=".*")']
            #self.cmd['regular'] = ['(data-qidanadd-tvid=".*")']
            self.cmd['cid']     = cid
            self.cmd['page']    = page

    def CmdParser(self, js):
        if not js['data']: return

        soup = bs(js['data'])  # , from_encoding = 'GBK')
        playlist = soup.findAll('a', { "class" : "pic_list imgBg1" })
        #playlist = js['data'].split()
        for a in playlist:
            text = str(a)

            href = ''
            albumid = ''
            tvid = ''
            vlist = re.findall('(albumid|channelid|tvid|vip|href|title)="([\s\S]*?)"', text)
            for u in vlist:
                if u[0] == 'href':
                    href = u[1]
                elif u[0] == 'albumid':
                    albumid = u[1]
                elif u[0] == 'tvid':
                    tvid = u[1]

            if tvid != albumid:
                ParserAlbumJsonAVList(albumid, tvid, href).Execute()
            elif href:
                ParserAlbumPage(href).Execute()

        if len(playlist) > 0:
                ParserAlbumList(js['cid'], js['page'] + 1).Execute()

class QiyiVideoMenu(kola.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.albumClass = QiyiAlbum

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        ParserAlbumList(self.cid, 1).Execute()

    def UpdateHotList(self):
        pass

    def UpdateAllScore(self):
        pass

# 电影
class QiyiMovie(QiyiVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 1
        self.HomeUrlList = ['http://list.qiyi.com/api/chandata.json?c=1&ph=1&s=1&o=20&p=1',
                            'http://list.qiyi.com/api/chandata.json?c=1&ph=1&s=2&o=20&p=1']

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 电视
class QiyiTV(QiyiVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 2
        self.HomeUrlList = ['http://list.iqiyi.com/www/1/-6---------0--2-2-1-1---.html']

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass


# Qiyi 搜索引擎
class QiyiEngine(VideoEngine):
    def __init__(self):
        super().__init__()

        self.engine_name = 'QiyiEngine'
        self.albumClass = QiyiAlbum

        # 引擎主菜单
        self.menu = [
            QiyiMovie('电影'),
            QiyiTV('电视剧'),
        ]

        self.parserList = [
            ParserAlbumList(),
            ParserAlbumPage(),
            ParserAlbumJson(),
            ParserAlbumJsonA(),
            ParserAlbumJsonAVList(),
            ParserAlbumXml(),
        ]

