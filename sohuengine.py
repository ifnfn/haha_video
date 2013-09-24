#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import traceback
import sys
import json
import re
import redis
import base64
import tornado.escape

from bs4 import BeautifulSoup as bs
from fetchTools import fetch_httplib2 as fetch
from engine import VideoBase, AlbumBase, VideoMenuBase, VideoEngine, Template

logging.basicConfig()
log = logging.getLogger("crawler")

#================================= 以下是搜狐视频的搜索引擎 =======================================
SOHU_HOST = 'tv.sohu.com'
MAX_TRY = 3

# 搜狐节目列表
class TemplateVideoAll(Template):
    def __init__(self, menu):
        cmd = {
            'name' : 'videoall',
            'menu': menu.name,
            'source': menu.homePage
        }
        super().__init__(menu.command, cmd)

# 搜狐节目列表
class TemplateVideoList(Template):
    def __init__(self, menu, url):
        cmd = {
            'name': 'videolist',
            'menu': menu.name,
            'source': url,
            'regular': [
                    '(<a class="pic" target="_blank" title=".+/></a>)',
                    '(<p class="tit tit-p">.+</a>)'
                ]
        }
        super().__init__(menu.command, cmd)
        #self.command = menu.command.AddCommand2(cmd)

# 搜狐节目
class TemplateAlbum(Template):
    def __init__(self, album):
        cmd = {
            'name'    : 'album',
            'source'  : album.albumPageUrl,
            'menu'    : album.parent.name,
            'regular' : [
                'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
            ],
        }
        super().__init__(album.command, cmd)
        #self.command = album.command.AddCommand2(cmd)

# 搜狐节目指数
class TemplateAlbumScore(Template):
    def __init__(self, album):
        cmd = {
            'name'    : 'album_score',
            'source'  : 'http://index.tv.sohu.com/index/switch-aid/' + album.playlistid,
            'menu'    : '电影',
            'json'    : [
                         'attachment.album',
                         'attachment.index'
            ],
        }
        super().__init__(album.command, cmd)
        #self.command = album.command.AddCommand2(cmd)

# 更新热门节目信息
class TemplateAlbumHotList(Template):
    def __init__(self, menu, url):
        cmd = {
            'name'    : 'albumlist_hot',
            'source'  : url, #'http://so.tv.sohu.com/iapi?v=4&c=115&t=1&sc=115101_115104&o=3',
            'menu'    : menu.name,
        }
        super().__init__(menu.command, cmd)

# 更新节目的完整信息
class TemplateAlbumFullInfo(Template):
    def __init__(self, album):
        cmd = {
            'name' : 'album_fullinfo',
            'menu' : album.parent.name,
            'source' : 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=%s' % album.playlistid
        }
        super().__init__(album.command, cmd)
        #self.command = album.command.AddCommand2(cmd)

# 更新节目的完整信息
class TemplateAlbumMvInfo(Template):
    def __init__(self, album, source_url):
        cmd = {
            'name'    : 'album_mvinfo',
            'menu'    : album.parent.name,
            'source'  : 'http://search.vrs.sohu.com/mv_i%s.json' % album.vid,
            'privdate_data' : source_url
        }
        super().__init__(album.command, cmd)

# 更新节目的播放信息
class TemplateAlbumPlayInfo(Template):
    def __init__(self, album, url):
        cmd = {
            'name'    : 'album_playinfo',
            'source'  : url, #'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s',
            'menu'    : album.parent.name,
            'json' : [
                'data.highVid',
                'data.norVid',
                'data.oriVid',
                'data.superVid',
                'data.relativeId',
                'id'
            ],
        }
        super().__init__(album.command, cmd)

class SohuVideo(VideoBase):
    def __init__(self, v):
        pass

