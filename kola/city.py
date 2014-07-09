#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

import pymongo
import tornado.escape

from .fetchTools import GetCacheUrl


class City():
    con = pymongo.Connection('localhost', 27017)
    mongodb = con.kola
    city_table  = mongodb.city
    city_table.create_index([('id', pymongo.ASCENDING)])
    cityList = []
    for x in city_table.find():
        del x['_id']
        cityList.append(x)

    def __init__(self):
        if len(self.cityList) == 0:
            self.Update()
            self.cityList = []
            for x in self.city_table.find():
                del x['_id']
                self.cityList.append(x)

    def Load(self):
        ret = []
        for x in self.city_table.find():
            del x['_id']
            ret.append(x)
        return x

    def Parser(self, url, pid=None):
        text = GetCacheUrl(url).decode()
        x = re.findall('callback\((.*)\);', text)

        ret = []
        if x:
            js = tornado.escape.json_decode(x[0])
            for prov in js:
                province = {}
                province['id']   = prov[1]
                province['name'] = prov[0]
                if pid:
                    province['pid']  = pid
                else:
                    province['pid']  = '0'
                ret.append(province)
                self.city_table.update({'id': prov[1]}, province, upsert=True)

        return ret

    def Update(self):
        province = self.Parser('http://cdn.weather.hao.360.cn/sed_api_area_query.php?grade=province')
        for p in province:
            city = self.Parser('http://cdn.weather.hao.360.cn/sed_api_area_query.php?grade=city&code=%s' % p['id'], p['id'])
            for c in city:
                self.Parser('http://cdn.weather.hao.360.cn/sed_api_area_query.php?grade=town&code=%s' % c['id'], c['id'])

    def GetFullById(self, p, cid):
        for prov in self.cityList:
            if cid == prov['id']:
                if p:
                    p = prov['name'] + ',' + p
                else:
                    p = prov['name']

                if prov['pid'] != '0':
                    return self.GetFullById(p, prov['pid'])
                else:
                    return p
        return p
    
    
    def GetListByCid(self, cid):
        ret = []
        for x in self.city_table.find({'pid': cid}):
            del x['_id']
            ret.append(x)
            
        return ret

    def GetListByFullName(self, name):
        ret = []
        cid = '0'
        if name == '':
            return self.GetListByCid(cid)

        found = False
        names = name.split('-')
        for n in names:
            if not n:
                continue
            found = False
            ret = self.GetListByCid(cid)
            for x in ret:
                if n == x['name']:
                    cid = x['id']
                    found = True

        if found:
            return self.GetListByCid(cid)
        else:
            return []
    
    def GetCiyByFullName(self, name):
        if not name:
            return ''
        cid = '0'
        
        found = False
        names = name.split('-')
        for n in names:
            if not n:
                continue
            
            found = False
            ret = self.GetListByCid(cid)
            for x in ret:
                if n == x['name']:
                    cid = x['id']
                    found = True

        if found:
            return cid
        else:
            return ''
        
    def GetCid(self, name):
        for prov in self.cityList:
            if prov['name'] in name:
                return prov['id']
            
        return None
    
    def GetCity(self, city):
        if '东南' in city:
            return '福建'
        elif '上视新娱乐' in city:
            return '上海'
        elif '南方卫视' in city:
            return '广东省'
        elif '旅游南方' in city:
            return '海南'

        # 优先找前匹配的
        for prov in self.cityList:
            city.find(prov['name'], )
            l = len(prov['name'])
            if city[:l] == prov['name']:
                return self.GetFullById('', prov['id'])

        for prov in self.cityList:
            if prov['name'] in city:
                return self.GetFullById('', prov['id'])

        return ''

def main():
    city = City()
    #city.Update()
    print(city.GetCity('营口台'))
    print(city.GetCity('大丰台'))

if __name__ == "__main__":
    main()
