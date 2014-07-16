#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

import pymongo

from kola import GetPinYin, autostr


TVOrder = [
    'CCTV-1 ',
    'CCTV-2 ',
    'CCTV-3 ',
    'CCTV-4 ',
    'CCTV-5 ',
    'CCTV5\+',
    'CCTV-6 ',
    'CCTV-7 ',
    'CCTV-8 ',
    'CCTV-9 ',
    'CCTV-10 ',
    'CCTV-11 ',
    'CCTV-12 ',
    'CCTV-13 ',
    'CCTV-14 ',
    'CCTV-15 ',
    'CCTV NEWS',
    'CCTV-Français',
    'CCTV-Español',
    'CCTV-العربية',
    'CCTV-Русский',
    'CCTV体育赛事',
    '安徽卫视',
    '北京卫视',
    '重庆卫视',
    '东方卫视',
    '东南卫视',
    '广东卫视',
    '广西卫视',
    '甘肃卫视',
    '贵州卫视',
    '海峡卫视',
    '河北卫视',
    '河南卫视',
    '黑龙江卫视',
    '湖南卫视',
    '湖北卫视',
    '吉林卫视',
    '江西卫视',
    '江苏卫视',
    '康巴卫视',
    '辽宁卫视',
    '旅游卫视',
    '内蒙古卫视',
    '宁夏卫视',
    '青海卫视',
    '山东卫视',
    '山东教育台',
    '深圳卫视',
    '陕西卫视',
    '山西卫视',
    '四川卫视',
    '天津卫视',
    '西藏卫视',
    '厦门卫视',
    '新疆卫视',
    '香港卫视',
    '延边卫视',
    '云南卫视',
    '浙江卫视',
    '三沙卫视',
    '兵团卫视',
    '凤凰卫视',
    '华娱卫视'
    'CCTV ',
]

con = pymongo.Connection('localhost', 27017)
mongodb = con.kola
tv_table  = mongodb.tvnumber
tv_table.create_index([('id', pymongo.ASCENDING)])

def GetOrder(name):
    i = 0
    for n in TVOrder:
        if re.findall(n, name):
            return '%04d' % i

        i += 1
    pinyin = GetPinYin(name, True)
    if pinyin:
        return '9' + pinyin

    return '9999'

def GetNumber(name):
    i = 1
    for n in TVOrder:
        if re.findall(n, name):
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
