#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback
import re
import tornado.escape
import hashlib

from engine import VideoBase, AlbumBase, VideoMenuBase, VideoEngine, Template
from utils import json_get, GetNameByUrl
import tv

global Debug
Debug = True

class LiveVideo(VideoBase):
    def __init__(self, js = None):
        super().__init__(js)

    def GetVideoPlayUrl(self, definition=0):
        pass

class LiveAlbum(AlbumBase):
    def __init__(self, parent):
        super().__init__(parent)
        self.albumPageUrl = ''

        self.videoClass = LiveVideo

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

class LiveVideoMenu(VideoMenuBase):
    def __init__(self, name, engine):
        super().__init__(name, engine)
        self.tvCate = tv.TVCategory()
        self.homePage    = ''
        self.albumClass  = LiveAlbum
        self.cid = 200
        self.filter = {
            '类型': {
                '卫视台':1,
                '地方台':2,
                '央视台':3,
                '境外台':4,
            }
        }
        self.cmd = {
            'menu' :  name,
            'name' : 'livetv_list',
            'cache' : False or Debug
        }

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        if self.command:
            self.command.AddCommand(self.cmd)
            self.command.Execute()

    def CmdParser(self, js):
        pass

# 乐视直播电视
class LetvLiveMenu(LiveVideoMenu):
    def __init__(self, name, engine):
        super().__init__(name, engine)
        self.cmd['source']  = 'http://www.leshizhibo.com/channel/index.php'
        self.cmd['regular'] = ["<dt>(<a title=.*</a>)</dt>"]

    def CmdParser(self, js):
        ret = []

        playlist = js['data'].split("</a>")

        for t in playlist:
            #print(t)
            x = re.findall('<a title="(.*)" href=".*/channel/(.*)" target="_blank"><img alt=.* src="(.*)"><span class', t)
            if x:
                name = x[0][0]
                vid = x[0][1]
                print(name, x[0][1], x[0][2])

                album  = self.NewAlbum()
                album.cid         = 200
                album.vid         = hashlib.md5(name.encode()).hexdigest()[16:]
                album.playlistid  = ''
                album.pid         = ''
                album.albumName   = name
                album.categories = self.tvCate.GetCategories(name)

                v = album.NewVideo()
                v.playUrl = 'http://live.gslb.letv.com/gslb?stream_id=%s&ext=m3u8&sign=live_tv&format=1' % vid
                v.playlistid = album.playlistid
                # v.pid = album.vid
                # v.cid = album.cid
                v.vid = hashlib.md5(v.playUrl.encode()).hexdigest()[24:]
                v.largePicUrl = x[0][2]
                v.priority = 1
                v.name = "乐视"
                v.script = {
                    'script' : 'letv',
                    'parameters' : [v.playUrl]
                }

                album.videos.append(v)
                self.engine._save_update_append(ret, album)
        return ret

# 搜狐直播电视
class SohuLiveMenu(LiveVideoMenu):
    def __init__(self, name, engine):
        super().__init__(name, engine)
        self.cmd['source'] = 'http://tvimg.tv.itc.cn/live/top.json'

    def CmdParser(self, js):
        ret = []

        '''
        {'cu': 249, 'id': 147,
            'programaId': 76372, 'percentage': 0.1530424093423479,
            'enName': 'zjtv', 'name': '浙江卫视',
            'ico': 'http://i2.itc.cn/20120119/2cea_d8216f64_5ba9_b7dd_4b3d_f2ea360e895f_17.png',
            'videoId': 136573770, 'videoName': '浙江新闻联播'}
        '''
        tvlist = tornado.escape.json_decode(js['data'])
        for v in tvlist['attachment']:
            name = json_get(v, 'name', '')
            pid = json_get(v, 'id', '')
            vid = hashlib.md5(name.encode()).hexdigest()[16:]
            album  = self.NewAlbum()
            album.cid         = 200
            album.albumName   = json_get(v, 'name', '')
            album.vid         = vid
            #album.enAlbumName = json_get(v, 'enName', '')
            album.smallPicUrl = json_get(v, 'ico', '')

            v = album.NewVideo()
            # v.pid = album.vid
            # v.cid = album.cid
            v.vid = hashlib.md5(v.playUrl.encode()).hexdigest()[24:]
            v.playUrl = 'http://live.tv.sohu.com/live/player_json.jhtml?encoding=utf-8&lid=%s&type=1' % pid
            v.priority = 2
            v.name = "搜狐"
            v.script = {
                'script' : 'sohutv',
                'parameters' : [v.playUrl]
            }
            album.videos.append(v)
            self.engine._save_update_append(ret, album)

        return ret