class SohuAlbum(AlbumBase):
    def __init__(self, parent):
        AlbumBase.__init__(self, parent)
        self.VideoClass = SohuVideo

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        ret = self.playlistid != ""

        if ret:
            TemplateAlbumFullInfo(self)
            #url = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=%s' % self.playlistid
            #self.command.AddCommand('album_fullinfo', self.parent.name, url)

        return ret

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        ret = self.playlistid != ""
        if ret:
            TemplateAlbumScore(self).Execute()
            #url = 'http://index.tv.sohu.com/index/switch-aid/%s' % self.playlistid
            #self.command.AddCommand('album_score', self.parent.name, url)
        return ret

    # 更新节目主页
    def UpdateAlbumPageCommand(self):
        if self.albumPageUrl != '':
            TemplateAlbum(self).Execute()
            #self.command.AddCommand('album', self.parent.name, self.albumPageUrl)

    # 更新节目播放信息
    def UpdateAlbumPlayInfoCommand(self):
        url = self.GetVideoPlayUrl()
        if url != '':
            TemplateAlbumPlayInfo(self, url)
            #self.command.AddCommand('album_playinfo', self.parent.name, url)

    # 得到节目的地址
    def GetVideoPlayUrl(self, definition=0):
        maplist = self.vid,self.norVid,self.highVid,self.supverVid,self.oriVid,self.relativeId
        if definition < len(maplist):
            vid = maplist[definition]
            if vid != '':
                return 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid

        return ''

