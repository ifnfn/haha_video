#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
import time
from urllib.parse import quote

from bs4 import BeautifulSoup as bs, Tag
import tornado.escape

import kola

from .engines import VideoEngine, KolaParser, KolaAlias, EngineVideoMenu


global Debug
Debug = True

class FunshionAlias(KolaAlias):
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

alias = FunshionAlias()

class FunshionPrivate:
    def __init__(self):
        self.name =  'PPTV'
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

class FunshionAlbum(kola.AlbumBase):
    def __init__(self):
        self.engineName = 'FunshionEngine'
        super().__init__()

        self.qq = FunshionPrivate()

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
        if self.qq.vid:
            ParserPlayCount(self).Execute()

class FunshionDB(kola.DB, kola.Singleton):
    def __init__(self):
        super().__init__()
        self.albumNameAlias = {}   # 别名
        self.blackAlbumName = {}   # 黑名单

    # 从数据库中找到 album
    def FindAlbumJson(self, qvid='', albumName=''):
        qvid = kola.autostr(qvid)
        if qvid == '' and albumName == '':
            return None

        f = []
        if albumName: f.append({'albumName'            : albumName})
        if qvid     : f.append({'private.FunshionEngine.vid' : qvid})

        return self.album_table.find_one({'engineList' : {'$in' : ['FunshionEngine']}, '$or' : f})

    def GetMenuAlbumList(self, cid, All=False):
        fields = {'engineList' : True,
                  'albumName': True,
                  'private'  : True,
                  'cid'      : True,
                  'vid'      : True}

        data = self.album_table.find({'engineList' : {'$in' : ['FunshionEngine']}, 'cid' : cid}, fields)

        albumList = []
        for p in data:
            album = FunshionAlbum()
            album.LoadFromJson(p)
            albumList.append(album)

        return albumList

    # 从数据库中找到album
    def GetAlbumFormDB(self, qvid='', albumName='', auto=False):
        album = None
        json = self.FindAlbumJson(qvid, albumName)
        if json:
            album = FunshionAlbum()
            album.LoadFromJson(json)
        elif auto:
            album = FunshionAlbum()
            if qvid:
                album.qq.vid = qvid
            if albumName:
                album.mName = albumName

        return album

    def SaveAlbum(self, album, upsert=True):
        if album.albumName and album.qq.vid:
            self._save_update_append(None, album, key={'private.FunshionEngine.vid' : album.qq.vid}, upsert=upsert)

class ParserPlayCount(KolaParser):
    def __init__(self, album=None):
        super().__init__()
        if album:
            self.cmd['name'] = album.albumName
            self.cmd['source'] = 'http://sns.video.qq.com/tvideo/fcgi-bin/batchgetplaymount?id=%s&otype=json' % album.qq.vid
            self.cmd['qvid'] = album.qq.vid
            self.cmd['cache'] = False

    def CmdParser(self, js):
        text = re.findall('QZOutputJson=({[\s\S]*});', js['data'])
        if not text:
            return

        json = tornado.escape.json_decode(text[0])
        if json['msg'] != 'success':
            return

        db = FunshionDB()
        album = db.GetAlbumFormDB(qvid=js['qvid'])
        if album == None:
            return

        for v in json['node']:
            if v['id'] == js['qvid']:
                if 'all' in v: album.totalPlayNum = v['all']
                if 'yest' in v: album.dailyPlayNum = v['yest']
                db.SaveAlbum(album)

# 节目列表
class ParserAlbumList(KolaParser):
    def __init__(self, url=None, cid=None, album_regular_key=None, next_regular_key=None):
        super().__init__()
        if url and cid and album_regular_key and next_regular_key:
            regular = '(<a href=.*(_hot="%s"|class="next").*</a>|<strong class="c_txt3">.*</strong>)' % (album_regular_key)
            self.cmd['source']    = url
            self.cmd['regular']   = [regular]
            self.cmd['cid']       = cid
            self.cmd['album_key'] = album_regular_key
            self.cmd['next_key']  = next_regular_key

    def CmdParser(self, js):
        #print(js['data'])
        albumlist = []
        soup = bs(js['data'])  # , from_encoding = 'GBK')
        albumTag = soup.findAll('a', { "target" : '_blank' })
        for a in albumTag:
            href = a.attrs['href']
            name = a.text
            albumlist.append({'href': href, 'name': name})

        scoreTag = soup.findAll('strong')
        idx = 0
        for a in scoreTag:
            href = albumlist[idx]['href']
            name = albumlist[idx]['name']
            ParserAlbumPage2(href, name, js['cid'], a.text).Execute()
            idx += 1

        nextTag = soup.findAll('a', { "class" : 'next' })
        if nextTag:
            nexturl = nextTag[0].get('href', '')
            if nexturl:
                print(nexturl)
                ParserAlbumList(nexturl, js['cid'], js['album_key'], js['next_key']).Execute()

