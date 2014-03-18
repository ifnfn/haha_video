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
            "绍兴影视娱乐" : '绍兴-文化影视',
            "绍兴公共频道" : '绍兴-公共频道',
            "绍兴新闻综合" : '绍兴-新闻综合',
            "宁波台-少儿频道" : "宁波-少儿",
            "宁波台-社会生活频道" : "宁波-社会生活",
            "宁波台-影视频道"     : "宁波-影视",
            "宁波台-新闻综合频道" : "宁波-新闻综合",
            "宁波台-文化娱乐频道" : "宁波-都市文体",
            "南宁公共频道" : "南宁-公共频道",
            "南宁影视娱乐" : "南宁-影视娱乐",
            "南宁台-都市生活" : "南宁-都市生活",
            "南宁台-老友LIVE" : "南宁-老友LIVE",
            "南宁台-新闻综合" : "南宁-新闻综合",
            "济南娱乐" : "济南-娱乐",
            "大丰生活综艺频道" : "大丰-生活综艺",
            "大丰新闻综合频道" : "大丰-新闻综合",
            "大丰影视剧频道" : "大丰-影视剧",
            "邯郸新闻综合频道" : "邯郸-新闻综合",
            "荆州垄上频道" : "荆州-垄上频道",
            "荆州社区频道" : "荆州-社区频道",
            "荆州新闻频道" : "荆州-新闻频道",
            "荆州专题频道" : "荆州-专题频道",
            "兰州睛彩兰州" : "兰州-睛彩兰州",
            "南昌都市频道" : "南昌-都市频道",
            "南昌法制频道" : "南昌-法制频道",
            "南昌公共频道" : "南昌-公共频道",
            "南昌新闻综合频道" : "南昌-新闻综合",
            "安阳法制频道" : "安阳-法制频道",
            "安阳睛彩安阳" : "安阳-睛彩安阳",
            "安阳科教频道" : "安阳-科教频道",
            "安阳图文生活频道" : "安阳-图文生活",
            "安阳新闻综合" : "安阳-新闻综合",
            "贵阳都市频道" : "贵阳-都市频道",
            "贵阳法制频道" : "贵阳-法制频道",
            "贵阳经济生活频道" : "贵阳-经济生活",
            "贵阳新闻综合频道" : "贵阳-新闻综合",
            "太原百姓频道" : "太原-百姓频道",
            "太原法制频道" : "太原-法制频道",
            "太原家庭消费频道" : "太原-家庭消费",
            "太原文体频道" : "太原-文体频道",
            "太原新闻频道" : "太原-新闻频道",
            "太原影视频道" : "太原-影视频道",
            "湖北台-湖北卫视" : "湖北卫视",
            "湖北台-公共频道" : "湖北-公共频道",
            "湖北台-教育频道" : "湖北-教育频道",
            "湖北台-经济频道" : "湖北-经济频道",
            "湖北台-体育频道" : "湖北-体育频道",
            "湖北台-影视频道" : "湖北-影视频道",
            "湖北台-综合频道" : "湖北-综合频道",
            "济南台-济南都市" : "济南-济南都市",
            "济南台-济南商务" : "济南-济南商务",
            "济南台-济南少儿" : "济南-济南少儿",
            "济南台-济南生活" : "济南-济南生活",
            "济南台-济南新闻" : "济南-济南新闻",
            "济南台-济南影视" : "济南-济南影视",
            "武汉台-武汉科教" : "武汉-武汉科教",
            "武汉台-武汉少儿" : "武汉-武汉少儿",
            "武汉台-武汉文体" : "武汉-武汉文体",
            "武汉台-武汉新闻" : "武汉-武汉新闻",
            "珠海台-珠海一台" : "珠海一台",
            "珠海台-珠海二台" : "珠海二台",
            "珠海台-综合" : "珠海-综合",
            "石家庄都市频道" : "石家庄-都市频道",
            "石家庄新闻频道" : "石家庄-新闻频道",
            "石家庄影视频道" : "石家庄-影视频道",
            "石家庄娱乐频道" : "石家庄-娱乐频道",
            "苏州新闻综合频道" : "苏州-新闻综合",
            "泰州台-泰州新闻" : "泰州-泰州新闻",
            "柳州台-公共频道" : "柳州-公共频道",
            "柳州台-科教频道" : "柳州-科教频道",
            "柳州台-新闻频道" : "柳州-新闻频道",
            "深圳台-财经生活频道" : "深圳-财经生活",
            "深圳台-电视剧频道" : "深圳-电视剧",
            "深圳台-都市频道" : "深圳-都市频道",
            "深圳台-DV生活" : "深圳-DV生活",
            "深圳台-高清HD" : "深圳-高清HD",
            "深圳台-公共频道" : "深圳-公共频道",
            "深圳台-少儿频道" : "深圳-少儿频道",
            "深圳台-深圳卫视" : "深圳卫视",
            "深圳台-体育健康频道" : "深圳-体育健康",
            "深圳台-娱乐频道" : "深圳-娱乐频道",
            "烟台台-烟台一台" : "烟台一台",
            "西宁台-文化先锋" : "西宁-文化先锋",
            "西宁台-西宁生活" : "西宁-西宁生活",
            "西宁台-西宁新闻" : "西宁-西宁新闻",
            "西宁台-夏都房车" : "西宁-夏都房车",
            "襄阳精彩频道" : "襄阳-精彩频道",
            "郑州都市生活" : "郑州-都市生活",
        }

        self.ExcludeName = ['网络春晚', '济南', '邯郸', '西安', '南通', '南宁', '安阳', '大连', '鄂尔多斯']

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