class SohuVideoMenu(VideoMenuBase):
    def __init__(self, name, engine):
        VideoMenuBase.__init__(self, name, engine)
        self.homePage = ''
        self.HomeUrlList = []
        if hasattr(self, 'number'):
            self.HomeUrlList = ['http://so.tv.sohu.com/list_p1%d_p20_p3_p40_p5_p6_p73_p80_p9_2d1_p101_p11.html' % self.number]

        self.parserList = {
                   'videolist'      : self._CmdParserVideoList,
                   'album'          : self._CmdParserAlbumPage,
                   'album_score'    : self._CmdParserAlbumScore,
                   'videoall'       : self._CmdParserAlbumList,
                   'albumlist_hot'  : self._CmdParserHotInfoByIapi,
                   'album_fullinfo' : self._CmdParserAlbumFullInfo,
                   'album_mvinfo'   : self._CmdParserAlbumMvInfo,
                   'album_playinfo' : self._CmdParserAlbumPlayInfo,
        }
        self.albumClass = SohuAlbum
        self.filter_year = {
            '2013' : '',
            '2012' : '',
            '2011' : '',
            '2010' : '',
            '00年代': '',
            '90年代': '',
            '80年代': '',
            '更早'  : ''
        }
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
        self.sort = {
            '周播放最多' : 7,
            '日播放最多' : 5,
            '总播放最多' : 1,
            '最新发布'   : 3,
            '评分最高'   : 4
        }

        self.fieldMapping = {
            '类型' : 'categories',
            '产地' : 'area',
            '地区' : 'area', # Music
            '年份' : 'publishYear',
            '篇幅' : '',
            '年龄' : '',
            '范围' : '',
            '语言' : '',
            '周播放最多' : 'weeklyPlayNum',
            '日播放最多' : 'dailyPlayNum',
            '总播放最多' : 'totalPlayNum',
            '最新发布'   : 'publishTime',
            '评分最高'   : 'dailyIndexScore'
        }

    def GetFilterJson(self):
        ret = {}
        for k,v in list(self.filter.items()):
            ret[k] = [x for x in v]

        return ret

    def GetSortJson(self):
        ret = []
        for k in self.sort:
            ret.append(k)

        return ret

    def ConvertFilterJson(self, f):
        for key in f:
            if key in self.fieldMapping:
                newkey = self.fieldMapping[key]
                f[newkey] = { "$in" : [f[key]]}
                del f[key]
        return f

    def ConvertSortJson(self, v):
        if v in self.fieldMapping:
            newkey = self.fieldMapping[v]
            return [(newkey, -1)]
        else:
            return [(v, -1)]

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        if self.homePage != "":
            TemplateVideoAll(self).Execute()
            #self.command.AddCommand('videoall', self.name, self.homePage).Execute()

    # 获取所有节目列表的别一种方法，该方法备用
    def UpdateAlbumList2(self):
        for url in self.HomeUrlList:
            TemplateVideoList(self, url).Execute()
            #self.command.AddCommand('videolist', self.name, page)

    def _GetHtmlList(self, playurl, times=0):
        ret = []
        count = 0
        if times > MAX_TRY:
            return ret
        try:
            print(playurl)
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
                    print(newurl)
                    ret.append(newurl)
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine.GetHtmlList:  %s, %s,%s,%s' % (playurl, t, v, traceback.format_tb(tb)))
            return self.GetHtmlList(playurl, times + 1)

        return ret;

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

        TemplateAlbumHotList(self, url).Execute()
        #self.command.AddCommand('albumlist_hot', self.name, url).Execute()

    def UpdateHotList2(self):
        # http://so.tv.sohu.com/jsl?c=100&area=5&cate=100102_100122&o=1&encode=GBK
        fmt = 'http://so.tv.sohu.com/jsl?c=%d&cate=%s&o=1'
        sc = ''
        if '类型' in self.filter:
            for (_, v) in list(self.filter['类型'].items()):
                sc += v + '_'
        url = fmt % (v, self.number, sc)

        TemplateAlbumHotList(self, url).Execute()
        #self.command.AddCommand('albumlist_hot', self.name, url).Execute()

    def _save_update_append(self, sets, tv):
        if tv:
            tv.SaveToDB(self.engine.album_table)
            sets.append(tv)

    # 解析热门节目
    # http://so.tv.sohu.com/iapi?v=4&c=115&t=1&sc=115101_115104&o=3
    # albumlist_hot
    def _CmdParserHotInfoByIapi(self, js):
        ret = []
        try:
            js = tornado.escape.json_decode(js['data'])

            tv = None
            if 'r' in js:
                for p in js['r']:
                    if 'url' in p:
                        tv = self.GetAlbumFormDB(albumPageUrl = p['url'])
                    elif 'aurl' in p:
                        tv = self.GetAlbumFormDB(albumPageUrl = p['aurl'])
            self._save_update_append(ret, tv)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserHotInfoByIapi  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

    # 通过 vid 获得节目更多的信息
    # http://search.vrs.sohu.com/mv_i1268037.json
    # album_mvinfo
    def _CmdParserAlbumMvInfo(self, js):
        ret = []
        try:
            text = js['data'].decode()
            g = re.search('var video_album_videos_result=(\{.*.\})', text)
            if g:
                playlistid = ''
                albumName = ''
                albumPageUrl = ''
                a = tornado.escape.json_decode(g.group(1))
                if 'playlistId' in a:
                    playlistid = str(a['playlistId'])

                if 'videos' in a and len(a['videos']) > 0:
                    tv = None
                    video = a['videos'][0]
                    if 'videoAlbumName' in video:
                        albumName = video['videoAlbumName']
                    if tv == None and 'privdate_data' in js:
                        albumPageUrl = js['privdate_data']

                    tv = self.GetAlbumFormDB(playlistid, albumName, albumPageUrl)

                    if tv == None:
                        return []

                    if 'isHigh' in video          : tv.isHigh = str(video['isHigh'])
                    if 'albumDesc' in video       : tv.albumDesc = video['albumDesc']

                    if 'AlbumYear' in video       : tv.publishYear = str(video['AlbumYear'])
                    if 'videoScore' in video      : tv.videoScore = str(video['videoScore'])
                    if 'videoArea' in video       : tv.area = video['videoArea']
                    if 'videoMainActor' in video  : tv.mainActors = video['videoMainActor'].split(';') # 主演
                    if 'videoActor' in video      : tv.actors = video['videoActor'].split(';') # 演员
                    if 'videoDirector' in video   : tv.directors = video['videoDirector'].split(';') # 导演

                    if 'videoAlbumContCategory' in video:
                        tv.categories = video['videoAlbumContCategory'].split(';')

                    self._save_update_append(ret, tv)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumMvInfo: %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析节目的完全信息
    # http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5112241
    # album_fullinfo
    def _CmdParserAlbumFullInfo(self, js):
        ret = []
        try:
            js = tornado.escape.json_decode(js['data'])

            playlistid = js['playlistid']
            albumName = ''
            albumPageUrl = ''

            if 'albumName' in js:
                albumName = js['albumName']

            if 'albumPageUrl' in js:
                albumPageUrl = js['albumPageUrl']

            p = self.GetAlbumFormDB(playlistid, albumName, albumPageUrl)
            if p:
                if 'videos' in js:
                    if 'vid' in js:
                        vid = js['vid']
                    else:
                        vid = -1

                    for video in js['videos']:
                        if 'vid' in video and video['vid'] == vid and vid != -1:
                            if 'playLength' in video: p.playLength =  video['playLength']
                            if 'publishTime' in video: p.publishTime = video['publishTime']

                        video = p.VideoClass(video)
                        p.videos.append(video)
                del js['videos']

                p.LoadFromJson(js)
                p.SaveToDB(self.engine.album_table)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumFullInfo:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析所有节目列表：
    # 拿到菜单下所有节目的 albumName、albumPageUrl
    # http://tv.sohu.com/tvall/
    # videoall
    def _CmdParserAlbumList(self, js):
        ret = []

        try:
            text = js['data']
            soup = bs(text)#, from_encoding = 'GBK')
            playlist = soup.findAll('li')
            for a in playlist:
                text = re.findall('<a href="(\S*)"\s+target="_blank">\s*(\S*)\s*</a>', a.prettify())
                if text:
                    (url, album) = text[0]

                    if url != "" and album != "":
