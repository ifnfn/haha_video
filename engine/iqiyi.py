#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time, sys, traceback
import tornado.escape
from bs4 import BeautifulSoup as bs
from xml.etree import ElementTree

from engine import VideoEngine, KolaParser, KolaAlias
from kola import DB, autostr, autoint, Singleton, utils
import kola


#================================= 以下是搜狐视频的搜索引擎 =======================================
global Debug
Debug = True

class QiyiAlias(KolaAlias):
    def __init__(self):
        self.alias = {
            # 电视剧
            '言情剧' : '言情片',
            '历史剧' : '历史片',
            '武侠剧' : '武侠片',
            '古装剧' : '古装片',
            '年代剧' : '年代片',
            '农村剧' : '农村片',
            '偶像剧' : '偶像片',
            '悬疑剧' : '悬疑片',
            '科幻剧' : '科幻片',
            '喜剧'   : '喜剧片',
            '宫廷剧' : '宫廷片',
            '商战剧' : '谍战片',
            '穿越剧' : '穿越片',
            '罪案剧' : '刑侦片',
            '谍战剧' : '谍战片',
            '青春剧' : '偶像片',
            '家庭剧' : '家庭片',
            '军旅剧' : '军旅片',

            # 电影
            '爱情' : '爱情片',
            '战争' : '战争片',
            '喜剧' : '喜剧片',
            '科幻' : '科幻片',
            '恐怖' : '恐怖片',
            '动作' : '动作片',
            '动画' : '动画片',
            '悲剧' : '悲剧片',
            '灾难' : '灾难片',
            '剧情' : '剧情片',
            '惊悚' : '惊悚片',
            '魔幻' : '魔幻片',
            '青春' : '青春片',
            '枪战' : '枪战片',
            '伦理' : '伦理片',
            '悬疑' : '悬疑片',
            '犯罪' : '警匪片',
            '传记' : '其他',
            '歌舞' : '其他',
            '运动' : '其他',
            '其它' : '其他',

            # 地址
            '华语' : '内地',
            '大陆' : '内地',
        }

class QiyiAliasComic(KolaAlias):
    def __init__(self):
        self.alias = {
            # 动漫
        '未来':'科幻',
        '侦探':'悬疑',
        '言情':'恋爱',
    }

alias = QiyiAlias()
ComicAlias = QiyiAliasComic()

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

class ParserAlbumJsonAVList(KolaParser):
    def __init__(self, albumid=None, tvid=None, albumUrl=None, cid=None):
        super().__init__()
        if albumid and tvid and albumUrl and cid:
            self.cmd['source']  = 'http://cache.video.qiyi.com/avlist/%s/' % albumid
            self.cmd['albumid'] = albumid
            self.cmd['tvid'] = tvid
            self.cmd['aurl'] = albumUrl
            self.cmd['cid']  = cid

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
            ParserAlbumJson(tvid, videoid, js['cid']).Execute()

class ParserAlbumJsonA(KolaParser):
    def __init__(self, albumid=None, tvid=None, videoid=None, ar=None, tg=None, cid=None):
        super().__init__()
        if albumid and tvid and videoid and cid:
            self.cmd['source']  = 'http://cache.video.qiyi.com/a/%s' % albumid
            self.cmd['tvid']    = tvid
            self.cmd['videoid'] = videoid
            self.cmd['albumid'] = albumid
            self.cmd['ar']      = ar
            self.cmd['tg']      = tg
            self.cmd['cid']     = cid

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
            #album.cid = json['albumType']
            album.cid = js['cid']

            if album.cid == 3:
                a = ComicAlias
            else:
                a = alias

            album.area             = a.Get(js['ar'])                           # 地区
            album.categories       = a.GetStrings(js['tg'], ' ')               # 类型
            #album.categories       = [v+"片" for v in js['tg'].split(' ')]     # 类型

            album.publishYear      = autoint(json['tvYear']) // 10000          # 年

            album.albumPageUrl     = json['purl']                              # 'vu'
            album.largePicUrl      = json['tvPictureUrl']                      # 大图 post20 最大的

            if not album.largePicUrl:
                print(album.largePicUrl)
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
    def __init__(self, tvid=None, videoid=None, cid=None):
        super().__init__()
        if tvid and videoid and cid:
            self.cmd['source'] = 'http://cache.video.qiyi.com/vi/%s/%s/' % (tvid, videoid)
            self.cmd['cid'] = cid

    def CmdParser(self, js):
        json = tornado.escape.json_decode(js['data'])
        ar = json['ar']
        tg = json['tg']
        aid = json['aid']
        vid = json['vid']
        tvid = json['tvid']

        ParserAlbumJsonA(aid, tvid, vid, ar, tg, js['cid']).Execute()

class ParserAlbumPage(KolaParser):
    def __init__(self, url=None, cid=None):
        super().__init__()
        if url and cid:
            self.cmd['source']  = url
            self.cmd['regular'] = ['(data-player-videoid.*|data-player-tvid.*|data-player-albumid)']
            self.cmd['cid'] = cid

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
            ParserAlbumJson(tvid, videoid, js['cid']).Execute()
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
                ParserAlbumJsonAVList(albumid, tvid, href, js['cid']).Execute()
            elif href:
                ParserAlbumPage(href, js['cid']).Execute()

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

# 动漫
class QiyiComic(QiyiVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 3
        self.HomeUrlList = ['http://list.iqiyi.com/www/4/------------2-1-1-1---.html',
                            'http://list.iqiyi.com/www/15/------------2-1-1-0---.html',
                            ]

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 记录片
class QiyiDocumentary(QiyiVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 3
        self.HomeUrlList = ['http://list.iqiyi.com/www/3/----------0--2-1-1-1---.html']

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
            QiyiComic('动漫'),
            QiyiDocumentary('记录片'),
        ]

        self.parserList = [
            ParserAlbumList(),
            ParserAlbumPage(),
            ParserAlbumJson(),
            ParserAlbumJsonA(),
            ParserAlbumJsonAVList(),
        ]