class ParserAlbumPage2(KolaParser):
    #http://s.video.qq.com/search?comment=1&plat=2&otype=json&query=%E6%84%8F%E5%A4%96%E7%9A%84%E6%81%8B%E7%88%B1%E6%97%B6%E5%85%89
    #urlencode
    def __init__(self, url=None, name=None, cid=0, score=None):
        super().__init__()

        if url and name and cid and score:
            self.cmd['source'] = 'http://s.video.qq.com/search?comment=1&plat=2&otype=json&query=%s' % quote(name)
            self.cmd['cid']     = cid
            self.cmd['name']    = name
            self.cmd['urlx']    = url
            self.cmd['score']   = score

    def CmdParser(self, js):
        db = FunshionDB()
        text = re.findall('QZOutputJson=({[\s\S]*});', js['data'])
        if not text:
            return

        json = tornado.escape.json_decode(text[0])

        if 'list' not in json:
            return

        for a in json['list']:
            if a['AW'] == js['urlx']:
                #print(a['AC'], a['AT'], a['AU'], a['TX'])
                album = FunshionAlbum()
                album_js = kola.DB().FindAlbumJson(albumName=a['title'])
                if album_js:
                        album.LoadFromJson(album_js)

                album.albumName = db.GetAlbumName(a['title'])
                if not album.albumName:
                    continue

                album.vid   = kola.genAlbumId(album.albumName)
                album.cid   = js['cid']
                album.Score = kola.autofloat(js['score'])

                if 'AC' in a: album.area        = alias.Get(a['AC'])               # 地区
                if 'BE' in a: album.categories  = alias.GetStrings(a['BE'], ';')   # 类型
                if 'BM' in a: album.mainActors  = a['BM'].split(';')     # 主演
                if 'BD' in a: album.directors   = a['BD'].split(';')     # 导演
                if 'AY' in a: album.publishYear = a['AY']
                if 'TX' in a: album.albumDesc   = a['TX']                # 简介
                if 'ID' in a: album.qq.vid      = a['ID']

                if 'AU' in a:
                    album.largePicUrl      = a['AU']                     # 大图
                    album.smallPicUrl      = a['AU']                     # 小图
                    album.largeHorPicUrl   = a['AU']                     # 横大图
                    album.smallHorPicUrl   = a['AU']                     # 横小图
                    album.largeVerPicUrl   = a['AU']                     # 竖大图
                    album.smallVerPicUrl   = a['AU']                     # 竖小图

                if 'Z1' in a and 'pic2' in a['Z1']:
                    album.smallHorPicUrl = a['Z1']['pic2']

                if 'AT' in a:
                    updateTime = time.mktime(time.strptime(a['AT'],"%Y-%m-%d %H:%M:%S"))
                    album.updateTime  = time.strftime('%Y-%m-%d', time.gmtime(updateTime))
                    album.publishTime = album.updateTime

                if 'src_list' in a and 'vsrcarray' in a['src_list']:
                    vsrcarray = a['src_list']['vsrcarray'][0]
                    if 'total_episode' in vsrcarray:
                        album.totalSet = kola.autoint(vsrcarray['total_episode'])       # 总集数
                    if 'cnt' in vsrcarray:
                        if 'nowEpisodes' in a: album.updateSet = kola.autoint(a['nowEpisodes'])    # 当前更新集

                album.qq.videoListUrl = kola.GetScript('qq', 'get_videolist', [js['source'], album.qq.vid])

                db.SaveAlbum(album)
                break

# 节目列表
class ParserAlbumPage(KolaParser):
    alias = FunshionAlias()
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

class FunshionVideoMenu(EngineVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.albumClass = FunshionAlbum
        self.DBClass = FunshionDB
        self.album_regular_key = ''
        self.next_regular_key = ''

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            ParserAlbumList(url, self.cid, self.album_regular_key, self.next_regular_key).Execute()

# 电影
class FunshionMovie(FunshionVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 1
        self.album_regular_key = 'movielist.title.link.0'
        self.next_regular_key = 'movielist.page\w*?.next'
        self.HomeUrlList = ['http://v.qq.com/movielist/10001/0/10004-100001/0/0/100/0/0.html']

# 电视
class FunshionTV(FunshionVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 2
        self.album_regular_key = 'tv.title.link.\w*.\w*'
        self.next_regular_key = 'tv.page\w*?.next.\w*'
        self.HomeUrlList = ['http://v.qq.com/list/2_-1_-1_-1_0_0_0_100_-1_-1_0.html']

# 动漫
class FunshionComic(FunshionVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 3
        self.HomeUrlList = []

# 记录片
class FunshionDocumentary(FunshionVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 4
        self.HomeUrlList = []

# 综艺
class FunshionShow(FunshionVideoMenu):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 5
        self.HomeUrlList = []

# Funshion 搜索引擎
class FunshionEngine(VideoEngine):
    def __init__(self):
        super().__init__()

        self.engine_name = 'FunshionEngine'
        self.albumClass = FunshionAlbum

        # 引擎主菜单
        self.menu = [
            FunshionMovie('电影'),
            FunshionTV('电视剧'),
            #FunshionComic('动漫'),
            #FunshionDocumentary('记录片'),
            #FunshionShow('综艺')
        ]

        self.parserList = [
            ParserAlbumList(),
            ParserPlayCount(),
            ParserAlbumPage(),
            ParserAlbumPage2(),
        ]
