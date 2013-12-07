#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback
import re
import tornado.escape
import hashlib

from bs4 import BeautifulSoup as bs
from engine import VideoEngine, KolaParser
from kola import VideoBase, AlbumBase, VideoMenuBase
from kola import log, autostr

#================================= 以下是视频的搜索引擎 =======================================
global Debug
Debug = True
HOST_URL = 'http://www.wolidou.com'

# 更新节目的播放信息
class TemplateWolidouAlbumList(KolaParser):
    def __init__(self, menu, url):
        cmd = {
            'name'   : 'wolidou_list',
            'source' : url,
            'regular': [ '(<li>\s*<div class="left">[\s\S]*.?</div>\s*</li>|<option value=.*html\'>)' ],
            'cache'  : False or Debug
        }
        super().__init__(menu.command, cmd)

class TemplateWolidouAlbumPage(KolaParser):
    def __init__(self, album):
        cmd = {
            'name'   : 'wolidou_album_page',
            'source' : album.albumPageUrl,
            'regular': [ '<div id="pplist">([\s\S]*.?)</div>\s*<div class="ddes">' ],
            'cache'  : False or Debug,
            'vid'    : album.vid
        }
        super().__init__(album.command, cmd)

class TemplateWolidouAlbumVideoUrl(KolaParser):
    def __init__(self, engine, vid, server, url):
        cmd = {
            'name'   : 'wolidou_album_video_url',
            'source' : url,
            'regular': [ '<input type="hidden" id="zsurl" name="zsurl" value="(.*)"\s*/>' ],
            'cache'  : False or Debug,
            'server' : server,
            'vid'    : vid
        }
        super().__init__(engine.command, cmd)


class WolidouVideo(VideoBase):
    def __init__(self, js=None):
        super().__init__(js)
        self.TVList = {
            '浙江电视台' : {
                'channels' : [{
                    'script'     : 'zjtv.lua',
                    'function'   : 'get_channel',
                    'parameters' : 'api.cztv.com',
                    'area'       : '浙江省'},
                ]
            },
            '杭州电视台' : {
                'channels' : [{
                    'script'   : 'hztv.lua',
                    'function' : 'get_channel',
                    'area'     : '浙江省杭州市'}
                ]
            },
            '宁波电视台' : {
                'channels' : [
                    {'script'     : 'jztv.lua',
                     'parameters' : 'ming-api.nbtv.com',
                     'area'       : '浙江省杭州市' },
                ]
            },
            '卫视' :{
                   'channels': [
                    {'script' : 'wolidu.lua',
                     'parameters' : []}
                    ]
            }
        }


    def GetVideoPlayUrl(self, definition=0):
        pass

    def SaveToJson(self):
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)

class WolidouAlbum(AlbumBase):
    def __init__(self, parent):
        super().__init__(parent)

        self.albumPageUrl = ''
        self.VideoClass = WolidouVideo

    def SaveToJson(self):
        ret = super().SaveToJson()
        pri = {}
        if self.albumPageUrl    : pri['albumPageUrl'] = self.albumPageUrl

        if pri:
            ret['private'] = pri

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if 'private' in json:
            pri = json['private']
            if 'albumPageUrl' in pri   : self.albumPageUrl = pri['albumPageUrl']

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        pass

    # 更新节目主页
    def UpdateAlbumPageCommand(self):
        if self.albumPageUrl:
            TemplateWolidouAlbumPage(self).Execute()

class WolidouTV(VideoMenuBase):
    def __init__(self, name, engine):
        super().__init__(name, engine)
        self.homePage = ''
        self.HomeUrlList = []
        self.albumClass = WolidouAlbum
        self.cid = 200
        self.sort = {
            '周播放最多' : 7,
            '日播放最多' : 5,
            '总播放最多' : 1,
            '最新发布'   : 3,
            '评分最高'   : 4
        }
        self.Outside = '凤凰|越南|半岛|澳门|东森|澳视|亚洲|良仔|朝鲜| TV|KP|Yes|HQ|NASA|Poker|Docu|Channel|Neotv|fashion|Sport|sport|Power|FIGHT|Pencerahan|UK|GOOD|Kontra|Rouge|Outdoor|Divine|Europe|DaQu|Teleromagna|Alsharqiya|Playy|Boot Movie|Runway|Bid|LifeStyle|CBN|HSN|BNT|NTV|Virgin|Film|Smile|Russia|NRK|VIET|Gulli|Fresh'
        self.filter = {
            '类型' : {
                'CCTV' : 'cctv|CCTV',
                '卫视台' : '卫视',
                '体育台' : '体育|足球|网球',
                '综合台' : '综合|财|都市|经济|旅游',
                '动画台' : '动画|卡通|动漫',
                '地方台' : '^(?!.*?(cctv|CCTV|卫视|测试|' + self.Outside + ')).*$',
                '境外台' : self.Outside
            }
        }

    def GetCategories(self, name):
        ret = []
        for k, v in self.filter['类型'].items():
            x = re.findall(v, name)
            if x:
                ret.append(k)
        return ret

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        url = HOST_URL + '/tvz/cctv/70_1.html'
        TemplateWolidouAlbumList(self, url).Execute()
        url = HOST_URL + '/tvl/weishi/2_1.html'
        TemplateWolidouAlbumList(self, url).Execute()
        #url = HOST_URL + '/tvl/shengshi/3_1.html'
        #TemplateWolidouAlbumList(self, url).Execute()
        #url = HOST_URL + '/tvl/guonei/10_1.html'
        #TemplateWolidouAlbumList(self, url).Execute()

    def GetRealPlayer(self, text, definition, step):
        jdata = tornado.escape.json_decode(text)
        ret = {}
        try:
            ret['directPlayUrl'] = jdata['location']
            ret['name'] = jdata['desc']
            ret['publishTime'] = autostr(jdata['starttime'])
            print(ret)
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine._ParserRealUrlStep2: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return ret