#                        test = [
#                                'http://tv.sohu.com/s2011/1663/s322643386/',
#                                 'http://tv.sohu.com/s2011/ajyh/',
#                                 'http://tv.sohu.com/20110426/n306486856.shtml',
#                                 'http://store.tv.sohu.com/view_content/movie/5008825_704321.html',
#                                 'http://tv.sohu.com/20120517/n343417005.shtml',
#                                 'http://tv.sohu.com/s2012/zlyeye/',
#                                 'http://store.tv.sohu.com/5009508/706684_1772.html',
#                                ]
#                        if url in test:
#                            pass
#                        else:
#                            continue

                        tv = self.albumClass(self)
                        if tv.albumName == "":
                            tv.albumName = album
                        tv.albumPageUrl = url
                        self._save_update_append(ret, tv)

                        # 获取更多的信息
                        #tv.UpdateAlbumPageCommand().Execute()
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
        return ret

    # 解析节目基本信息：
    # 主要要拿到节目的playlistid、vid、pid，如果没有找到playlistid，则通过 mv_i继续找
    # http://tv.sohu.com/20120517/n343417005.shtml
    # album
    def _CmdParserAlbumPage(self, js):
        ret = []
        try:
            text = js['data'].decode()
            tv = self.GetAlbumFormDB(albumPageUrl=js['source'], auto=False)
            if tv == None:
                return []

            t = re.findall('var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)', text)
            if t:
                for u in t:
                    if u[0] == 'pid':
                        tv.pid = u[1]
                    elif u[0] == 'vid':
                        tv.vid = u[1]
                    elif u[0] == 'playlistId' or u[0] == 'PLAYLIST_ID':
                        tv.playlistid = u[1]

                if tv.vid == '-1' or tv.vid == '' or tv.vid == '1':
                    return ret
                # 如果得不到 playlistId 的话
                if tv.playlistid == "" and tv.vid != "":
                    TemplateAlbumMvInfo(tv, js['source']).Execute()
