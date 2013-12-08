#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback
import re
import tornado.escape
import hashlib
from xml.etree import ElementTree

from engine import VideoEngine, TVCategory, EngineCommands, KolaParser
import kola
from kola.element import LiveMenu
from kola import json_get, GetNameByUrl
from kola import VideoBase, AlbumBase, DB

global Debug
Debug = True

class LiveVideo(VideoBase):
    def __init__(self, js = None):
        super().__init__(js)

class LiveAlbum(AlbumBase):
    def __init__(self):
        super().__init__()
        self.albumPageUrl = ''

        self.videoClass = LiveVideo

    def SaveToJson(self):
        if self.albumPageUrl: self.private['albumPageUrl'] = self.albumPageUrl
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if 'albumPageUrl' in self.private: self.albumPageUrl = self.private['albumPageUrl']

class LiveVideoMenu(LiveMenu):
    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        ParserLetvLive().Execute()
        ParserSohuLive().Execute()
        ParserTextLive().Execute()
        ParserZJLive().Execute()
        ParserNBLive().Execute()
        ParserHangZhouLive().Execute()
        ParserUCLive().Execute()
        ParserWenZhouLive().Execute()


class LivetvParser(KolaParser):
    def __init__(self):
        super().__init__()
        self.tvCate = TVCategory()
        self.Alias = {}
        self.ExcludeName = ()

    def GetAliasName(self, name):
        for p in list(self.ExcludeName):
            if re.findall(p, name):
                return ""

        if name in self.ExcludeName:
            return ""

        if name in self.Alias:
            return self.Alias[name]

        return name

# 乐视直播电视
class ParserLetvLive(LivetvParser):
    def __init__(self):
        super().__init__()
        self.cmd['name']    = 'live_engine_parser'
        self.cmd['source']  = 'http://www.leshizhibo.com/channel/index.php'
        self.cmd['regular'] = ["<dt>(<a title=.*</a>)</dt>"]


    def CmdParser(self, js):
        db = DB()
        ret = []

        playlist = js['data'].split("</a>")

        for t in playlist:
            #print(t)
            x = re.findall('<a title="(.*)" href=".*/channel/(.*)" target="_blank"><img alt=.* src="(.*)"><span class', t)
            if x:
                name = x[0][0]
                vid = x[0][1]
                print(name, x[0][1], x[0][2])

                album  = LiveAlbum()
                album.cid        = 200
                album.vid        = hashlib.md5(name.encode()).hexdigest()[16:]
                album.albumName  = name
                album.categories = self.tvCate.GetCategories(name)

                v = album.NewVideo()
                v.playUrl     = 'http://live.gslb.letv.com/gslb?stream_id=%s&ext=m3u8&sign=live_tv&format=1' % vid
                v.vid         = hashlib.md5(v.playUrl.encode()).hexdigest()[24:]
                v.largePicUrl = x[0][2]
                v.priority    = 1
                v.name        = "乐视"
                v.script      = {
                    'script' : 'letv',
                    'parameters' : [v.playUrl]
                }

                album.videos.append(v)
                db._save_update_append(ret, album)
        return ret


# 搜狐直播电视
class ParserSohuLive(LivetvParser):
    def __init__(self):
        super().__init__()
        self.cmd['name']    = 'live_engine_parser'
        self.cmd['source'] = 'http://tvimg.tv.itc.cn/live/top.json'

    def CmdParser(self, js):
        db = DB()
        ret = []

        tvlist = tornado.escape.json_decode(js['data'])
        for v in tvlist['attachment']:
            name = json_get(v, 'name', '')
            pid = json_get(v, 'id', '')
            vid = hashlib.md5(name.encode()).hexdigest()[16:]
            album  = LiveAlbum()
            album.cid         = 200
            album.albumName   = json_get(v, 'name', '')
            album.vid         = vid
            #album.enAlbumName = json_get(v, 'enName', '')
            album.smallPicUrl = json_get(v, 'ico', '')

            v = album.NewVideo()
            v.vid      = hashlib.md5(v.playUrl.encode()).hexdigest()[24:]
            v.playUrl  = 'http://live.tv.sohu.com/live/player_json.jhtml?encoding=utf-8&lid=%s&type=1' % pid
            v.priority = 2
            v.name     = "搜狐"
            v.script   = {
                'script' : 'sohutv',
                'parameters' : [v.playUrl]
            }
            album.videos.append(v)
            db._save_update_append(ret, album)

        return ret

