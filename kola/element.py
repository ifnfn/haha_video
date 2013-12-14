#! /usr/bin/python3
# -*- coding: utf-8 -*-

from . import db


filter_year = [ '2013', '2012', '2011', '2010', '00年代', '90年代', '80年代', '更早' ]
filter_sort = ['周播放最多', '日播放最多', '总播放最多', '最新发布', '评分最高']

# 直播
class LivetvMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 200
        self.sort = ['Name', '日播放最多']

        self.filter = {
            '类型': ['卫视台', '地方台', '央视台', '境外台', '本地台' ]
        }

# 电影
class MovieMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 1

        self.sort = filter_sort
        self.filter = {
            '年份' :  filter_year,
            '类型' : [
                '爱情片', '战争片', '喜剧片', '科幻片', '恐怖片', '动画片', '动作片', '风月片', '剧情片',
                '歌舞片', '纪录片', '魔幻片', '灾难片', '悬疑片', '传记片', '警匪片', '伦理片', '惊悚片',
                '谍战片', '历史片', '武侠片', '青春片', '文艺片'
            ],
            '产地' : [
                '内地', '香港', '台湾', '日本', '韩国', '欧洲',  '美国',   '英国',
                '印度', '泰国', '其他', '法国', '德国','意大利', '西班牙', '俄罗斯', '加拿大'
            ]
        }
        self.quickFilter = {
            '热门电影' : {
                    'sort' : '周播放最多'
            },
            '最新电影' :{
                    'sort' : '日播放最多'
            },
            '推荐电影' :{
                    'sort' : '评分最高'
            },
            '国产电影' : {
                    'filter': {'产地' : '内地' },
                    'sort'  :  '日播放最多'
            },
            '欧美大片' : {
                    'filter': {'产地' : '美国,英国,法国,德国,意大利,西班牙,俄罗斯' },
                    'sort' :   '日播放最多'
            },
            '港台电影' : {
                    'filter': {'产地' : '香港,台湾' },
                    'sort'  :  '日播放最多'
            },
            '日韩电影' : {
                    'filter': {'产地' : '日本,韩国' },
                    'sort'  :  '日播放最多'
            },
        }

# 电视剧
class TVMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 2

        self.sort = filter_sort
        self.filter = {
            '年份' : filter_year,
            '类型' : [
                '偶像片', '家庭片', '历史片', '年代片', '言情片', '武侠片', '古装片', '都市片',
                '农村片', '军旅片', '刑侦片', '喜剧片', '悬疑片', '情景片', '传记片', '科幻片',
                '动画片', '动作片', '栏目片', '惊悚片', '谍战片', '伦理片', '战争片', '神话片',
                '真人秀片'
            ],
            '产地' : [ '内地', '港剧', '台剧', '美剧', '韩剧', '英剧', '泰剧', '日剧', '其他' ]
        }
        self.quickFilter = {
            '热播剧' : {
                    'sort' : '周播放最多'
            },
            '最新更新' :{
                    'sort' : '最新发布'
            },
            '推荐' :{
                    'sort' : '评分最高'
            },
            '国内剧' : {
                    'filter': {'产地' : '内地' },
                    'sort'  :  '日播放最多'
            },
            '日韩剧' : {
                    'filter': {'产地' : '韩剧,日剧' },
                    'sort'  :  '日播放最多'
            },
            '港台剧' : {
                    'filter': {'产地' : '港剧,台剧' },
                    'sort' :   '日播放最多'
            },
            '美剧' : {
                    'filter': {'地区' : '美剧' },
                    'sort' :   '日播放最多'
            },
        }

# 动漫
class ComicMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 115
        self.sort = filter_sort
        self.filter = {
            '年份' : self.filter_year,
            '篇幅' : [ '剧场版', 'TV版', '花絮', 'OVA', '其他' ],
            '类型' : [
                '历史', '搞笑', '战斗', '冒险', '魔幻', '励志', '益智', '童话', '体育', '神话', '青春',
                '悬疑', '真人', '亲子', '恋爱', '科幻', '治愈', '日常', '神魔', '百合', '耽美', '校园',
                '后宫', '竞技', '机战', '美少女'],

            '产地' : [ '大陆', '日本', '美国', '韩国', '香港', '欧洲', '英国', '加拿大', '俄罗期', '其他'],
            '年龄' : [ '5岁以下', '5岁-12岁', '13岁-18岁', '18岁以上' ]
        }

# 综艺
class SohuShow(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 106
        self.sort = filter_sort
        self.filter = {
            '类型' : ['访谈', '时尚', '游戏竞技', 'KTV', '交友', '选秀', '音乐', '曲艺',
                      '养生', '脱口秀', '歌舞', '娱乐节目', '真人秀', '其他'],
            '产地' : ['内地', '港台', '欧美', '日韩', '其他']
        }

# 记录片
class SohuDocumentary(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 107
        self.sort = filter_sort
        self.filter = {
            '类型': ['人物', '历史', '自然', '军事', '社会', '幕后', '财经',
                     '剧情', '旅游', '科技', '文化', '搜狐视频大视野']
        }

# 教育
class SohuEdu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 119
        self.sort = filter_sort
        self.filter = {
            '类型': ['公开课', '考试辅导', '职业培训', '外语学习', '幼儿教育', '乐活', '职场管理', '中小学教育']
        }

# 新闻
class SohuNew(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 122
        self.sort = filter_sort
        self.filter = {
            '类型': ['国内', '国际', '军事', '科技', '财经', '社会', '生活'],
            '范围': ['今天', '本周', '本月']
        }

# 娱乐
class SohuYule(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 112
        self.sort = filter_sort
        self.filter = {
            '类型' : ['明星', '电影', '电视', '音乐', '戏剧', '动漫', '其他'],
            '范围' : ['今天', '本周', '本月']
        }

# 旅游
class SohuTour(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 131
        self.sort = filter_sort
        self.filter = {
            '类型': [
                '自驾游','攻略','交通住宿','旅游资讯','国内游',
                '境外游','自然','人文','户外','美食','节庆活动',
            ]
        }
