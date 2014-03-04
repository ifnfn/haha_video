#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import sys
import time
import traceback
from bs4 import BeautifulSoup as bs, Tag
from urllib.parse import quote

import tornado.escape

from kola import DB, autostr, autoint, autofloat, Singleton, utils
import kola

from .engines import VideoEngine, KolaParser, KolaAlias, EngineVideoMenu


#================================= 以下是搜狐视频的搜索引擎 =======================================
global Debug
Debug = True

class QQAlias(KolaAlias):
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

alias = QQAlias()

class QQVideo(kola.VideoBase):
    def SaveToJson(self):
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)

    def SetVideoScript(self, name, vid, func_name='kola_main'):
        url = {
            'script'     : 'qq',
            'parameters' : [autostr(vid), autostr(self.cid)]
        }
        if func_name and func_name != 'kola_main':
                url['function'] = func_name

        self.SetVideoUrl(name, url)

class QQPrivate:
    def __init__(self):
        self.name =  '乐视'
        self.vid = ''
        self.videoListUrl = {}

    def Json(self):
        json = {'name' : self.name}
        if self.vid          : json['vid'] = self.vid
        if self.videoListUrl : json['videoListUrl'] = self.videoListUrl

        return json

    def Load(self, js):
        if 'name' in js         : self.name         = js['name']
        if 'vid' in js          : self.vid          = js['vid']
        if 'videoListUrl' in js : self.videoListUrl = js['videoListUrl']

class QQAlbum(kola.AlbumBase):
    def __init__(self):
        self.engineName = 'QQEngine'
        super().__init__()

        self.qq = QQPrivate()

        self.videoClass = QQVideo

    def SaveToJson(self):
        if self.qq:
            self.private[self.engineName] = self.qq.Json()
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if self.engineName in self.private:
            self.qq.Load(self.private[self.engineName])

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        pass
        #if self.qq.playlistid:
        #    ParserPlayCount(self).Execute()

class QQDB(DB, Singleton):
    def __init__(self):
        super().__init__()
        self.albumNameAlias = {}   # 别名
        self.blackAlbumName = {}   # 黑名单

    # 从数据库中找到 album
    def FindAlbumJson(self, qvid='', albumName=''):
        qvid = autostr(qvid)
        if qvid == '' and albumName == '':
            return None

        f = []
        if albumName: f.append({'albumName'            : albumName})
        if qvid     : f.append({'private.QQEngine.vid' : qvid})

        return self.album_table.find_one({'engineList' : {'$in' : ['QQEngine']}, '$or' : f})

    def GetMenuAlbumList(self, cid, All=False):
        fields = {'engineList' : True,
                  'albumName': True,
                  'private'  : True,
                  'cid'      : True,
                  'vid'      : True}

        data = self.album_table.find({'engineList' : {'$in' : ['QQEngine']}, 'cid' : cid}, fields)

        albumList = []
        for p in data:
            album = QQAlbum()
            album.LoadFromJson(p)
            albumList.append(album)

        return albumList

    # 从数据库中找到album
    def GetAlbumFormDB(self, qvid='', albumName='', auto=False):
        album = None
        json = self.FindAlbumJson(qvid, albumName)
        if json:
            album = QQAlbum()
            album.LoadFromJson(json)
        elif auto:
            album = QQAlbum()
            if qvid:
                album.qq.vid = qvid
            if albumName:
                album.mName = albumName

        return album

    def SaveAlbum(self, album, upsert=True):
        if album.albumName and album.qq.vid:
            self._save_update_append(None, album, key={'private.QQEngine.vid' : album.qq.vid}, upsert=upsert)

