#! /usr/bin/python3
# -*- coding: utf-8 -*-

from xml.etree import ElementTree

from .livetvdb import LivetvParser, LivetvDB
from kola import utils, LivetvMenu

from .common import PRIOR_CUTV


class ParserCutvLivetv(LivetvParser):
    def __init__(self, station=None, tv_id=None):
        super().__init__()
        self.order = PRIOR_CUTV
        self.area = ''
        self.Alias = {
            "绍兴影视娱乐" : '绍兴台-文化影视',
            "绍兴公共频道" : '绍兴台-公共频道',
            "绍兴新闻综合" : '绍兴台-新闻综合',
            "宁波台-少儿频道" : "宁波台-少儿",
            "宁波台-社会生活频道" : "宁波台-社会生活",
            "宁波台-影视频道"     : "宁波台-影视",
            "宁波台-新闻综合频道" : "宁波台-新闻综合",
            "宁波台-文化娱乐频道" : "宁波台-都市文体",
            "南宁公共频道" : "南宁台-公共频道",
            "南宁影视娱乐" : "南宁台-影视娱乐",
            "济南娱乐" : "济南台-娱乐",
            "大丰生活综艺频道" : "大丰台-生活综艺",
            "大丰新闻综合频道" : "大丰台-新闻综合",
            "大丰影视剧频道" : "大丰台-影视剧",
            "邯郸新闻综合频道" : "邯郸台-新闻综合",
            "荆州垄上频道" : "荆州台-垄上频道",
            "荆州社区频道" : "荆州台-社区频道",
            "荆州新闻频道" : "荆州台-新闻频道",
            "荆州专题频道" : "荆州台-专题频道",
            "兰州睛彩兰州" : "兰州台-睛彩兰州",
            "南昌都市频道" : "南昌台-都市频道",
            "南昌法制频道" : "南昌台-法制频道",
            "南昌公共频道" : "南昌台-公共频道",
            "南昌新闻综合频道" : "南昌台-新闻综合",
            "安阳法制频道" : "安阳台-法制频道",
            "安阳睛彩安阳" : "安阳台-睛彩安阳",
            "安阳科教频道" : "安阳台-科教频道",
            "安阳图文生活频道" : "安阳台-图文生活",
            "安阳新闻综合" : "安阳台-新闻综合",
            "贵阳都市频道" : "贵阳台-都市频道",
            "贵阳法制频道" : "贵阳台-法制频道",
            "贵阳经济生活频道" : "贵阳台-经济生活",
            "贵阳新闻综合频道" : "贵阳台-新闻综合",
            "太原百姓频道" : "太原台-百姓频道",
            "太原法制频道" : "太原台-法制频道",
            "太原家庭消费频道" : "太原台-家庭消费",
            "太原文体频道" : "太原台-文体频道",
            "太原新闻频道" : "太原台-新闻频道",
            "太原影视频道" : "太原台-影视频道",
            "湖北台-湖北卫视" : "湖北卫视",
        }

        if station == None:
            self.cmd['step'] = 1
            self.cmd['source'] = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=tv_live'
        elif station and id:
            self.tvName = station

            self.cmd['step'] = 2
            self.cmd['station'] = station
            self.cmd['id'] = tv_id
            self.cmd['source'] = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=channel_prg_list&tv_id=' + utils.autostr(tv_id)

    def CmdParser(self, js):
        if js['step'] == 1:
            self.CmdParserAll(js)
        elif js['step'] == 2:
            self.CmdParserTV(js)

    def CmdParserAll(self, js):
        text = js['data']
        root = ElementTree.fromstring(text)
        for p in root.findall('tv'):
            ParserCutvLivetv(p.findtext('tv_name'), p.findtext('tv_id')).Execute()

    def CmdParserTV(self, js):
        db = LivetvDB()
        text = js['data']
        tv_id = js['id']

        self.area = self.city.GetCity(js['station'])
        root = ElementTree.fromstring(text)
        for p in root.findall('channel'):
            name = p.findtext('channel_name')
            channel_id = p.findtext('channel_id')

            album  = self.NewAlbum(name)
            if album == None:
                continue

            album.channel_id  = channel_id
            album.largePicUrl = p.findtext('thumb')

            v = album.NewVideo()
            v.order = self.order
            v.name     = js['station']

            v.SetVideoUrlScript('default', 'cutv', [tv_id, channel_id])

            url = p.findtext('mobile_url')
            x = url.split('/')
            if len(x) > 4:
                v.vid  = x[4]
                v.info = utils.GetScript('cutv', 'get_channel',[v.vid])

            album.videos.append(v)
            db.SaveAlbum(album)

class CuLiveTV(LivetvMenu):
    '''
    联合电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserCutvLivetv]
