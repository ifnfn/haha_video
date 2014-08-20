#! /usr/bin/python3
# -*- coding: utf-8 -*-

import base64
import re

from kola import LivetvMenu

from .common import PRIOR_VST, PRIOR_LETV, PRIOR_IMGO, PRIOR_CNTV, PRIOR_DEFTV
from .livetvdb import LivetvParser


class ParserVstLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = ''
        self.order = PRIOR_VST
        self.Alias = {
            'CCTV9 海外记录' : 'CCTV-9 海外纪录',
            'CCTV4 中文国际(美洲)' : 'CCTV-4 中文国际(美洲)',
            'CCTV4 中文国际(欧洲)' : 'CCTV-4 中文国际(欧洲)',
            'HD' : '-高清',
            '湖南卫视': '湖南卫视-高清'
        }
        self.cmd['cache'] = True
        self.cmd['source'] = 'http://ott.52itv.cn/vst_tvlist?app=egreat&name=mygica%20TV%20MX%20box&ver=4.1.2&uuid=00000000-71b9-5e32-0033-c5870033c587&mac=000102030406'
        self.ExcludeName = ['电影片花', '法国1', '高尔夫.网球', '高尔夫', '周星驰专区', 'CCTV-4 中文国际(欧洲)', 'CCTV-4 中文国际(美洲)', 'CCTV ',
                            '经典电影', 'CCTV4 中文国际(美洲)', 'CCTV4 中文国际(欧洲)',
                            '安庆'
                            ]
        self.vtv_order = 0

    def GetChannel(self, channels, name):
        for p in channels:
            if re.findall(p, name):
                return name

    def GetTVOrder(self, url):
        if url.find('vlive', 0) >= 0:
            return PRIOR_DEFTV, 'VLIVE'
        elif url.find('imgotv', 0) >= 0:
            return PRIOR_IMGO, 'VITV'
        elif url.find('pa://', 0) >= 0 or url.find('cntv.') > 0:
            return PRIOR_CNTV, 'VCNTV'
        elif re.findall('http://url.52itv.cn/live/(.*).m3u8', url):
            return PRIOR_DEFTV, 'M3U8'

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
            #if albumName.find('山东') < 0:
            #    continue
            self.vtv_order = 0

            tvUrl = []
            hrefs = ch_list[1]
            for u in hrefs.split('#'):
                if u.find('imgotv') >= 0:
                    continue

                #if re.findall('http://url.52itv.cn/live/(.*).sdtv', u):
                #    continue

                # 将 YY直播去掉
                need = True
                vid = re.findall('http://url.52itv.cn/live/(.*).m3u8', u)
                if vid:
                    #print(albumName, u)
                    channels = ['安徽公共', '安徽综艺', '安徽影视', '安徽科教', '安徽经济', '安徽国际', '安徽人物',
                                'CCTV', '南方', '广东', '广州', '英语辅导', '炫动卡通', '优漫卡通', '珠江频道', '嘉佳卡通', '山东']
                    if self.GetChannel(channels, albumName):
                        need = False
                        if vid[0] in ['6F736C5054333768614E597A704E42512AB587',
                                 '6E4E314D5379376861325951627936517B6A9F',
                                 '6F736C5054333768614E304A704E4251BF66E9'
                                 ] :
                            need = True
                    #need = not need
                if need:
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
