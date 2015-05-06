#! /usr/bin/python3
# -*- coding: utf-8 -*-

from . import db


filter_year = [ '2013', '2012', '2011', '2010', '00年代', '90年代', '80年代', '更早' ]
filter_sort = ['昨日热播', '历史热播', '最新发布', '最新更新', '评分最高']

# 直播
class LivetvMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 200
        self.sort = ['Name', '昨日热播']

        self.filter = {
            '类型':
                ['央视台',
                '卫视台',
                '本省台',
                #'高清台',
                '体育台',
                '少儿台',
                '地方台',
                '网络台',
                ],
            'PinYin' : []
        }

        self.parserList = []
        self.parserClassList = []

    def FixArgument(self, argument):
        if 'filter' in argument and 'area' in argument:
            _filter = argument['filter']
            c = '类型'
            if c in _filter and _filter[c] == '本省台':
                _filter['local_area'] = argument['area']['province']
                del _filter[c]

    def RegisterParser(self, parserList):
        for p in self.parserClassList:
            parserList.append(p())

    def UpdateAllScore(self):
        pass

    def UpdateAlbumList(self):
        for p in self.parserClassList:
            p().Execute()

# 电影
class MovieMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 1

        self.sort = filter_sort
        self.filter = {
            '年份' :  filter_year,
            '类型' : [
                '爱情片', '战争片', '喜剧片', '科幻片', '恐怖片', '动画片', '动作片', '风月片', '剧情片', '冒险片', '记录片',
                '歌舞片', '纪录片', '魔幻片', '灾难片', '悬疑片', '传记片', '警匪片', '伦理片', '惊悚片', '音乐片',
                '谍战片', '历史片', '武侠片', '青春片', '文艺片', '枪战片', '悲剧片', '武侠片', '家庭片', '其他'
            ],
            '产地' : [
                '内地', '香港', '台湾', '日本', '韩国', '欧洲',  '美国',   '英国',
                '印度', '泰国', '其他', '法国', '德国','意大利', '西班牙', '俄罗斯', '加拿大'
            ],
            'PinYin' : []
        }
        self.quickFilter = [
            {'title' : '热门电影', 'sort' : '昨日热播' },
            {'title' : '最新电影', 'sort' : '最新发布'   },
            {'title' : '推荐电影', 'sort' : '评分最高', 'filter': {'评分最高' : ''}},
            {'title' : '国产电影', 'sort' : '昨日热播', 'filter': {'产地' : '内地' }},
            {'title' : '欧美大片', 'sort' : '昨日热播', 'filter': {'产地' : '美国,英国,法国,德国,意大利,西班牙,俄罗斯' }},
            {'title' : '港台电影', 'sort' : '昨日热播', 'filter': {'产地' : '香港,台湾,港台' }},
            {'title' : '日韩电影', 'sort' : '昨日热播', 'filter': {'产地' : '日本,韩国,日韩' }},
        ]

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
                '农村片', '军旅片', '刑侦片', '喜剧片', '悬疑片', '剧情片', '传记片', '科幻片',
                '动画片', '动作片', '栏目片', '惊悚片', '谍战片', '伦理片', '战争片', '神话片',
                '宫廷片', '穿越片', '灾难片', '真人秀片'
            ],
            '产地' : [ '内地', '香港', '台湾', '美国', '韩国', '英国', '泰国', '日本', '其他' ],
            'PinYin' : []
        }

        self.quickFilter = [
            {'title' : '热播剧'  , 'sort' : '昨日热播'},
            {'title' : '最新更新' , 'sort' : '最新发布' },
            {'title' : '推荐'    , 'sort' : '评分最高', 'filter': {'评分最高' : ''}  },
            {'title' : '国内剧'  , 'sort' : '昨日热播', 'filter': {'产地' : '内地' }      },
            {'title' : '日韩剧'  , 'sort' : '昨日热播', 'filter': {'产地' : '日本,韩国,日韩' } },
            {'title' : '港台剧'  , 'sort' : '昨日热播', 'filter': {'产地' : '香港,台湾,港台' } },
            {'title' : '美剧'   , 'sort' : '昨日热播', 'filter': {'地区' : '美国' }     },
        ]

