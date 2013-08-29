#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado import gen
from tornado import httpclient
from tornado.options import define, options
from tornado.escape import json_encode
import haha

import redis
import json
import random
import re
import time
from jsonphandler import JSONPHandler
from datetime import timedelta, date

class ImgHandler(tornado.web.RequestHandler):
    def get(self,id):
        c = redis.Redis(host='127.0.0.1', port=6379, db=4)
        d = redis.Redis(host='127.0.0.1', port=6379, db=3)
        e = redis.Redis(host='127.0.0.1', port=6379, db=5)
        if id.startswith("singer") or id.startswith("show"):
            img = e.hget("id:%s"%id,"img")
            self.redirect(img, permanent=True)
            return
        elif c.exists("id:%s"%id):
            img = c.hget("id:%s"%id,"img")
            self.redirect(img, permanent=True)
            return
        elif d.exists("id:%s"%id):
            data = d.hgetall("id:%s"%id)
            item = json.loads(data.values()[0])
            img = item['img']
            self.redirect(img, permanent=True)
            return
        else:
            raise tornado.web.HTTPError(404)
            self.finish()
            return


def getlist(page, size, setname, flag, type):
    c = redis.Redis(host='127.0.0.1', port=6379, db=4)
    print c.keys()

    m = (int(page) - 1) * int(size)
    n = int(page) * int(size)
    length = c.llen(setname)
    print "length: ", length
    nexts = length - n
    if n > length:
        n = length - 1
        if m > length:
            m = n - int(size) +1
        nexts = 0
    else:
        n = n -1
    if m < 0:
        m = 0

    ids = c.lrange(setname, m, n)
    items = []
    for id in ids:
        # c.expire(id, 10)
        # print "TTL: ", c.ttl(id)
        if not c.exists(id):
            continue
        item = c.hgetall(id)
        items.append(item)
    data = {}
    data['total'] = length
    data['next']  = nexts
    data['items'] = items
    return data

class TvnewHandler(JSONPHandler):
    def get(self):
        page = self.get_argument("page")
        size = self.get_argument("size")
        setname = "new:tv"
        type = "tv"
        flag = False
        data = getlist(page,size,setname,flag,type)
        self.finish(json.dumps(data, indent=4, ensure_ascii=False))
        return


class TvhotHandler(JSONPHandler):
    def get(self):
        page = self.get_argument("page")
        size = self.get_argument("size")
        setname = "title:tv"
        type = "tv"
        flag = False
        data = getlist(page, size, setname, flag, type)
        self.finish(json.dumps(data, indent=4, ensure_ascii=False))
        return

class CateHandler(JSONPHandler):
    def get(self):
        t_cate = [
            ("电影", "100"、电视剧101、动漫115、综艺1270()
            m_cate006、纪录片107、音乐121、教育119、新闻122、娱乐112、星尚130、
            旅游131、网友上传99900onPopupPost()
            m_cate0
        m_cate = [
                    { "title":"传记片", "id":"m_zhuanji"},
                    { "title":"伦理片", "id":"m_lunli"},
                    { "title":"剧情片", "id":"m_juqing"},
                    { "title":"动作片", "id":"m_dongzuo"},
                    { "title":"动画片", "id":"m_donghua"},
                    { "title":"历史片", "id":"m_lishi"},
                    { "title":"喜剧片", "id":"m_xiju"},
                    { "title":"恐怖片", "id":"m_kongbu"},
                    { "title":"悬疑片", "id":"m_xuanyi"},
                    { "title":"惊悚片", "id":"m_jingsong"},
                    { "title":"战争片", "id":"m_zhanzheng"},
                    { "title":"歌舞片", "id":"m_gewu"},
                    { "title":"武侠片", "id":"m_wuxia"},
                    { "title":"灾难片", "id":"m_zainan"},
                    { "title":"爱情片", "id":"m_aiqing"},
                    { "title":"短片",   "id":"m_duan"},
                    { "title":"科幻片", "id":"m_kehuan"},
                    { "title":"纪录片", "id":"m_jilu"},
                    { "title":"警匪片", "id":"m_jingfei"},
                    { "title":"风月片", "id":"m_fengyue"},
                    { "title":"魔幻片", "id":"m_mohuan"},
                    { "title":"青春片", "id":"m_qingchun"},
                    { "title":"文艺片", "id":"m_wenyi"},
                    { "title":"谍战片", "id":"m_diezhan"}
                ]
        t_cate = [
                    { "title":"伦理剧", "id":"t_lunli"},
                    { "title":"偶像剧", "id":"t_ouxiang"},
                    { "title":"军旅剧", "id":"t_junlv"},
                    { "title":"刑侦剧", "id":"t_xingzhen"},
                    { "title":"剧情片", "id":"t_juqing"},
                    { "title":"动作剧", "id":"t_dongzuo"},
                    { "title":"历史剧", "id":"t_lishi"},
                    { "title":"古装剧", "id":"t_guzhuang"},
                    { "title":"喜剧片", "id":"t_xiju"},
                    { "title":"家庭剧", "id":"t_jiating"},
                    { "title":"悬疑剧", "id":"t_xuanyi"},
                    { "title":"情景剧", "id":"t_qingjing"},
                    { "title":"战争剧", "id":"t_zhanzheng"},
                    { "title":"武侠剧", "id":"t_wuxia"},
                    { "title":"科幻剧", "id":"t_kehuan"},
                    { "title":"谍战剧", "id":"t_diezhan"},
                    { "title":"都市剧", "id":"t_dushi"},
                    { "title":"神话剧", "id":"t_shenhua"},
                    { "title":"言情剧", "id":"t_yanqing"},
                    { "title":"年代剧", "id":"t_niandai"},
                    { "title":"农村剧", "id":"t_nongcun"},
                    { "title":"惊悚剧", "id":"t_jingsong"},
                    { "title":"传记剧", "id":"t_zhuanji"},
                    { "title":"灾难剧", "id":"t_zainan"},
                    { "title":"犯罪剧", "id":"t_fanzui"},
                    { "title":"生活剧", "id":"t_shenghuo"},
                    { "title":"经典剧", "id":"t_jingdian"}
                 ]
        cate = {}
        cate['movie'] = m_cate
        cate['tv'] = t_cate
        self.finish(json.dumps(cate, indent=4, ensure_ascii=False))
        return

class VideoListHandler(tornado.web.RequestHandler):
    def get(self):
        c = redis.Redis(host='127.0.0.1', port=6379, db=4)
#        print c.keys()
        ids = c.lrange('title:tv', 0, -1)
        items = []
        for id in ids:
            if not c.exists(id):
                continue
            item = {}
            item['title'] = c.hgetall(id)['title']
#            self.finish(c.hgetall(id)['title']
            items.append(item)
        self.finish(json.dumps(items, sort_keys=True, indent=4, ensure_ascii=False))

        return
        return data

def main():
    define("port", default=9990, help="run on the given port", type=int)
    settings = {"debug": False, "template_path": "templates",
           "cookie_secret": "z1DAVh+WTvyqpWGmOtJCQLETQYUznEuYskSF062J0To="}
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/video/tv/new",            TvnewHandler),
        (r"/video/tv/hot",            TvhotHandler),
        (r"/video/cate",              CateHandler),
        (r"/video/list",              VideoListHandler),
        (r"/video/img/(.*)",          ImgHandler),
    ], **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
if __name__ == "__main__":
    main()
