#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import GetPinYin, autostr
import pymongo

TVOrder = [
    'CCTV-1 综合',
    'CCTV-2 财经',
    'CCTV-3 综艺',
    'CCTV-4 中文国际',
    'CCTV-4 (亚洲)',
    'CCTV-4 (欧洲)',
    'CCTV-4 (美洲)',
    'CCTV-5 体育',
    'CCTV-5+ 体育',
    'CCTV-6 电影',
    'CCTV-7 军事农业',
    'CCTV-8 电视剧',
    'CCTV-9 纪录',
    'CCTV-9 纪录(英)',
    'CCTV-10 科教',
    'CCTV-11 戏曲',
    'CCTV-12 社会与法',
    'CCTV-13 新闻',
    'CCTV-14 少儿',
    'CCTV-15 音乐',
    'CCTV-NEWS',
    'CCTV-Français',
    'CCTV-Español',
    'CCTV-العربية',
    'CCTV-Русский',
    'CCTV体育赛事',
    '安徽卫视',
    #'安徽卫视-高清',
    '北京卫视',
    #'北京卫视-高清',
    '重庆卫视',
    #'重庆卫视-高清',
    '东方卫视',
    #'东方卫视-高清',
    '东南卫视',
    #'东南卫视-高清',
    '广东卫视',
    #'广东卫视-高清',
    '广西卫视',
    '甘肃卫视',
    '贵州卫视',
    '海峡卫视',
    '河北卫视',
    #'河北卫视-高清',
    '河南卫视',
    '黑龙江卫视',
    #'黑龙江卫视-高清',
    '湖南卫视',
    #'湖南卫视-高清',
    '湖北卫视',
    #'湖北卫视-高清',
    '吉林卫视',
    '江西卫视',
    '江苏卫视',
    #'江苏卫视-高清',
    '康巴卫视',
    '辽宁卫视',
    '旅游卫视',
    '内蒙古卫视',
    '宁夏卫视',
    '青海卫视',
    '山东卫视',
    #'山东卫视-高清',
    '山东教育台',
    '深圳卫视',
    #'深圳卫视-高清',
    '陕西卫视',
    '山西卫视',
    '四川卫视',
    '天津卫视',
    #'天津卫视-高清',
    '西藏卫视',
    '厦门卫视',
    '新疆卫视',
    '香港卫视',
    '延边卫视',
    '云南卫视',
    '浙江卫视',
    #'浙江卫视-高清',
]

con = pymongo.Connection('localhost', 27017)
mongodb = con.kola
tv_table  = mongodb.tvnumber
tv_table.create_index([('id', pymongo.ASCENDING)])

def GetOrder(name):
    i = 0
    for n in TVOrder:
        if n == name:
            return '%04d' % i

        i += 1
    pinyin = GetPinYin(name, True)
    if pinyin:
        return '9' + pinyin

    return '9999'

def GetNumber(name):
    i = 1
    for n in TVOrder:
        if n == name:
            return '%d' % i
        i += 1

    ret = tv_table.find_one({'name' : name})
    if ret:
        return ret['number']
    else:
        count = tv_table.find().count() + 100
        number = autostr(count + 1)
        tv_table.insert({'name' : name, 'number' : number})

        return number
