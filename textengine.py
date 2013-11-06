#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback
import re
import tornado.escape

from engine import VideoBase, AlbumBase, VideoMenuBase, VideoEngine, Template
from utils import log, autostr, GetNameByUrl

#================================= 以下是视频的搜索引擎 =======================================

# 更新节目的播放信息
class TemplateTextvInfo(Template):
    def __init__(self, menu):
        cmd = {
            'name'   : 'text_livetv_list',
            'source' : 'http://files.cloudtv.bz/media/20130927.txt',
        }
        super().__init__(menu.command, cmd)

class TextvVideo(VideoBase):
    def __init__(self, js = None):
        super().__init__(js)

    def GetVideoPlayUrl(self, definition=0):
        vid = self.GetVid(definition)
        if vid:
            return 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
        else:
            return ''

class TextvAlbum(AlbumBase):
    def __init__(self, parent):
        AlbumBase.__init__(self, parent)
        self.VideoClass = TextvVideo

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        pass

class TextvTV(VideoMenuBase):
    def __init__(self, name, engine):
        VideoMenuBase.__init__(self, name, engine)
        self.homePage    = ''
        self.HomeUrlList = []
        self.albumClass  = TextvAlbum
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
        for k,v in self.filter['类型'].items():
            x = re.findall(v, name)
            if x:
                ret.append(k)
        return ret

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        TemplateTextvInfo(self).Execute()

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
class TextvEngine(VideoEngine):
    def __init__(self, db, command):
        VideoEngine.__init__(self, db, command)

        self.engine_name = 'TextvEngine'
        self.albumClass = TextvAlbum
        self.videoClass = TextvVideo

        # 引擎主菜单
        self.menu = {
            '直播'   : TextvTV
        }

        self.parserList = {
                   'text_livetv_list' : self._CmdParserLiveTVList,
        }

    # 从分页的页面上解析该页上的节目
    # videolist
    def _CmdParserLiveTVList(self, js):
        text = js['data']
        text = text.replace('（华侨直播）', '')
        text = text.replace('【夜猫】', '')
        text = text.replace('[腾讯]', '')
        playlist = text.split('\n')

        tvmenu = TextvTV('直播', self)

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
                    x['name'] = GetNameByUrl(value)
                    x['directPlayUrl'] = value
                    tv[key].append(x)
        for k,v in list(tv.items()):
            album  = self.NewAlbum()
            album.cid         = 200
            album.vid         = k
            album.playlistid  = k
            album.pid         = k
            album.albumName   = k
            album.categories  = tvmenu.GetCategories(k)
            album.sources = v
            self._save_update_append(None, album)

    def _save_update_append(self, sets, album, _filter={}, upsert=True):
        if album:
            self.db.SaveAlbum(album, _filter, upsert)
        if sets:
            sets.append(album)