#                     url = 'http://search.vrs.sohu.com/mv_i%s.json' % tv.vid
#                     if 'pid.json' in url:
#                         print(text)
#                     elif 'PLAYLIST_ID.json' in url:
#                         print(text)
#                     self.command.AddCommand("album_mvinfo", self.name, url, js['source']).Execute()
                tv.SaveToDB(self.engine.album_table)
                #tv.UpdateFullInfoCommand().Execute()
                #tv.UpdateScoreCommand().Execute()
            else:
                db = redis.Redis(host='127.0.0.1', port=6379, db=2) # 出错页
                db.rpush('urls', js['source'])

                print("ERROR: ", js['source'])
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbum:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析节目指数信息
    # http://index.tv.sohu.com/index/switch-aid/1012657
    # album_score
    def _CmdParserAlbumScore(self, js):
        ret = []
        try:
            data = tornado.escape.json_decode(js['data'])
            if 'album' in data:
                album = data['album']
                if album:
                    playlistid   = 'id' in album and album['id'] or ''
                    albumName    = 'albumName' in album and album['albumName'] or ''
                    albumPageUrl = 'playUrl' in album and album['playUrl'] or ''

                    tv = self.GetAlbumFormDB(playlistid, albumName, albumPageUrl)
                    if tv == None:
                        return ret
                    tv.albumName = album['albumName']

                    if 'index' in data:
                        index = data['index']
                        if index:
                            if 'dailyPlayNum' in index:
                                tv.dailyPlayNum    = index['dailyPlayNum']    # 每日播放次数
                            if 'weeklyPlayNum' in index:
                                tv.weeklyPlayNum   = index['weeklyPlayNum']   # 每周播放次数
                            if 'monthlyPlayNum' in index:
                                tv.monthlyPlayNum  = index['monthlyPlayNum']  # 每月播放次数
                            if 'totalPlayNum' in index:
                                tv.totalPlayNum    = index['totalPlayNum']    # 总播放资料
                            if 'dailyIndexScore' in index:
                                tv.dailyIndexScore = index['dailyIndexScore'] # 每日指数
                            if playlistid in ['5770420', '308122']:
                                print(playlistid, ": weeklyPlayNum=", tv.weeklyPlayNum)


                    tv.SaveToDB(self.engine.album_table)
                    ret.append(tv)

        except:
            print(js['source'])
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumScore:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析节目播放信息
    # 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s
    # album_playinfo
    def _CmdParserAlbumPlayInfo(self, js):
        ret = []
        try:
            data = tornado.escape.json_decode(js['data'])
            vid = data['id']
            tv = self.GetAlbumFormDB(vid=vid)
            if tv:
                if 'highVid' in data: tv.highVid = data['highVid']
                if 'norVid' in data: tv.norVid = data['norVid']
                if 'oriVid' in data: tv.oriVid = data['oriVid']
                if 'superVid' in data: tv.superVid = data['superVid']
                if 'relativeId' in data: tv.relativeId = data['relativeId']
                tv.SaveToDB(self.engine.album_table)
                ret.append(tv)
        except:
            print(js['source'])
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumScore:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 从分页的页面上解析该页上的节目
    def _CmdParserVideoList(self, js):
        ret = []
        try:
            g = re.search('p10(\d+)', js['source'])
            if g:
                current_page = int(g.group(1))
                link = re.compile('p10\d+')
                newurl = re.sub(link, 'p10%d' % (current_page + 1), js['source'])
                TemplateVideoList(self, newurl).Execute()

            text = js['data']
            soup = bs(text)
            playlist = soup.findAll('a')

            for tag in playlist:
                tv = self.albumClass(self)
                text = tag.prettify()

                urls = re.findall('(href|title)="(\S+)"', text)
                for u in urls:
                    if u[0] == 'href':
                        tv.albumPageUrl = u[1]
                        try:
                            ids = re.search('(\d+)_(\d+)', u[1])
                            if ids:
                                tv.pid = ids.group(1)
                                tv.vid = ids.group(2)
                        except:
                            t, v, tb = sys.exc_info()
                            log.error('SohuGetVideoList:  %s, %s,%s,%s' % (tv.albumPageUrl, t, v, traceback.format_tb(tb)))
                    elif u[0] == 'title':
                        newid = re.findall('(vrsab_ver|vrsab)([0-9]+).(jpg|jpeg)', u[1])
                        if len(newid) > 0:
                            tv.playlistid = newid[0][1]

                # 取节目的标题
                x = re.findall('<img.*title="(\S+)"', text)
                if x:
                    tv.albumName = x[0]

                self._save_update_append(ret, tv)
                # 获取更多的信息
                #tv.UpdateAlbumPageCommand().Execute()
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserVideoList:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
        return ret