# 动漫
class ComicMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 3
        self.sort = filter_sort
        self.filter = {
            '年份' : filter_year,
            '篇幅' : [ '剧场版', 'TV版', '花絮', 'OVA', '其他' ],
            '类型' : [
                '历史', '搞笑', '战斗', '冒险', '魔幻', '励志', '益智', '童话', '体育', '神话', '青春',
                '悬疑', '真人', '亲子', '恋爱', '科幻', '治愈', '日常', '神魔', '百合', '耽美', '校园',
                '后宫', '竞技', '机战', '动作', '热血', '战争', '古代', '都市', '宠物', '教育', '美少女'],

            '产地' : [ '大陆', '日本', '美国', '韩国', '香港', '欧洲', '英国', '加拿大', '俄罗斯', '其他'],
            '年龄' : [ '5岁以下', '5岁-12岁', '13岁-18岁', '18岁以上' ],
            'PinYin' : []
        }

        self.quickFilter = [
            {'title' : '热播剧'  , 'sort' : '昨日热播'},
            {'title' : '最新更新' , 'sort' : '最新发布' },
            {'title' : '推荐'    , 'sort' : '评分最高', 'filter': {'评分最高' : ''}  },
            {'title' : '中国动漫'  , 'sort' : '昨日热播', 'filter': {'产地' : '内地,香港,台湾,港台' }      },
            {'title' : '日韩动漫'  , 'sort' : '昨日热播', 'filter': {'产地' : '日本,韩国,日韩' } },
            {'title' : '欧美动漫'   , 'sort' : '昨日热播', 'filter': {'地区' : '美国,欧洲,英国,加拿大,俄罗斯' }     },
        ]

# 记录片
class DocumentaryMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 4
        self.sort = filter_sort
        self.filter = {
            '类型': ['人物', '历史', '自然', '军事', '社会', '幕后', '财经',
                     '剧情', '旅游', '科技', '文化', '搜狐视频大视野'],
            'PinYin' : []
        }

# 综艺
class ShowMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 5
        self.sort = filter_sort
        
        self.filter = {
            '类型' : ['访谈', '情感', '访谈', '搞笑', '时尚', '游戏', 'KTV', '美食', '文化', '命理',
                      '交友', '选秀', '音乐', '曲艺', '养生', '歌舞', '娱乐', '纪实', '歌舞',
                      '真人秀', '脱口秀', '其他'],
            '产地' : ['内地', '港台', '欧美', '日韩', '其他'],
            'PinYin' : []
        }
        self.quickFilter = [
            {'title' : '热播'     , 'sort' : '昨日热播'},
            {'title' : '最新更新' , 'sort' : '最新发布' },
            {'title' : '推荐'    , 'sort' : '评分最高', 'filter': {'评分最高' : ''}},
            {'title' : '中国综艺'  , 'sort' : '昨日热播', 'filter': {'产地' : '内地,香港,台湾,港台' }      },
            {'title' : '日韩综艺'  , 'sort' : '昨日热播', 'filter': {'产地' : '日本,韩国,日韩' } },
            {'title' : '欧美综艺'   , 'sort' : '昨日热播', 'filter': {'地区' : '美国,欧洲,英国,加拿大,俄罗斯' }     },
        ]

# 教育
class EduMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 6
        self.sort = filter_sort
        self.filter = {
            '类型': ['公开课', '考试辅导', '职业培训', '外语学习', '幼儿教育', '乐活', '职场管理', '中小学教育'],
            'PinYin' : []
        }

# 娱乐
class YuleMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 7
        self.sort = filter_sort
        self.filter = {
            '类型' : ['明星', '电影', '电视', '音乐', '戏剧', '动漫', '其他'],
            '范围' : ['今天', '本周', '本月'],
            'PinYin' : []
        }

# 旅游
class TourMenu(db.VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.cid = 8
        self.sort = filter_sort
        self.filter = {
            '类型': [
                '自驾游','攻略','交通住宿','旅游资讯','国内游',
                '境外游','自然','人文','户外','美食','节庆活动',
            ],
            'PinYin' : []
        }