class ParserPlayCount(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['name'] = album.albumName
            self.cmd['source'] = '%s' % (album.qq.vid)

    def CmdParser(self, js):
        if not js['data']: return

        db = QQDB()
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
    alias = QQAlias()
    def __init__(self, url=None, cid=0):
        super().__init__()
        if url and cid:
            self.cmd['source']  = url
            self.cmd['regular'] = ['(<a href=".*" title=".*" target="_blank" _hot="movielist.title.link.0">.*</a>)']
            self.cmd['cid']     = cid

    def CmdParser(self, js):
        soup = bs(js['data'])  # , from_encoding = 'GBK')
        playlist = soup.findAll('a', { "_hot" : "movielist.title.link.0" })
        for a in playlist:
            href = a.attrs['href']
            name = a.text
            print(name, href)
            ParserAlbumPage2(href, name, js['cid']).Execute()

        if len(playlist) > 0 and False:
            g = re.search('http://v.qq.com/movielist/10001/0/10004-100001/0/(\d+)', js['source'])
            if g:
                current_page = int(g.group(1))
                link = re.compile('http://v.qq.com/movielist/10001/0/10004-100001/0/\d+')
                newurl = re.sub(link, 'http://v.qq.com/movielist/10001/0/10004-100001/0/%d' % (current_page + 1), js['source'])
                ParserAlbumList(newurl, js['cid']).Execute()

class ParserAlbumPage2(KolaParser):
    #http://s.video.qq.com/search?comment=1&plat=2&otype=json&query=%E6%84%8F%E5%A4%96%E7%9A%84%E6%81%8B%E7%88%B1%E6%97%B6%E5%85%89
    #urlencode
    def __init__(self, url=None, name=None, cid=0):
        super().__init__()

        if url and name and cid:
            self.cmd['source'] = 'http://s.video.qq.com/search?comment=1&plat=2&otype=json&query=%s' % quote(name)
            self.cmd['cid']     = cid
            self.cmd['name']    = name
            self.cmd['urlx']    = url

    def CmdParser(self, js):
        db = QQDB()
        text = re.findall('QZOutputJson=({[\s\S]*});', js['data'])
        if not text:
            return

        json = tornado.escape.json_decode(text[0])

        for a in json['list']:
            if a['AW'] == js['urlx']:
                print(a['AC'], a['AT'], a['AU'], a['TX'])
                album = QQAlbum()
                album_js = DB().FindAlbumJson(albumName=a['title'])
                if album_js:
                        album.LoadFromJson(album_js)

                album.albumName = db.GetAlbumName(a['title'])
                if not album.albumName:
                    continue
                album.vid = utils.genAlbumId(album.albumName)
                album.cid = js['cid']

                if 'AC' in a: album.area        = alias.Get(a['AC'])               # 地区
                if 'BE' in a: album.categories  = alias.GetStrings(a['BE'], ';')   # 类型
                if 'BM' in a: album.mainActors  = a['BM'].split(';')     # 主演
                if 'BD' in a: album.directors   = a['BD'].split(';')     # 导演
                if 'AY' in a: album.publishYear = a['AY']
                if 'TX' in a: album.albumDesc   = a['TX']                # 简介
                if 'ID' in a: album.qq.vid      = a['ID']

                if 'AU' in a:
                    album.largePicUrl      = a['AU']                # 大图
                    album.smallPicUrl      = a['AU']                # 小图
                    album.largeHorPicUrl   = a['AU']                # 横大图
                    album.smallHorPicUrl   = a['AU']                # 横小图
                    album.largeVerPicUrl   = a['AU']                # 竖大图
                    album.smallVerPicUrl   = a['AU']                # 竖小图

                if 'Z1' in a and 'pic2' in a['Z1']:
                    album.smallHorPicUrl = a['Z1']['pic2']

                if 'AT' in a:
                    album.updateTime  = time.mktime(time.strptime(a['AT'],"%Y-%m-%d %H:%M:%S"))
                    album.publishTime = album.updateTime

                if 'src_list' in a and 'vsrcarray' in a['src_list']:
                    vsrcarray = a['src_list']['vsrcarray'][0]
                    if 'total_episode' in vsrcarray:
                        album.totalSet         = autoint(vsrcarray['total_episode'])       # 总集数
                    if 'cnt' in vsrcarray:
                        if 'nowEpisodes' in a: album.updateSet        = autoint(a['nowEpisodes'])    # 当前更新集

                album.qq.videoListUrl = utils.GetScript('qq', 'get_videolist', [js['source'], album.qq.vid])

                db.SaveAlbum(album)
                break

# 节目列表
class ParserAlbumPage(KolaParser):
    alias = QQAlias()
    def __init__(self, url=None, name=None, cid=0):
        super().__init__()
        if url and cid and name:
            print(url)
            self.cmd['source']  = url
            self.cmd['regular'] = ['(<div class="(video_title|info_cast|info_director|info_category|info_area|info_years|info_summary cf)"[\s\S]*?</div>|<img itemprop="image" src=[\s\S]*?>)']
            self.cmd['cid']     = cid
            self.cmd['name']    = name

    def CmdParser(self, js):
        ret = {}
        soup = bs(js['data'])  # , from_encoding = 'GBK')

        images = soup.findAll('img', {'itemprop' : 'image'})
        for img in images:
            image = img.get('src', '')
            if image:
                ret['image'] = image
        ret['name'] = js['name']

        playlist = soup.findAll('div') #, { "_hot" : "movielist.title.link.0" })
        for a in playlist:
            if type(a) == Tag:
                x = a.findAll('span', {'class' : 'label'})
                if x:
                    key = x[0].text.replace('：', '')
                    ret[key] = []

                    if key in ['主演', '导演']:
                        vlist = a.findAll('span', {'itemprop' : 'name'})
                        for v in vlist:
                            text = v.text.strip()
                            ret[key].append(text)
                    elif key in ['类型']:
                        vlist = a.findAll('a')
                        for v in vlist:
                            text = v.text.strip()
                            ret[key].append(text)
                    elif key in ['地区', '年份']:
                        vlist = a.findAll('a')
                        for v in vlist:
                            text = v.text.strip()
                            ret[key] = text
                    elif key  in ['简介']:
                        vlist = a.findAll('span', {'class' : 'desc'})
                        for v in vlist:
                            text = v.text.strip()
                            ret[key] = text

        print(ret)

class QQVideoMenu(EngineVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.albumClass = QQAlbum
        self.DBClass = QQDB

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            ParserAlbumList(url, self.cid).Execute()

# 电影
class QQMovie(QQVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 1
        self.HomeUrlList = ['http://v.qq.com/movielist/10001/0/10004-100001/0/0/20/0/0.html']

# 电视
class QQTV(QQVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 2
        self.HomeUrlList = []

# 动漫
class QQComic(QQVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 3
        self.HomeUrlList = []

# 记录片
class QQDocumentary(QQVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 4
        self.HomeUrlList = []

# 综艺
class QQShow(QQVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 5
        self.HomeUrlList = []

# QQ 搜索引擎
class QQEngine(VideoEngine):
    def __init__(self):
        super().__init__()

        self.engine_name = 'QQEngine'
        self.albumClass = QQAlbum

        # 引擎主菜单
        self.menu = [
            QQMovie('电影'),
            #QQTV('电视剧'),
            #QQComic('动漫'),
            #QQDocumentary('记录片'),
            #QQShow('综艺')
        ]

        self.parserList = [
            ParserAlbumList(),
            ParserPlayCount(),
            ParserAlbumPage(),
            ParserAlbumPage2(),
        ]