class WenZhouLiveMenu(LiveVideoMenu):
    def __init__(self, name, engine):
        super().__init__(name, engine)
        self.cmd['source'] = 'http://v.dhtv.cn/tv/'
        self.cmd['regular'] = ['(http://v.dhtv.cn/tv/\?channal=.*</a></li>)']
        self.Alias = {}
        self.ExcludeName = ()

    def CmdParser(self, js):
        ret = []
        ch_list = re.findall('(http://v.dhtv.cn/tv/\?channal=(.+))\">(.*)</a></li>', js['data'])
        for u, source, name in ch_list:
            vid = hashlib.md5(name.encode()).hexdigest()[16:]
            album  = self.NewAlbum()
            album.cid         = 200
            album.albumName   = name
            album.vid         = vid

            v = album.NewVideo()
            # v.pid = album.vid
            # v.cid = album.cid
            v.vid = hashlib.md5(v.playUrl.encode()).hexdigest()[24:]
            v.priority = 2
            v.playUrl = u
            v.name = "dhtv"
            v.script = {
                'script' : 'wztv',
                'parameters' : ['http://www.dhtv.cn/static/??js/tv.js?acm', source]
            }
            album.videos.append(v)
            self.engine._save_update_append(ret, album)


class TVIELiveMenu(LiveVideoMenu):
    def __init__(self, name, engine, url):
        super().__init__(name, engine)
        self.base_url = url
        self.cmd['source'] = 'http://' + self.base_url + '/api/getChannels'
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

    def CmdParser(self, js):
        ret = []
        jdata = tornado.escape.json_decode(js['data'])
        #print(json.dumps(jdata, indent=4, ensure_ascii=False))
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

                album = self.NewAlbum()
                album.cid       = 200
                album.albumName = name
                album.vid       = hashlib.md5(album.albumName.encode()).hexdigest()[16:]

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
                self.engine._save_update_append(ret, album)

        except:
            t, v, tb = sys.exc_info()
            print("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))


class ZJLiveMenu(TVIELiveMenu):
    def __init__(self, name, engine):
        self.tvName = '浙江电视台'
        super().__init__(name, engine, 'api.cztv.com')
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

class NBLiveMenu(TVIELiveMenu):
    def __init__(self, name, engine):
        self.tvName = '宁波电视台'
        super().__init__(name, engine, 'ming-api.nbtv.cn')
        self.Alias = {
            'nbtv1直播' : '宁波-新闻综合',
            'nbtv2直播' : '宁波-社会生活',
            'nbtv3直播' : '宁波-都市文体',
            'nbtv4直播' : '宁波-影视剧',
            'nbtv5直播' : '宁波-少儿',
        }

        self.ExcludeName = ('.*广播', '阳光调频', 'sunhotline')

class UCLiveMenu(TVIELiveMenu):
    def __init__(self, name, engine):
        self.tvName = '新疆电视台'
        super().__init__(name, engine, 'epgsrv01.ucatv.com.cn')
        self.ExcludeName = ('.*广播', '106点5旅游音乐', '天山云LIVE')

# 文本导入
class TextLiveMenu(LiveVideoMenu):
    def __init__(self, name, engine):
        super().__init__(name, engine)
        self.cmd['source'] = 'http://files.cloudtv.bz/media/20130927.txt'

    def CmdParser(self, js):
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
                album  = self.NewAlbum()
                album.cid         = 200
                album.vid         = k
                album.playlistid  = k
                album.pid         = k
                album.albumName   = k
                album.categories  = self.tvCate.GetCategories(k)
                album.sources     = v
                album.totalSet    = len(v)
                self.engine._save_update_append(None, album)


# Letv 搜索引擎
class LiveEngine(VideoEngine):
    def __init__(self, db, command):
        super().__init__(db, command)
        self.engine_name = 'LiveEngine'
        self.albumClass = LiveAlbum
        self.videoClass = LiveVideo

        # 引擎主菜单
        self.menu = {
            'Letv直播'   : LetvLiveMenu,
            'Sohu直播'   : SohuLiveMenu,
            #'text直播'   : TextLiveMenu,
            '浙江电视台'    : ZJLiveMenu,
            '宁波电视台'    : NBLiveMenu,
            '新疆电视台'    : UCLiveMenu,
            '温州电视台'    : WenZhouLiveMenu,
        }

        self.parserList = {
                'livetv_list' : self._CmdParserLiveTVList
        }

    def _CmdParserLiveTVList(self, js):
        menuName = js['menu']
        if menuName in self.menu:
            menu = self.menu[menuName]
            if type(menu) == type:
                return menu(menuName, self).CmdParser(js)
            else:
                return menu.CmdParser(js)
        else:
            return []