# Letv 搜索引擎
class WolidouEngine(VideoEngine):
    def __init__(self, command):
        super().__init__(command)

        self.engine_name = 'WolidouEngine'
        self.albumClass = WolidouAlbum
        self.videoClass = WolidouVideo

        # 引擎主菜单
        self.menu = {
            '直播'   : WolidouTV
        }

        self.parserList = {
            'wolidou_list' : self._CmdParserWolidouList,
            'wolidou_album_page' : self._CmdParserWolidouAlbumPage,
            'wolidou_album_video_url' : self._CmdParserWolidouAlbumVideoUrl
        }

    def _exclude_host(self, url):
        hosts = ()
        for h in hosts:
            if h in url:
                return False
        return True

    def _get_priority(self, url):
        hosts = ("sohu.php", "dxtx.php", "dxnm.php", 'dxnm.php', 'dxifeng.php', 'basicflv.php', "sxmsp.php", "jstv.php", "moon.php", "dxcctv.php")
        prior = 1
        for h in hosts:
            if h in url:
                return prior
            prior+= 1

        return 100

    def _CmdParserWolidouAlbumVideoUrl(self, js):
        text = js['data']
        if not text:
            return
        if self._exclude_host(text) == False:
            return
        album = self.GetAlbumFormDB(vid=js['vid'])
        if album:
            v = self.NewVideo()
            v.playlistid = album.playlistid
            v.pid = album.vid
            v.cid = album.cid
            v.priority = self._get_priority(text)
            v.vid = hashlib.md5(js['source'].encode()).hexdigest()[16:]
            v.script = {
                    'script' : 'wolidu',
                    'parameters' : [text, js['source'], js['server']]
            }

            album.videos.append(v)
            self._save_update_append(None, album)

    def _CmdParserWolidouAlbumPage(self, js):
        text = js['data']

        soup = bs(js['data'])  # , from_encoding = 'GBK')
        playlist = soup.findAll('div', { "class" : "ppls" })
        for a in playlist:
            text = str(a)
            b = re.findall('<span class="ppls_s">(\S*)\s*?', text)

            if b == None:
                continue

            album = self.GetAlbumFormDB(vid=js['vid'])
            if not album:
                continue

            if b[0] == '基本收视服务器：':
                print(b)
                u = re.findall('<li><a href="(.*0.html)" target="_blank">.*</a></li>', text)
                if u:
                    for url in u:
                        TemplateWolidouAlbumVideoUrl(self, js['vid'], b[0], HOST_URL + url).Execute()

            if b[0] in set(['超速服务器：', 'M3U8专线服务器：']):
                print(b)
                u = re.findall('<li><a href="(.*)" target="_blank">.*</a></li>', text)
                if u:
                    for url in u:
                        TemplateWolidouAlbumVideoUrl(self, js['vid'], b[0], HOST_URL + url).Execute()

#            if b and b[0] in set(['基本收视服务器：', 'M3U8专线服务器：', '超速服务器：', '飞速服务器：', '极速服务器【节目可回放】：']):
#                print(b)
#                b = re.findall('<li><a href="(.*)" target="_blank">.*</a></li>', text)
#                if b:
#                    for url in b:
#                        print(HOST_URL + url)
#                        TemplateWolidouAlbumVideoUrl(self, HOST_URL + url).Execute()
#            else:
#                print("No server", b) #<input type="hidden" id="zsurl" name="zsurl"

    # 从分页的页面上解析该页上的节目
    # videolist
    def _CmdParserWolidouList(self, js):
        text = js['data']
        soup = bs(js['data'])  # , from_encoding = 'GBK')
        playlist = soup.findAll('li')
        tvmenu = WolidouTV('直播', self)
        for a in playlist:
            img = ''
            name = ''
            url = ''
            text = str(a)  # .prettify(formatter='html')
            x = re.findall('img alt.*src="(.*)"', text)
            if x:
                img = HOST_URL + x[0]
            x = re.findall('<div class="right"><span><a href="(.*)">([\s\S]*?)</a></span>', text)
            if x:
                url = HOST_URL + x[0][0]
                name = x[0][1]
            print('img=%s, name=%s, url=%s' % (img, name, url))


            album = self.NewAlbum()
            album.cid = 200
            album.vid = hashlib.md5(name.encode()).hexdigest()[16:]
            album.albumName = name
            album.categories = tvmenu.GetCategories(name)
            album.albumPageUrl = url

            self._save_update_append(None, album)

        playlist = soup.findAll('option')

        startUpdate = False
        for a in playlist:
            text = str(a)
            x = re.findall('<option value="(.*)">', text)
            if x:
                url = HOST_URL + x[0]
                if startUpdate == False and url == js['source']:
                    startUpdate = True
                    continue

                if startUpdate:
                    TemplateWolidouAlbumList(self, url).Execute()

        # self._save_update_append(None, album)