# 电影
class SohuMovie(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 100
        SohuVideoMenu.__init__(self, name, engine)
#        self.HomeUrlList = [
#            'http://so.tv.sohu.com/list_p1100_p20_p3_p40_p5_p6_p73_p80_p9_2d1_p101_p11.html',
#        ]
        self.cid = 1
        self.homePage = 'http://tv.sohu.com/movieall/'
        self.filter = {
            '年份' :  self.filter_year,
            '类型' : {
                '爱情片' : '100100',
                '战争片' : '100101',
                '喜剧片' : '100102',
                '科幻片' : '100103',
                '恐怖片' : '100104',
                '动画片' : '100105',
                '动作片' : '100106',
                '风月片' : '100107',
                '剧情片' : '100108',
                '歌舞片' : '100109',
                '纪录片' : '100110',
                '魔幻片' : '100111',
                '灾难片' : '100112',
                '悬疑片' : '100113',
                '传记片' : '100114',
                '警匪片' : '100116',
                '伦理片' : '100117',
                '惊悚片' : '100118',
                '谍战片' : '100119',
                '历史片' : '100120',
                '武侠片' : '100121',
                '青春片' : '100122',
                '文艺片' : '100123'
            },
            '产地' : {
                '内地'  : '5',
                '香港'  : '27',
                '台湾'  : '28',
                '日本'  : '3',
                '韩国'  : '4',
                # '欧洲' : '2',
                '美国'  : '12',
                '英国'  : '17',
                '法国'  : '18',
                '德国'  : '19',
                '意大利': '20',
                '西班牙': '21',
                '俄罗斯': '24',
                '加拿大': '25',
                '印度'  : '22',
                '泰国'  : '23',
                '其他'  : ''
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 电视
class SohuTV(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 101
        SohuVideoMenu.__init__(self, name, engine)
        self.cid = 2
#        self.HomeUrlList = [
#            'http://so.tv.sohu.com/list_p1101_p20_p3_p40_p5_p6_p73_p80_p9_2d1_p101_p11.html'
#        ]
        self.homePage = 'http://tv.sohu.com/tvall/'
        self.filter = {
            '年份' : self.filter_year,
            '类型' : {
                '偶像片'   : '101100',
                '家庭片'   : '101101',
                '历史片'   : '101102',
                '年代片'   : '101103',
                '言情片'   : '101104',
                '武侠片'   : '101105',
                '古装片'   : '101106',
                '都市片'   : '101107',
                '农村片'   : '101108',
                '军旅片'   : '101109',
                '刑侦片'   : '101110',
                '喜剧片'   : '101111',
                '悬疑片'   : '101112',
                '情景片'   : '101113',
                '传记片'   : '101114',
                '科幻片'   : '101115',
                '动画片'   : '101116',
                '动作片'   : '101117',
                '真人秀片' : '101118',
                '栏目片'   : '101119',
                '谍战片'   : '101120',
                '伦理片'   : '101121',
                '战争片'   : '101122',
                '神话片'   : '101123',
                '惊悚片'   : '101124',
            },
            '产地' : {
                '内地' : '5',
                '港剧' : '6',
                '台剧' : '7',
                '美剧' : '9',
                '韩剧' : '8',
                '英剧' : '10',
                '泰剧' : '11',
                '日剧' : '15',
                '其他' : ''
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 动漫
class SohuComic(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 115
        SohuVideoMenu.__init__(self, name, engine)
        self.homePage = 'http://tv.sohu.com/comicall/'
        self.filter = {
            '年份' : self.filter_year,
            '篇幅' : {
                '剧场版' : '1',
                'TV版'   : '2',
                '花絮'   : '3',
                'OVA'    : '5',
                '其他'   : '3'
            },
            '类型' : {
                '历史'   : '115100',
                '搞笑'   : '115101',
                '战斗'   : '115102',
                '冒险'   : '115103',
                '魔幻'   : '115104',
                '励志'   : '115105',
                '益智'   : '115106',
                '童话'   : '115107',
                '体育'   : '115108',
                '神话'   : '115110',
                '青春'   : '115111',
                '悬疑'   : '115112',
                '真人'   : '115113',
                '亲子'   : '115114',
                '恋爱'   : '115118',
                '科幻'   : '115123',
                '治愈'   : '115124',
                '日常'   : '115125',
                '神魔'   : '115126',
                '百合'   : '115127',
                '耽美'   : '115128',
                '校园'   : '115129',
                '后宫'   : '115130',
                '美少女' : '115131',
                '竞技'   : '115132',
                '机战'   : '1151233',
            },
            '产地' : {
                '大陆' : '1',
                '日本' : '2',  # 7
                '美国' : '3',
                '韩国' : '5',
                '香港' : '6',
                '欧洲' : '',  # 英国8 加拿大 11 俄罗期 13
                '其他' : '',
            },
            '年龄' : {
                '5岁以下'   : '0',
                '5岁-12岁'  : '1',
                '13岁-18岁' : '2',
                '18岁以上'  : '3',
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 综艺
class SohuShow(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 106
        SohuVideoMenu.__init__(self, name, engine)
        self.homePage = ''
        self.filter = {
            '类型' : {
                '访谈'     : '106100',
                '时尚'     : '106101',
                '游戏竞技'  : '106102',
                'KTV'      : '106103',
                '交友'     : '106104',
                '选秀'     : '106105',
                '音乐'     : '106106',
                '曲艺'     : '106107',
                '养生'     : '106109',
                '脱口秀'   : '106110',
                '歌舞'     : '106111',
                '娱乐节目' : '106112',
                '真人秀'   : '106113',
                '其他'     : '106118'
            },
            '产地' : {
                '内地' : '5',
                '港台' : '14',
                '欧美' : '',  # 15?
                '日韩' : '16',
                '其他' : '',
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 记录片
class SohuDocumentary(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 107
        SohuVideoMenu.__init__(self, name, engine)
        self.homePage = ''
        self.filter = {
            '类型': {
                  '人物' : '107100',
                  '历史' : '107101',
                  '自然' : '107102',
                  '军事' : '107103',
                  '社会' : '107104',
                  '幕后' : '107105',
                  '财经' : '107106',
                  '搜狐视频大视野' : '107107',
                  '剧情' : '107108',
                  '旅游' : '107109',
                  '科技' : '107110',
                  '文化' : '107111',
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 教育
class SohuEdu(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 119
        SohuVideoMenu.__init__(self, name, engine)
        self.homePage = ''
        self.filter = {
            '类型': {
                '公开课':'119100',
                '考试辅导':'119101',
                '职业培训':'119102',
                '外语学习':'119103',
                '幼儿教育':'119104',
                '乐活':'119105',
                '职场管理':'119106',
                '中小学教育':'119107'
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 新闻
class SohuNew(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 122
        SohuVideoMenu.__init__(self, name, engine)
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
    def __init__(self, name, engine):
        self.number = 112
        SohuVideoMenu.__init__(self, name, engine)
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
    def __init__(self, name, engine):
        self.number = 131
        SohuVideoMenu.__init__(self, name, engine)
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

    def GetMenu(self):
        ret = {}
        for m, cls in list(self.menu.items()):
            if cls:
                ret[m] = cls(m, self)
        return ret

    def GetMenu2(self, times=0):
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
                            t = self.menu[menu_name](menu_name, self)
                            ret[menu_name] = t
                            #ret[menu_name.decode('utf-8')] = t
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine.GetMenu:  %s, %s,%s, %s' % (playurl, t, v, traceback.format_tb(tb)))
            return self.GetMenu(times + 1)

        return ret

    def GetRealPlayer(self, text, definition, step):
        if step == '1':
            res = self._ParserRealUrlStep1(text)
        else:
            res = self._ParserRealUrlStep1(text)

        return json.dumps(res, indent=4, ensure_ascii=False)

    def _ParserRealUrlStep1(self, text):
        res = {}
        try:
            jdata = tornado.escape.json_decode(text)
            if 'data' not in jdata:
                return res

            host = jdata['allot']
            prot = jdata['prot']
            urls = []
            data = jdata['data']
            if data == None:
                return {}

            if 'totalBytes' in data:
                res['totalBytes'] = data['totalBytes']

            if 'totalBlocks' in data:
                res['totalBlocks'] = data['totalBlocks']

            if 'totalDuration' in data:
                res['totalDuration'] = data['totalDuration']
            if 'clipsDuration' in data:
                res['clipsDuration'] = data['clipsDuration']
            if 'height' in data:
                res['height'] = data['height']
            if 'width' in data:
                res['width'] = data['width']

            if 'fps' in data:
                res['fps'] = data['fps']

            if 'scap' in jdata: # 字幕
                res['scap'] = jdata['scap']

            for tfile, new, duration, byte in zip(data['clipsURL'], data['su'], data['clipsDuration'], data['clipsBytes']):
                x = {}
                x['duration'] = duration
                x['size'] = byte
                x['new'] = new
                x['url'] = 'http://%s/?prot=%s&file=%s&new=%s' % (host, prot, tfile, new)
                urls.append(x)

            res['sets'] = urls

            return res
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine._ParserRealUrlStep1 playurl: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return res;

    def _ParserRealUrlStep2(self, text):
        ret = {}
        try:
            ret = tornado.escape.json_decode(text)

            if 'sets' in ret:
                urls = []
                for url in ret['sets']:
                    new = url['new']
                    text = base64.decodebytes(url['url'].encode()).decode()

                    start, _, _, key, _, _, _, _ = text.split('|')
                    u = '%s%s?key=%s' % (start[:-1], new, key)
                    urls.append(u)

                ret['sets'] = urls
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine._ParserRealUrlStep2 playurl: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return ret