class ParserHangZhouLive(LivetvParser):
    def __init__(self):
        super().__init__()
        self.cmd['name']    = 'live_engine_parser'
        self.cmd['source'] = 'http://www.hoolo.tv/'
        self.cmd['script'] = {
                'script' : 'hztvchannels',
                'parameters' : ['']
        }
        self.Alias = {}
        self.ExcludeName = ('交通918', 'FM1054', 'FM89')
        self.area = '中国-淅江省-杭州市'

    def CmdParser(self, js):
        db = DB()
        ret = []
        #for i in range(1, 60):
        for i in (1, 2, 3, 5, 13, 14, 15):
            url = 'http://api1.hoolo.tv/player/live/channel_xml.php?id=%d' % i
            text = kola.GetUrl(url).decode()
            root = ElementTree.fromstring(text)

            name = self.GetAliasName(root.attrib['name'])
            if name == '':
                continue

            ok = False
            for p in root:
                if p.tag == 'video':
                    for item in p.getchildren():
                        if 'url' in item.attrib:
                            ok = True
                            break

            if ok == False:
                continue

            album  = LiveAlbum()
            album.cid       = 200
            album.albumName = name
            album.vid       = hashlib.md5(name.encode()).hexdigest()[16:]
            album.area      = self.area

            v = album.NewVideo()
            v.playUrl  = url
            v.vid      = hashlib.md5(v.playUrl.encode()).hexdigest()[24:]
            v.priority = 2
            v.name     = "hztv"
            v.script   = {
                'script' : 'hztv',
                'parameters' : [v.playUrl]
            }
            album.videos.append(v)
            db._save_update_append(ret, album)
        return ret

class ParserWenZhouLive(LivetvParser):
    def __init__(self):
        super().__init__()
        self.cmd['name']    = 'live_engine_parser'
        self.cmd['source'] = 'http://v.dhtv.cn/tv/'
        self.cmd['regular'] = ['(http://v.dhtv.cn/tv/\?channal=.*</a></li>)']
        self.Alias = {}
        self.ExcludeName = ()
        self.area = '中国-淅江省-温州市'

    def CmdParser(self, js):
        db = DB()
        ret = []
        ch_list = re.findall('(http://v.dhtv.cn/tv/\?channal=(.+))\">(.*)</a></li>', js['data'])
        for u, source, name in ch_list:
            vid = hashlib.md5(name.encode()).hexdigest()[16:]
            album  = LiveAlbum()
            album.cid       = 200
            album.albumName = name
            album.vid       = vid
            album.area      = self.area

            v = album.NewVideo()
            v.playUrl  = u
            v.vid      = hashlib.md5(v.playUrl.encode()).hexdigest()[24:]
            v.priority = 2
            v.name     = "dhtv"
            v.script   = {
                'script' : 'wztv',
                'parameters' : ['http://www.dhtv.cn/static/??js/tv.js?acm', source]
            }
            album.videos.append(v)
            db._save_update_append(ret, album)

