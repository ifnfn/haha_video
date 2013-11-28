#!/usr/bin/python3
# -*- coding: utf-8 -*-


from xml.etree import ElementTree
from kolaclient import KolaClient

class TVStation:
    def __init__(self):
        self.flag = ''
        self.name = ''
        self.vid  = ''
        self.logo1 = ''
        self.logo2 = ''
        self.haha = KolaClient()
        self.script = '',
        self.parameters = ''
        self.area = ''
        
    def GetScript(self):
        return {'script'     : self.script,
                'parameters' : self.parameters}

class JLNTV(TVStation):
    def __init__(self):
        super().__init__()
        self.base_url = 'http://live.jlntv.cn'
        self.GetChannel()


class TVIEStation(TVStation):
    def __init__(self, name, url):
        super().__init__()
        self.name = name
        self.base_url = url
        self.script = 'tvie'
        

class NBTV(TVIEStation):
    def __init__(self):
        self.area = '淅江省,宁波市'
        super().__init__('宁波电视台', 'ming-api.nbtv.cn')

class UCATV(TVIEStation):
    def __init__(self):
        self.area = '新疆'
        super().__init__('新疆电视台', 'epgsrv01.ucatv.com.cn')

class ZJTV(TVIEStation):
    def __init__(self):
        self.area = '淅江省'
        super().__init__('浙江电视台', 'api.cztv.com')

class HZTV(TVStation):
    def __init__(self):
        super().__init__()
        self.name = '杭州电视台'
        self.area = '淅江省,杭州市'


class DHTV(TVStation):
    def __init__(self):
        super().__init__()
        self.name = '温州电视台'
        self.area = '淅江省,温州市'


class CUTV(TVStation):
    def __init__(self):
        super().__init__()
        self.tvlist = {}

    def GetTV(self):
        if not self.tvlist:
            url = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=tv_live'
            text = self.haha.GetCacheUrl(url).decode()
            root = ElementTree.fromstring(text)
            for p in root.findall('tv'):
                tv = TVStation()
                tv.vid = p.findtext('tv_id')
                tv.name = p.findtext('tv_name')
                tv.logo1 = p.findtext('tv_thumb_img')
                tv.logo2 = p.findtext('tv_logo')
                self.tvlist[tv.name] = tv

    def GetStation(self, name):
        if name not in self.tvlist:
            print(name)
            self.GetTV()
        if name in self.tvlist:
            return self.tvlist[name]
        else:
            return None

class CutvStation(TVStation):
    cutv = CUTV()
    def __init__(self, name):
        super().__init__()
        tv = self.cutv.GetStation(name)
        if tv:
            self.vid = tv.vid
            self.name = tv.name
            self.logo1 = tv.logo1
            self.logo2 = tv.logo2

class TV:
    def __init__(self):
        self.TVStationList = {
            '新疆电视台' : UCATV(),
            '浙江电视台' : ZJTV(),
            '杭州电视台' : HZTV(),
            '宁波电视台' : NBTV(),
            '吉林电视台' : JLNTV(),
            '温州电视台' : DHTV(),
            '绍兴电视台' : CutvStation('绍兴台'),
            '深圳电视台' : CutvStation('深圳台'),
            '太原电视台' : CutvStation('太原台'),
            '荆州电视台' : CutvStation('荆州台'),
            '湖北电视台' : CutvStation('湖北台'),
            '襄阳电视台' : CutvStation('襄阳台'),
            '石家庄电视台' : CutvStation('石家庄台'),
            '南通电视台' : CutvStation('南通台'),
            '柳州电视台' : CutvStation('柳州台'),
            '济南电视台' : CutvStation('济南台'),
            '武汉电视台' : CutvStation('武汉台'),
            '苏州电视台' : CutvStation('苏州台'),
            '西安电视台' : CutvStation('西安台'),
            '西宁电视台' : CutvStation('西宁台'),
            '郑州电视台' : CutvStation('郑州台'),
            '泰州电视台' : CutvStation('泰州台'),
            '台州电视台' : CutvStation('台州台'),
            '安阳电视台' : CutvStation('安阳台'),
            '南宁电视台' : CutvStation('南宁台'),
            '大连电视台' : CutvStation('大连台'),
            '兰州电视台' : CutvStation('兰州台'),
            '珠海电视台' : CutvStation('珠海台'),
        }
        
    def GetScript(self, name):
        if name in self.TVStationList:
            return self.TVStationList[name].GetScript()
        else:
            return {}

def main():
    pass

if __name__ == "__main__":
    main()
