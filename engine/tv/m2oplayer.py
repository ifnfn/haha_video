#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from xml.etree import ElementTree

from kola import LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser, LivetvDB


class M2OLivetvParser(LivetvParser):
    def __init__(self):
        super().__init__()

        self.order = PRIOR_DEFTV
        self.baseUrl = ''
        self.channelIds = ()

    def Execute(self):
        for i in self.channelIds:
            self.cmd['source'] = 'http://%s/m2o/player/channel_xml.php?id=%d&url=%s' % (self.baseUrl, i, self.baseUrl)
            self.cmd['channel_id'] = i
            self.command.AddCommand(self.cmd)

        self.cmd = None
        self.command.Execute()

    def CmdParser(self, js):
        url = js['source']
        text = js['data']
        root = ElementTree.fromstring(text)

        albumName = root.attrib['name']
        if albumName == '':
            return

        ok = False
        for p in root:
            if p.tag == 'video':
                for item in p.getchildren():
                    if 'url' in item.attrib:
                        ok = True
                        break

        if ok == False:
            return

        album  = self.NewAlbum(albumName)

        if album == None:
            return

        videoUrl,_ = re.subn('^http://', 'm2otv://', url)
        v = album.NewVideo(videoUrl)
        if v:
            album.videos.append(v)
            LivetvDB().SaveAlbum(album)

# 安徽电视台
class ParserAnhuiLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '安徽电视台'
        self.area = '中国,安徽'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '安徽公共' : '安徽-公共频道',
            '科教频道' : '安徽-科教频道',
            '综艺频道' : '安徽-综艺频道',
            '影视频道' : '安徽-影视频道',
            '经济生活' : '安徽-经济生活',
            '安徽国际' : '安徽-国际频道',
            '人物频道' : '安徽-人物频道',
        }

        self.ExcludeName = []
        self.baseUrl = 'www.ahtv.cn'
        self.channelIds = (2, 3, 4, 5, 6, 7, 8, 9)

# 杭州电视台
class ParserHangZhouLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '杭州电视台'
        self.area = '中国,浙江,杭州'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '西湖明珠' : '杭州-西湖明珠',
            '杭州导视' : '杭州-导视',
            '杭州房产' : '杭州-房产',
            '杭州少儿' : '杭州-少儿',
            '杭州生活' : '杭州-生活',
            '杭州综合' : '杭州-综合'
        }
        self.ExcludeName = []

        self.baseUrl = 'www.hoolo.tv'
        self.channelIds = (1, 2, 3, 5, 30, 31)

# 济南电视台
class ParserJiNanLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '济南电视台'
        self.area = '中国,山东,济南'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '新闻频道' : '济南-新闻频道',
            '都市频道' : '济南-都市频道',
            '影视频道' : '济南-影视频道',
            '娱乐频道' : '济南-娱乐频道',
            '生活频道' : '济南-生活频道',
            '商务频道' : '济南-商务频道',
            '少儿频道' : '济南-少儿频道',
            '新闻高清' : '济南-新闻高清'
        }

        self.ExcludeName = ['济南都市', '济南商务', '济南少儿', '济南生活', '济南新闻', '济南影视', '济南娱乐'] # 与 VST 重复
        self.baseUrl = 'www.ijntv.cn'
        self.channelIds = (5, 6, 7, 8, 9, 10, 11, 13)

# 盐城电视台
class ParserYanChenLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '盐城电视台'
        self.area = '中国,江苏,盐城'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '盐城电视一套' : '盐城-电视一套',
            '盐城电视二套' : '盐城-电视二套',
            '盐城电视三套' : '盐城-电视三套',
            '七一小康频道' : '盐城-七一小康'
        }

        self.baseUrl = 'www.0515yc.cn'
        self.channelIds = (1, 2, 3, 4)

# 长春电视台
class ParserChangChongLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '长春电视台'
        self.area = '中国,吉林,长春'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '长春1频道': '长春-综合频道',
            '长春2频道': '长春-娱乐频道',
            '长春3频道': '长春-市民频道',
            '长春4频道': '长春-商业频道',
            '长春5频道': '长春-新知频道',
        }

        self.baseUrl = 'www.chinactv.com'
        self.channelIds = (1, 2, 3, 4, 5)

# 福建电视台
class ParserFuJianLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '福建电视台'
        self.area = '中国,福建'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '海峡卫视': '海峡卫视',
            '东南卫视': '东南卫视',
            '综合频道': '福建-综合频道',
            '公共频道': '福建-公共频道',
            '电视剧频道': '福建-电视剧',
            '都市时尚': '福建-都市时尚',
            '经济生活': '福建-经济生活',
            '体育频道': '福建-体育频道',
            '新闻综合': '福建-新闻频道'
        }

        self.baseUrl = 'v.fjtv.net'
        self.channelIds = (3, 4, 5, 6, 7, 8, 9, 10, 11)

# 银川电视台
class ParserYingChuangvLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '银川电视台'
        self.area = '中国,甘肃,银川'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '银川公共': '银川-公共',
            '银川生活': '银川-生活'
        }

        self.baseUrl = 'www.ycgbtv.com.cn'
        self.channelIds = (1, 2)

class M2OLiveTV(LivetvMenu):
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserAnhuiLivetv,
                                ParserJiNanLivetv,
                                ParserYanChenLivetv,
                                ParserChangChongLivetv,
                                ParserFuJianLivetv,
                                ParserYingChuangvLivetv
                                ]