class ParserTVIELive(LivetvParser):
    def __init__(self, url):
        super().__init__()
        self.base_url = url
        self.cmd['name']    = 'live_engine_parser'
        self.cmd['source'] = 'http://' + self.base_url + '/api/getChannels'
        self.area = ''

    def CmdParser(self, js):
        db = DB()
        ret = []
        jdata = tornado.escape.json_decode(js['data'])
        try:
            for x in jdata['result']:
                if 'group_names' in x and x['group_names'] == '':
                    continue
                name = ''
                if 'name' in x: name = x['name']
                if 'display_name' in x: name = x['display_name']

                name = self.GetAliasName(name)
                if name == '':
                    continue

                album = LiveAlbum()
                album.cid       = 200
                album.albumName = name
                album.vid       = hashlib.md5(album.albumName.encode()).hexdigest()[16:]
                album.area      = self.area

                v = album.NewVideo()
                # v.pid = album.vid
                # v.cid = album.cid
                v.vid = hashlib.md5(v.playUrl.encode()).hexdigest()[24:]
                v.playUrl = 'http://' + self.base_url + '/api/getCDNByChannelId/' + x['id']

                if self.base_url in ['api.cztv.com']:
                    v.playUrl += '?domain=' + self.base_url
                v.priority = 2
                v.name = "TVIE"
                v.script = {
                    'script' : 'tvie',
                    'parameters' : [v.playUrl]
                }
                album.videos.append(v)
                db._save_update_append(ret, album)
        except:
            t, v, tb = sys.exc_info()
            print("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))


class ParserZJLive(ParserTVIELive):
    def __init__(self):
        self.tvName = '浙江电视台'
        super().__init__('api.cztv.com')
        self.Alias = {
            "频道101" : "浙江卫视",
            "频道102" : "钱江频道",
            "频道103" : "浙江经视",
            "频道104" : "教育科技",
            "频道105" : "浙江影视",
            "频道106" : "6频道",
            "频道107" : "公共新农村",
            "频道108" : "浙江少儿",
            #"频道109" : "留学世界",
            #"频道110" : "浙江国际",
            #"频道111" : "好易购"
        }
        self.ExcludeName = ('频道109', '频道1[1,2,3]\w*', '频道[23].*')
        self.area = '中国-淅江省'

class ParserNBLive(ParserTVIELive):
    def __init__(self):
        self.tvName = '宁波电视台'
        super().__init__('ming-api.nbtv.cn')
        self.Alias = {
            'nbtv1直播' : '宁波-新闻综合',
            'nbtv2直播' : '宁波-社会生活',
            'nbtv3直播' : '宁波-都市文体',
            'nbtv4直播' : '宁波-影视剧',
            'nbtv5直播' : '宁波-少儿',
        }
        self.ExcludeName = ('.*广播', '阳光调频', 'sunhotline')
        self.area = '中国-淅江省-宁波市'

class ParserUCLive(ParserTVIELive):
    def __init__(self):
        self.tvName = '新疆电视台'
        super().__init__('epgsrv01.ucatv.com.cn')
        self.ExcludeName = ('.*广播', '106点5旅游音乐', '天山云LIVE')
        self.area = '中国-新疆'

# 文本导入
class ParserTextLive(LivetvParser):
    def __init__(self):
        super().__init__()
        self.cmd['name']    = 'live_engine_parser'
        self.cmd['source'] = 'http://files.cloudtv.bz/media/20130927.txt'

    def CmdParser(self, js):
        db = DB()
        text = js['data']
        text = text.replace('（华侨直播）', '')
        text = text.replace('【夜猫】', '')
        text = text.replace('[腾讯]', '')
        playlist = text.split('\n')

        tv = {}
        for t in playlist:
            t = t.strip()
            if t[0:1] != '#':
                v = re.findall('(.*)((http://|rtmp://|rtsp://).*)', t)
                if v and len(v[0]) >= 2:
                    key = v[0][0].strip()
                    value = v[0][1].strip()
                    if key not in tv:
                        tv[key] = []
                    x = {}
                    x['name'], x['order'] = GetNameByUrl(value)
                    x['directPlayUrl'] = value

                    if x not in tv[key]:
                        tv[key].append(x)
        for k,v in list(tv.items()):
            if k and v:
                v.sort(key=lambda x:x['order'])
                album  = LiveAlbum()
                album.cid         = 200
                album.vid         = k
                album.playlistid  = k
                album.pid         = k
                album.albumName   = k
                album.categories  = self.tvCate.GetCategories(k)
                album.sources     = v
                album.totalSet    = len(v)
                db._save_update_append(None, album)

# LiveTV 搜索引擎
class LiveEngine(VideoEngine):
    def __init__(self, command):
        super().__init__(command)
        self.engine_name = 'LiveEngine'
        self.albumClass = LiveAlbum

        # 引擎菜单
        self.menu = {
            '直播' : LiveVideoMenu
        }

        self.parserList = {
            ParserLetvLive(),
            ParserSohuLive(),
            ParserTextLive(),
            ParserZJLive(),
            ParserNBLive(),
            ParserHangZhouLive(),
            ParserUCLive(),
            ParserWenZhouLive(),
        }

