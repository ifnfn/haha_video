#! /usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib
import json
import sys
import traceback
import uuid

from pymongo import Connection
import redis
import tornado.escape
import tornado.ioloop
import tornado.web

from kola import BaseHandler, log, utils
from kolaserver import KolatvServer


tv = KolatvServer()

class AlbumListHandler(BaseHandler):
    def argument(self):
        args = {}
        args['page']  = int(self.get_argument('page', 0))
        args['size']  = int(self.get_argument('size', 20))
        args['full']  = int(self.get_argument('full', 0))

        engine = self.get_argument('engine', '')
        if engine:
            args['engine'] = engine

        key = self.get_argument('key', '')
        if key:
            args['key'] = key

        value = self.get_argument('value', '')
        if value: args['value'] = value

        return args, self.get_argument('menu', ''), self.get_argument('cid', ''), self.get_argument('vid', '')

    def get(self):
        args, menu, cid, vid = self.argument()

        if cid:
            albumlist, args['total'] = tv.GetMenuAlbumListByCid(cid, args)
        elif menu:
            albumlist, args['total'] = tv.GetMenuAlbumListByName(menu, args)
        elif vid:
            albumlist, args['total'] = tv.GetMenuAlbumListByVidList(vid, args)

        if albumlist: args['result'] = albumlist

        self.finish(json.dumps(args, indent=4, ensure_ascii=False))

    def post(self):
        args, menu, cid, vid = self.argument()

        if self.request.body:
            try:
                umap = tornado.escape.json_decode(self.request.body)
                args.update(umap)
            except:
                t, v, tb = sys.exc_info()
                log.error("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
                raise tornado.web.HTTPError(400)

        if cid:
            albumlist, args['total'] = tv.GetMenuAlbumListByCid(cid, args)
        elif menu:
            albumlist, args['total'] = tv.GetMenuAlbumListByName(menu, args)
        elif vid:
            albumlist, args['total'] = tv.GetMenuAlbumListByVidList(vid, args)

        if albumlist: args['result'] = albumlist

        self.finish(json.dumps(args, indent=4, ensure_ascii=False))

class GetVideoPlayerUrlHandle(BaseHandler):
    def get(self):
        ret = []
        vid = self.get_argument('vid', '')
        res = self.get_argument('resolution', '')
        try:
            video = tv.GetVideoByVid(vid)
            if video:
                for k,v in list(video['videos'].items()):
                    if (res == '' and k == 'default') or res == 'all' or v['name'] in res:
                        ret.append(v)
                if len(ret) == 0: # 如果没有找到，就使用第一个
                    for _,v in list(video['videos'].items()):
                        ret.append(v)
                        break

        finally:
            self.finish(json.dumps(ret, indent=4, ensure_ascii=False))

# 'http://127.0.0.1:9991/video/getvideo?pid=1330988&full=1'
# 'http://127.0.0.1:9991/video/getvideo?pid=1330988&full=0'
class GetVideoHandler(BaseHandler):
    def argument(self):
        args = {}
        page = self.get_argument('page', 0)
        if page:
            args['page'] = page
        size = self.get_argument('size', 0)
        if size:
            args['size'] = size

        return args, self.get_argument('pid', ''), self.get_argument('full', '')

    def get(self):
        args,pid,full = self.argument()

        self.Finish(args, pid, full)

    def Finish(self, args, pid, full):
        videos, count = tv.GetVideoListByPid(pid, args)
        #if full != '1':
        #    for v in videos:
        #        del v['videos']

        args['count'] = count
        args['videos'] = videos
        self.finish(json.dumps(args, indent=4, ensure_ascii=False))

    def post(self):
        args,pid,full = self.argument()

        if self.request.body:
            try:
                umap = tornado.escape.json_decode(self.request.body)
                args.update(umap)
            except:
                t, v, tb = sys.exc_info()
                log.error("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
                raise tornado.web.HTTPError(400)

        self.Finish(args, pid, full)

class GetPlayerHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        body = self.request.body.decode()
        if body and len(body) > 0:
            text = self.sohuVideoUrl(body, self.request.protocol + '://' + self.request.host  + '/video/urls')
            self.finish(text)
        else:
            raise tornado.web.HTTPError(404)

    def sohuVideoUrl(self, text, url):
        try:
            ret = tornado.escape.json_decode(text)
            if type(ret) == str:
                ret = tornado.escape.json_decode(ret)

            if 'sets' in ret:
                max_duration = 0.0
                m3u8 = ''
                video_count = len(ret['sets'])
                for u in ret['sets']:
                    new      = u['new']
                    url_tmp  = u['url']
                    duration = float(u['duration'])
                    if not (new and url_tmp and duration):
                        continue

                    start, _, _, key, _, _, _, _ = url_tmp.split('|')
                    u_tmp = '%s%s?key=%s' % (start[:-1], new, key)

                    if video_count == 1:
                        return u_tmp
                    m3u8 += '#EXTINF:%.0f\n%s\n' % (duration, u_tmp)
                    if duration > max_duration:
                        max_duration = duration

                m3u8 = '#EXTM3U\n#EXT-X-TARGETDURATION:%.0f\n%s#EXT-X-ENDLIST\n' % (max_duration, m3u8)

                name = hashlib.md5(m3u8.encode()).hexdigest()[16:]
                tv.db.SetVideoCache(name, m3u8)

                return url + name
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine._ParserRealUrlStep2: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return ''

# http://xxxxx/video/getmenu?cid=1,2
# http://xxxxx/video/getmenu
# http://xxxxx/video/getmenu?name=电影,电视剧
# http://xxxxx/video/getmenu?name=
class GetMenuHandler(BaseHandler):
    def get(self):
        ret = []
        cid = self.get_argument('cid', '')
        name  = self.get_argument('name', '')
        if cid:
            cid = cid.split(',')
            ret = tv.GetMenuJsonInfoById(cid)
        elif name != '':
            name = name.split(',')
            ret =  tv.GetMenuJsonInfoByName(name)
        else:
            ret =  tv.GetMenuJsonInfoByName([])

        self.finish(json.dumps(ret, indent=4, ensure_ascii=False))

class GetKolaInfoHandler(BaseHandler):
    def get(self):
        ret =  tv.GetVideoSource()

        self.finish(json.dumps(ret, indent=4, ensure_ascii=False))

class UploadHandler(BaseHandler):
    def get(self):
        print('Upload get')
        pass

    def post(self):
        try:
            if type(self.request.body) == bytes:
                body = self.request.body.decode()
            else:
                body = self.request.body
            if body and len(body) > 0:
                tv.ParserHtml(body)
                #tv.AddTask(body)
        except:
            pass

class ShowHandler(BaseHandler):
    def initialize(self):
        pass

    def get(self):
        vid = self.get_argument('vid')
        album = tv.db.FindAlbumJson(vid=vid)
        if not album:
            return

        if 'largeVerPicUrl' in album:
            album['pic'] = album['largeVerPicUrl']
        elif 'largeHorPicUrl' in album:
            album['pic'] = album['largeHorPicUrl']
        elif 'smallVerPicUrl' in album:
            album['pic'] = album['smallVerPicUrl']
        elif 'smallVerPicUrl' in album:
            album['pic'] = album['smallVerPicUrl']
        else:
            album['pic'] = ''
        if 'directors' in album:
            album['directors'] = ', '.join(album['directors'])
        else:
            album['directors'] = ''
        if 'mainActors' in album:
            album['mainActors'] = ', '.join(album['mainActors'])
        else:
            album['mainActors'] = ''

        if 'area' not in album:
            album['area'] = ''

        if 'playLength'   not in album: album['playLength'] = 0
        if 'albumDesc'    not in album: album['albumDesc'] = ''
        if 'totalPlayNum' not in album: album['totalPlayNum'] = ''
        if 'videoScore'   not in album: album['videoScore'] = 0

        totalPlayNum = utils.autoint(album['totalPlayNum'])
        if totalPlayNum > 100000000:
            album['totalPlayNum'] = '%.4f 亿次' % (totalPlayNum / 100000000)
        elif totalPlayNum > 10000:
            album['totalPlayNum'] = '%.2f 万次' % (totalPlayNum / 10000)
        else:
            album['totalPlayNum'] = '%d次' % (totalPlayNum)

        album['playLength'] = '%.2f 分钟' % (album['playLength'] / 60.0)

        if album['cid'] == 1:
            album['type'] = '电影'
        elif album['cid'] == 2:
            album['type'] = '电视剧'
        else:
            album['type'] = ''

        self.render("show.html", alubm=album)

class RandomVideoUrlHandle(BaseHandler):
    def get(self, name):
        self.finish(tv.db.GetVideoCache(name))

    def post(self, name):
        if name == '':
            body = self.request.body
            name = hashlib.md5(body).hexdigest().upper()
            self.db.set(name, body.decode())
            self.db.expire(name, 60) # 1 分钟有效
            self.finish(name)

class LoginHandler(BaseHandler):
    def initialize(self):
        pass

    def check_user_id(self):
        self.user_id = self.get_argument('user_id')
        status = 'YES'
        con = Connection('localhost', 27017)
        user_table = con.kola.users

        json = user_table.find_one({'user_id' : self.user_id})
        if json:
            status = json['status']
        else:
            user_table.insert({'user_id' : self.user_id, 'status' : 'YES'})

        if status == 'NO' or self.user_id == None or self.user_id == '':
            raise tornado.web.HTTPError(401, 'Missing key %s' % self.user_id)

        # 登录检查，生成随机 KEY
        redis_db = redis.Redis(host='127.0.0.1', port=6379, db=1)
        if not redis_db.exists(self.user_id):
            key = (self.user_id + uuid.uuid4().__str__() + self.request.remote_ip).encode()
            key = hashlib.md5(key).hexdigest().upper()
            redis_db.set(self.user_id, key)
            redis_db.set(key, self.request.remote_ip)
        else:
            key = redis_db.get(self.user_id).decode()
            redis_db.set(key, self.request.remote_ip)
        redis_db.expire(self.user_id, 60) # 一分钟过期
        redis_db.expire(key, 60) # 一分钟过期

        return key

    def get(self):
        ret = {
            'key'    : self.check_user_id(),
            'server' : self.request.protocol + '://' + self.request.host,
            'next'   : 60,   # 下次登录时间
        }

        cmd = self.get_argument('cmd', '1')
        if cmd == '1':
            if self.user_id == '000001':
                timeout = 0
            else:
                timeout = 0.3
            count = self.get_argument('count', 1)

            if self.user_id == '000001':
                cmd = tv.command.GetCommand(timeout, count)
            else:
                cmd = None
            if cmd:
                ret['dest'] =  self.request.protocol + '://' + self.request.host + '/video/upload'
                ret['command'] = cmd
                if self.user_id == '000001':
                    ret['next'] = 0
            else:
                tv.CommandEmptyMessage()

        self.finish(json.dumps(ret))

    def post(self):
        self.finish('OK')

class IndexHandler(BaseHandler):
    def initialize(self):
        pass

    def get(self):
        args = {}
        args['page'] = 0
        args['size'] = 20
        args['sort'] = '周播放最多'

        _items, _ = tv.GetMenuAlbumListByName('电视剧', args)
        newtv = []
        for i in _items:
            _item = {}
            _item['id'] = i['vid']
            _item['title'] = i['albumName']
            if 'publishTime' in i:
                _item['time'] = i['publishTime']
            elif 'publishYear' in i:
                _item['time'] = i['publishYear']
            else:
                _item['time'] = ''
#            _item['time'] = _item['time'].replace("集更新", "集|更新至")
#            if "更新" in _item['time']:
#                _item['time'] = "更"+ _item['time'].split("更")[1]
            if 'smallVerPicUrl' in i:
                _item['pic'] = i['smallVerPicUrl']
            elif 'smallVerPicUrl' in i:
                _item['pic'] = i['smallVerPicUrl']
            elif 'largeHorPicUrl' in i:
                _item['pic'] = i['largeHorPicUrl']
            elif 'largeVerPicUrl' in i:
                _item['pic'] = i['largeVerPicUrl']
            else:
                _item['pic'] = ''
            newtv.append(_item)

        toptv = []
        x = 0
        args['page'] = 0
        args['size'] = 20
        args['sort'] = '评分最高'

        _items, _ = tv.GetMenuAlbumListByName('电视剧', args)
        for i in _items:
            _item = {}
            if x == 0:
                _item['info'] = i['albumName']
            x += 1
            _item['id'] = i['vid']
            _item['title'] = i['albumName']
            if 'videoScore' in i:
                _item['score'] = '%.2f' % (float(i['videoScore']))
            else:
                _item['score'] = ''

            if 'smallVerPicUrl' in i:
                _item['pic'] = i['smallVerPicUrl']
            elif 'smallVerPicUrl' in i:
                _item['pic'] = i['smallVerPicUrl']
            elif 'largeHorPicUrl' in i:
                _item['pic'] = i['largeHorPicUrl']
            elif 'largeVerPicUrl' in i:
                _item['pic'] = i['largeVerPicUrl']
            else:
                _item['pic'] = ''
            toptv.append(_item)

        args['page'] = 0
        args['size'] = 20
        args['sort'] = '周播放最多'
        _items, _ = tv.GetMenuAlbumListByName('电影', args)
        newmovie = []
        for i in _items:
            _item = {}
            _item['id'] = i['vid']
            _item['title'] = i['albumName']
            if 'publishTime' in i:
                _item['time'] = i['publishTime']
            elif 'publishYear' in i:
                _item['time'] = i['publishYear']
            else:
                _item['time'] = ''
#            _item['time'] = _item['time'].replace("集更新", "集|更新至")
#            if "更新" in _item['time']:
#                _item['time'] = "更"+ _item['time'].split("更")[1]
            if 'smallVerPicUrl' in i:
                _item['pic'] = i['smallVerPicUrl']
            elif 'smallVerPicUrl' in i:
                _item['pic'] = i['smallVerPicUrl']
            elif 'largeHorPicUrl' in i:
                _item['pic'] = i['largeHorPicUrl']
            elif 'largeVerPicUrl' in i:
                _item['pic'] = i['largeVerPicUrl']
            else:
                _item['pic'] = ''
            newmovie.append(_item)

        topmovie = []
        x = 0
        args['page'] = 0
        args['size'] = 20
        args['sort'] = '评分最高'

        _items, _ = tv.GetMenuAlbumListByName('电影', args)
        for i in _items:
            _item = {}
            if x == 0:
                _item['info'] = i['albumName']
            x += 1
            _item['id'] = i['vid']
            _item['title'] = i['albumName']

            if 'videoScore' in i:
                _item['score'] = '%.2f' % (float(i['videoScore']))
            else:
                _item['score'] = ''

            if 'smallVerPicUrl' in i:
                _item['pic'] = i['smallVerPicUrl']
            elif 'smallVerPicUrl' in i:
                _item['pic'] = i['smallVerPicUrl']
            elif 'largeHorPicUrl' in i:
                _item['pic'] = i['largeHorPicUrl']
            elif 'largeVerPicUrl' in i:
                _item['pic'] = i['largeVerPicUrl']
            else:
                _item['pic'] = ''
            topmovie.append(_item)

        self.render("index.html",newtv=newtv,toptv=toptv,topmovie=topmovie,newmovie=newmovie)

class ViewApplication(tornado.web.Application):
    def __init__(self):
        settings = dict(
            debug = False,
            gzip = True,
            login_url = "/login",
            template_path = "templates",
            cookie_secret = 'z1DAVh+WTvyqpWGmOtJCQLETQYUznEuYskSF062J0To=',
            #xsrf_cookies = True,
            autoescape = None,
            autoreload = True
        )

        handlers = [
            (r'/video/list',       AlbumListHandler),
            (r'/video/getvideo',   GetVideoHandler),
            (r'/video/upload',     UploadHandler),          # 接受客户端上网的需要解析的网页文本
            (r'/video/getplayer',  GetPlayerHandler),       # 得到下载地位
            (r'/video/getmenu',    GetMenuHandler),         #
            (r'/video/getinfo',    GetKolaInfoHandler),     #

            (r'/video/geturl',     GetVideoPlayerUrlHandle),
            (r'/video/urls(.*)',   RandomVideoUrlHandle),
            (r'/login',            LoginHandler),           # 登录认证
            (r'/show',             ShowHandler),
            (r'/',                 IndexHandler),

            (r"/static/(.*)",      tornado.web.StaticFileHandler, {"path": "static"}),
            (r"/scripts/(.*)",     tornado.web.StaticFileHandler, {"path": "scripts"}),
        ]

        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    http_server = ViewApplication()
    http_server.listen(9991, xheaders = True)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
