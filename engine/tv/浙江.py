#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

import tornado.escape

from kola import utils, LivetvMenu

from .common import PRIOR_DEFTV, PRIOR_UCTV
from .livetvdb import LivetvParser, LivetvDB
from .m2oplayer import M2OLivetvParser
from .tvielivetv import ParserTVIELivetv


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

# 浙江电视台
class ParserZJLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.cztv.com')
        self.tvName = '浙江电视台'
        self.area = '中国,浙江'
        self.order = PRIOR_DEFTV

        self.Alias = {
            "频道101" : "浙江卫视",
            "频道102" : "浙江-钱江频道",
            "频道103" : "浙江-经视",
            "频道104" : "浙江-教育科技",
            "频道105" : "浙江-影视",
            "频道106" : "浙江-6频道",
            "频道107" : "浙江-公共新农村",
            "频道108" : "浙江-少儿",
            # "频道109" : "留学世界",
            # "频道110" : "浙江国际",
            # "频道111" : "好易购"
        }
        self.ExcludeName = ['频道109', '频道1[1,2,3]\w*', '频道[23].*']


class ParserTVIELivetv2(LivetvParser):
    def __init__(self, url):
        super().__init__()
        self.base_url = url
        self.order = PRIOR_UCTV
        self.area = ''

        self.cmd['source'] = 'http://' + self.base_url + '/api/getChannels'
        self.Referer = ''

    def CmdParser(self, js):
        db = LivetvDB()

        jdata = tornado.escape.json_decode(js['data'])

        for x in jdata['result']:
            if 'group_names' in x and x['group_names'] == 'audio':
                continue
            name = ''
            if 'name' in x: name = x['name']
            if 'display_name' in x: name = x['display_name']

            album = self.NewAlbum(name)
            if album == None:
                continue

            v = album.NewVideo()
            v.order = self.order
            v.name = self.tvName

            url = 'http://' + self.base_url + '/api/getCDNByChannelId/' + x['id']
            if self.base_url in ['api.cztv.com']:
                url += '?domain=' + self.base_url

            v.vid = utils.getVidoId(url)

            v.SetVideoUrlScript('default', 'nbtv', [url, x['id'], self.Referer])

            url = 'http://%s/api/getEPGByChannelTime/%s' % (self.base_url, x['id'])
            v.info = utils.GetScript('tvie', 'get_channel', [url, x['id']])

            album.videos.append(v)
            db.SaveAlbum(album)

    def GetCategories(self, name):
        return self.tvCate.GetCategories(name)
# 宁波电视台
class ParserNBLivetv(ParserTVIELivetv2):
    def __init__(self):
        super().__init__('ming-api.nbtv.cn')
        self.tvName = '宁波电视台'
        self.area = '中国,浙江,宁波'

        self.Alias = {
            'nbtv1直播' : '宁波-新闻综合',
            'nbtv2直播' : '宁波-社会生活',
            'nbtv3直播' : '宁波-都市文体',
            'nbtv4直播' : '宁波-影视',
            'nbtv5直播' : '宁波-少儿',
        }
        self.ExcludeName = ['.*广播', '阳光调频', 'sunhotline']

# 义乌电视台
class ParserYiwuLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('live-01.ywcity.cn')
        self.tvName = '义乌电视台'
        self.area = '中国,浙江,金华,义乌'
        self.Alias = {
            "新闻综合" : '义乌-新闻综合',
            "商贸频道" : '义乌-商贸频道',
        }
        self.ExcludeName = ['FM']

# 绍兴电视台
class ParserShaoxinLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('115.239.168.72')
        self.tvName = '绍兴电视台'
        self.area = '中国,浙江,绍兴'

        self.Alias = {
            "新闻综合频道" : '绍兴-新闻综合',
            "公共频道"     : '绍兴-公共频道',
            "文化影视频道" : '绍兴-文化影视',
        }
        self.ExcludeName = ['.*广播', '直播']

# 温州电视台
class ParserWenZhouLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '温州电视台'
        self.area = '中国,浙江,温州'

        self.cmd['source'] = 'http://tv.dhtv.cn'
        self.cmd['regular'] = ['(<a href=.* data-source=.*</a>)']
        self.Alias = {}
        self.ExcludeName = []

    def CmdParser(self, js):
        db = LivetvDB()

        ch_list = re.findall('data-source="(.*?)" data-id="(.*?)">(.*?)<i>', js['data'])
        for source, data_id, name in ch_list:
            name = '温州-' + name
            album = self.NewAlbum(name)

            v = album.NewVideo()
            v.vid = utils.getVidoId(js['source'] + '/' + source)
            v.order = 2
            v.name = self.tvName

            v.SetVideoUrlScript('default', 'wztv', ['http://www.dhtv.cn/static/js/tv.js?acm', source])
            v.info = utils.GetScript('wztv', 'get_channel', [data_id])

            album.videos.append(v)
            db.SaveAlbum(album)

class ZheJianLiveTV(LivetvMenu):
    '''
    浙江省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [
            ParserZJLivetv,      # 浙江省台
            ParserNBLivetv,      # 宁波
            ParserYiwuLivetv,    # 义乌
            ParserShaoxinLivetv, # 绍兴
            ParserHangZhouLivetv,# 杭州台
            ParserWenZhouLivetv, # 温州
        ]
