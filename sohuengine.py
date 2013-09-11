#! env /usr/bin/python3
# -*- coding: utf-8 -*-

'''
Created on 2013-9-7

@author: zhuzhg
'''

import logging
import traceback
import sys
import json
import re
from .utils.fetchTools import fetch_httplib2 as fetch
from .engine import VideoBase, AlbumBase, VideoMenuBase, VideoEngine
#from .utils.BeautifulSoup import BeautifulSoup as bs
import redis
from bs4 import (
        BeautifulSoup as bs,
        BeautifulStoneSoup,
)

logging.basicConfig()
log = logging.getLogger("crawler")

#================================= 以下是搜狐视频的搜索引擎 =======================================
SOHU_HOST = 'tv.sohu.com'
MAX_TRY = 3

class SohuVideo(VideoBase):
    def __init__(self, v):
        pass
    def GetPlayerUrl(self):
        return 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % self.vid

class SohuAlbum(AlbumBase):
    def __init__(self, parent):
        AlbumBase.__init__(self, parent)
        self.VideoClass = SohuVideo

    # 更新节目所有信息
    def UpdateAllCommand(self):
        if self.UpdateFullInfoCommand():
            self.UpdateScoreCommand()
        else: #　如果没有 playlistid
            self.UpdateAlbumPageCommand()

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        ret = self.playlistid != ""

        if ret:
            url = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=%s' % self.playlistid
            self.command.SendCommand('album_fullinfo', self.parent.name, url)

        return ret


    # 更新节目指数信息
    def UpdateScoreCommand(self):
        ret = self.playlistid != ""
        if ret:
            url = 'http://index.tv.sohu.com/index/switch-aid/%s' % self.playlistid
            self.command.SendCommand('album_score', self.parent.name, url)
        return ret

    # 访问网页
    def UpdateAlbumPageCommand(self):
        if self.albumPageUrl != '':
            self.command.SendCommand('album', self.parent.name, self.albumPageUrl)

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
                   'album_fullinfo': self.CmdParserAlbumFullInfo,
                   'album_mvinfo'  : self.CmdParserAlbumMvInfo,
        }
        self.albumClass = SohuAlbum
        self.filter_year = [
                   {'2013':''},
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

    def GetFilterJson(self):
        ret = {}
        for k,v in list(self.filter.items()):
            ret[k] = [list(x.keys())[0] for x in v]

        return ret

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
        if '类型' in self.filter:
            for (_, v) in list(self.filter['类型'].items()):
                sc = sc + v + '_'
        url = fmt % (v, self.number, sc)

        self.command.SendCommand('albumlist_hot', self.name, url)

    def UpdateHotInfo2(self):
        # http://so.tv.sohu.com/jsl?c=100&area=5&cate=100102_100122&o=1&encode=GBK
        fmt = 'http://so.tv.sohu.com/jsl?c=%d&cate=%s&o=1'
        sc = ''
        if '类型' in self.filter:
            for (_, v) in list(self.filter['类型'].items()):
                sc += v + '_'
        url = fmt % (v, self.number, sc)

        self.command.SendCommand('albumlist_hot', self.name, url)

    # 解析热门节目
    # http://so.tv.sohu.com/iapi?v=4&c=115&t=1&sc=115101_115104&o=3
    # albumlist_hot

    def _save_update_append(self, sets, tv):
        if tv:
            tv.SaveToDB(self.engine.album_table)
            tv.UpdateAllCommand()
            sets.append(tv)

    def CmdParserHotInfoByIapi(self, js):
        ret = []
        try:
            text = js['data']
            js = json.loads(text)
            tv = None
            if 'r' in js:
                for p in js['r']:
                    if 'url' in p:
                        tv = self.GetAlbumByUrl(p['url'])
                    elif 'aurl' in p:
                        tv = self.GetAlbumByUrl(p['aurl'])
            self._save_update_append(ret, tv)
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
                playlistid = ''
                albumName = ''
                albumPageUrl = ''
                a = json.loads(g.group(1))
                if 'playlistId' in a:
                    playlistid = str(a['playlistId'])

                if 'videos' in a and str(a['videos']) > 0:
                    tv = None
                    video = a['videos'][0]
                    if 'videoAlbumName' in video:
                        albumName = video['videoAlbumName']
                    if tv == None and 'privdate_data' in js:
                        albumPageUrl = js['privdate_data'][0]

                    tv = self.GetAlbum(playlistid, albumName, albumPageUrl)

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
    def CmdParserAlbumFullInfo(self, js):
        ret = []
        try:
            text = js['data']
            js = json.loads(text)

            playlistid = js['playlistid']
            albumName = ''
            albumPageUrl = ''

            if 'albumName' in js:
                albumName = js['albumName']

            if 'albumPageUrl' in js:
                albumPageUrl = js['albumPageUrl']

            p = self.GetAlbum(playlistid, albumName, albumPageUrl)
            if p:
                p.LoadFromJson(js)
                p.SaveToDB(self.engine.album_table)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumFullInfo:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析所有节目列表
    # http://tv.sohu.com/tvall/
    # videoall
    def CmdParserTVAll(self, js):
        ret = []

        try:
            text = js['data']
            soup = bs(text)
            playlist = soup.findAll('li')
            for a in playlist:
                text = re.findall('<a href="(\S*)"\s+target="_blank">\s*(\S*)\s*</a>', a.prettify())
                if text:
                    (url, album) = text[0]

                    if url != "" and album != "":
                        test = [
                                'http://tv.sohu.com/s2011/1663/s322643386/',
#                                 'http://tv.sohu.com/s2011/ajyh/',
#                                 'http://tv.sohu.com/20110426/n306486856.shtml',
#                                 'http://store.tv.sohu.com/view_content/movie/5008825_704321.html',
#                                 'http://tv.sohu.com/20120517/n343417005.shtml',
#                                 'http://tv.sohu.com/s2012/zlyeye/',
#                                 'http://store.tv.sohu.com/5009508/706684_1772.html',
                                ]
#                        if url in test:
#                            pass
#                        else:
#                            continue

                        tv = self.albumClass(self)
                        if tv.albumName == "":
                            tv.albumName = album
                        tv.albumPageUrl = url
                        self._save_update_append(ret, tv)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
        return ret

    # 解析节目基本信息
    # http://tv.sohu.com/20120517/n343417005.shtml
    # album
    def CmdParserAlbum(self, js):
        ret = []
        try:
            text = js['data']
            tv = self.GetAlbumByUrl(js['source'], False)
            if tv == None:
                return []

            t = re.findall('var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)', text)
            if t:
                for u in t:
                    if u[0] == 'pid':
                        tv.pid = u[1]
                    elif u[0] == 'vid':
                        tv.vid = u[1]
                    elif u[0] == 'playlistId' or u[0] == 'PLAYLIST_ID':
                        tv.playlistid = u[1]
                    elif u[0] == 'tag' and tv.albumName == "":
                        tv.albumName = u[1]

                if tv.vid == '-1' or tv.vid == '' or tv.vid == '1':
                    return ret
                # 如果得不到 playlistId 的话
                if tv.playlistid == "" and tv.vid != "":
                    url = 'http://search.vrs.sohu.com/mv_i%s.json' % tv.vid
                    if 'pid.json' in url:
                        print(text)
                    elif 'PLAYLIST_ID.json' in url:
                        print(text)
                    self.command.SendCommand("album_mvinfo", self.name, url, js['source'])
                tv.SaveToDB(self.engine.album_table)
                tv.UpdateFullInfoCommand()
                tv.UpdateScoreCommand()
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
    def CmdParserAlbumScore(self, js):
        ret = []
        try:
            x = re.search('(.*?),"asudIncomes', js['data'])
            if x and x.lastindex > 0:
                text = x.group(1) + '}'
            else:
                return []

            data = json.loads(text)
            if 'album' in data:
                album = data['album']
                if album:
                    playlistid   = 'id' in album and album['id'] or ''
                    albumName    = 'albumName' in album and album['albumName'] or ''
                    albumPageUrl = 'playUrl' in album and album['playUrl'] or ''

                    tv = self.GetAlbum(playlistid, albumName, albumPageUrl)
                    if tv == None:
                        return ret
                    tv.albumName = album['albumName']

                    if 'album' in data:
                        index = data['index']
                        if index:
                            tv.dailyPlayNum    = index['dailyPlayNum']    # 每日播放次数
                            tv.weeklyPlayNum   = index['weeklyPlayNum']   # 每周播放次数
                            tv.monthlyPlayNum  = index['monthlyPlayNum']  # 每月播放次数
                            tv.totalPlayNum    = index['totalPlayNum']    # 总播放资料
                            tv.dailyIndexScore = index['dailyIndexScore'] # 每日指数

                    tv.SaveToDB(self.engine.album_table)
                    ret.append(tv)

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
                    self._save_update_append(ret, tv)
                elif tv.albumPageUrl != "":
                    # 如果无法直接解析出节目信息，则进入详细页面解析, 重新解析
                    print("No Found:", tv.albumPageUrl)
                    tv.UpdateAlbumPageCommand()
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
                'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)'
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
            'name'    : 'album_fullinfo',
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

    def ParserRealUrl(self, text):
        res = []
        try:
            jdata = json.loads(text)
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
            log.error('SohuEngine.ParserRealUrl playurl: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return res;

    def RealUrl(self, playurl, times=0):
        res = []
        if times > MAX_TRY:
            return res
        try:
            _, _, _, response = fetch(playurl)
            vid = re.search('vid="(\d+)', response).group(1)
            newurl = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
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
        return res

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
                        album.playlistid = newid[0][1]
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
            if album.playlistid == '' :
                _, _, _, response = fetch(album.albumPageUrl)
                if response == None:
                    print('error url: ', album.albumPageUrl)
                    return

                pid = re.findall('(var PLAYLIST_ID|playlistId)\s*="(\d+)', response)
                if pid:
                    album.playlistid = pid[0][1]
                else:
                    # 多部电视情况
                    return
            newurl = 'http://hot.vrs.sohu.com/vrs_videolist.action?playlist_id=%s' % album.playlistid
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

class test_case:
    def __init__(self):
        self.vid = ''
        self.pid = ''
        self.playlistid = ''

    def test_avs_i(self):
        url = 'http://search.vrs.sohu.com/avs_i%s_pr%s_o2_n_p1000_chltv.sohu.com.json' % (self.vid, self.pid)
        _, _, _, response = fetch(url)
        oflvo = re.search('var video_album_videos_result=(\{.*.\})', response).group(1)
        a = json.loads(oflvo)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_v(self):
        # url ='http://search.vrs.sohu.com/v?id=1268036&pageSize=200000&pageNum=1'
        url = 'http://search.vrs.sohu.com/v?id=1268037&pid=5497903&pageNum=1&pageSize=50&isgbk=true&var=video_similar_search_result'
        _, _, _, response = fetch(url)
        oflvo = re.search('var video_similar_search_result=(\{.*.\})', response).group(1)
        a = json.loads(oflvo)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_videopage(self):
        url = 'http://tv.sohu.com/20130517/n376295917.shtml'
        url = 'http://tv.sohu.com/20110222/n279464056.shtml'
        url = 'http://tv.sohu.com/s2011/1663/s322643386/'
    #    url = 'http://v.tv.sohu.com/20100618/n272893884.shtml'
    #    url = 'http://tv.sohu.com/20101124/n277876671.shtml'
    #    url = 'http://tv.sohu.com/s2010/72jzk/'
    #    url = 'http://tv.sohu.com/s2011/7film/'
        _, _, _, response = fetch(url)
        a = re.findall('var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\s*\W*(.+?)"*', response)
        print(a)

    def test_mvi(self):
        url = 'http://search.vrs.sohu.com/mv_i%s.json' % self.vid
        _, _, _, response = fetch(url)
        oflvo = re.search('var video_album_videos_result=(\{.*.\})', response).group(1)
        a = json.loads(oflvo)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_allvideo(self):
        url = 'http://tv.sohu.com/tvall'
        _, _, _, response = fetch(url)
        soup = bs(response)
        playlist = soup.findAll('li')
        for a in playlist:
            xx = re.findall('<a href="(\S*)"\s+target="_blank">\s*(\S*)\s*</a>', a.prettify())
            if xx:
                print(xx[0][0], xx[0][1])

    def test_videolist(self):
        url = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=%s' % self.playlistid
        _, _, _, response = fetch(url)
        a = json.loads(response)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_iapi(self):
        url = 'http://so.tv.sohu.com/iapi?v=2&c=100'
        _, _, _, response = fetch(url)
        a = json.loads(response)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_switch_aid(self):
        url = 'http://index.tv.sohu.com/index/switch-aid/' + self.playlistid
        _, _, _, response = fetch(url)
        a = json.loads(response)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_list(self):
        url = 'http://so.tv.sohu.com/list_p1101_p2_p3_p4_p5_p6_p7_p8_p9.html'
        _, _, _, response = fetch(url)
        x = re.findall('(<a class="pic" target="_blank" title=".+/></a>)', response)
        for a in x:
            print(a)
        x = re.findall('(<p class="tit tit-p">.+</a>)', response)
        for a in x:
            print(a)
        return
        x.extend(re.findall('<p class="tit tit-p">', response))
        print(str(x))

    def test_jsl(self):
        url = 'http://so.tv.sohu.com/jsl?c=100&cate=100100_100107&o=1&pageSize=1'
        _, _, _, response = fetch(url)
        a = json.loads(response)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_all(self):
        self.test_videolist()
        return

        self.test_all()
        self.test_avs_i()
        self.test_v()
        self.test_videopage()
        self.test_iapi()
        self.test_switch_aid()
        self.test_jsl()
        self.test_list()

def test():
    t = test_case()
    t.test_videopage()
    return
    t.playlistid = '1005485'
    t.vid = '460464'
    t.pid = '322963713'

    t.playlistid = '1002050'
    t.vid = '460464'
    t.pid = '322963713'
    t.test_videolist()


if __name__ == '__main__':
    test()
