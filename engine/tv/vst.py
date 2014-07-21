#! /usr/bin/python3
# -*- coding: utf-8 -*-

import base64
import re

from kola import LivetvMenu

from .common import PRIOR_VST, PRIOR_LETV, PRIOR_IMGO, PRIOR_CNTV
from .livetvdb import LivetvParser


class ParserVstLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = ''
        self.order = PRIOR_VST
        self.Alias = {
            '珠海2台' : '珠海-生活服务',
            '珠海1台' : '珠海-新闻综合',
            '浙江钱江' : '浙江-钱江频道',
            '钱江都市' : '浙江-钱江频道',
            '浙江6' : '浙江-6频道',
            '杭州明珠' : '杭州-西湖明珠',
            '吉林公共' : '吉林-公共新闻',
            '第一财经' : '上海-第一财经',
            '江西经视' : '江西-经济生活',
            '江苏体育休闲' : '江苏-休闲',
            '凤凰卫视香港台' : '凤凰卫视-香港台',
            '凤凰卫视中文台' : '凤凰卫视-中文台',
            '凤凰卫视资讯台' : '凤凰卫视-资讯台',
            'CCTV1 综合频道' : 'CCTV-1 综合',
            'CCTV2 财经频道' : 'CCTV-2 财经',
            'CCTV3 综艺频道' : 'CCTV-3 综艺',
            'CCTV4 中文国际' : 'CCTV-4 中文国际',
            'CCTV5 体育频道' : 'CCTV-5 体育',
            'CCTV6 电影频道' : 'CCTV-6 电影',
            'CCTV7 军事农业' : 'CCTV-7 军事农业',
            'CCTV8 电视剧'   : 'CCTV-8 电视剧',
            'CCTV9 中文记录' : 'CCTV-9 纪录',
            'CCTV10 科教频道' : 'CCTV-10 科教',
            'CCTV11 戏曲频道' : 'CCTV-11 戏曲',
            'CCTV12 社会与法' : 'CCTV-12 社会与法',
            'CCTV13 新闻频道' : 'CCTV-13 新闻',
            'CCTV14 少儿频道' : 'CCTV-14 少儿',
            'CCTV15 音乐频道' : 'CCTV-15 音乐',
            'CCTV5+体育赛事' : 'CCTV5+ 体育赛事',
            'CCTV9 海外记录' : 'CCTV-9 海外纪录',
            'CCTV4 中文国际(美洲)' : 'CCTV-4 中文国际(美洲)',
            'CCTV4 中文国际(欧洲)' : 'CCTV-4 中文国际(欧洲)',
            'HD' : '-高清'
        }
        self.cmd['cache'] = True
        self.cmd['source'] = 'http://ott.52itv.cn/vst_tvlist?app=egreat&name=mygica%20TV%20MX%20box&ver=4.1.2&uuid=00000000-71b9-5e32-0033-c5870033c587&mac=000102030406'
        self.ExcludeName = ['电影片花', '法国1', '高尔夫.网球', '高尔夫', '周星驰专区', 'CCTV-4 中文国际(欧洲)', 'CCTV-4 中文国际(美洲)', 'CCTV ',
                            '经典电影', 'CCTV4 中文国际(美洲)', 'CCTV4 中文国际(欧洲)',
                            '安庆'
                            ]
        self.vtv_order = 0

    def GetChannel(self, name):
        #channels = ['浙江', '杭州', '宁波', '绍兴', '温州', '义乌']
        #channels = ['山东', '济南']
        channels = ['.*']
        for p in list(channels):
            if re.findall(p, name):
                return name

    def GetTVOrder(self, url):
        if url.find('letv', 0) >= 0:
            return PRIOR_LETV, 'VLTV'
        elif url.find('imgotv', 0) >= 0:
            return PRIOR_IMGO, 'VITV'
        elif url.find('pa://', 0) >= 0:
            return PRIOR_CNTV, 'VCNTV'

        self.vtv_order += 1
        return self.order + self.vtv_order, 'VTV'

    def CmdParser(self, js):
        data = js['data']
        data,_ = re.subn('[*]', '/', data)
        data,_ = re.subn('[!]', '+', data)
        data,_ = re.subn('[,]', '=', data)
        data = base64.decodebytes(data.encode()).decode()
        try:
            f = open('/tmp/vst', 'wb')
            f.write(data.encode())
            f.close()
        except:
            pass

        playlist = data.split("\n")

        for ch_text in playlist:
            ch_list = ch_text.split(',')

            albumName = ch_list[0]

            if self.GetChannel(albumName) == None:
                continue

            hrefs = ch_list[1]

            self.vtv_order = 0

            tvUrl = []
            for u in hrefs.split('#'):
                if hrefs.find('imgotv') >= 0:
                    continue
                tvUrl.append(u)

            album,videos = self.NewAlbumAndVideo(albumName, tvUrl)
            if album:
                album.largePicUrl = ch_list[2]
                for v in videos:
                    v.order, v.name = self.GetTVOrder(v.videoUrl)

                self.db.SaveAlbum(album)

class VstLiveTV(LivetvMenu):
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserVstLivetv]
