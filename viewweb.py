#!env python3
# -*- coding: utf-8 -*-

import base64
import hashlib
import json
import os
import sys
import traceback
from urllib.parse import unquote
import zlib

import redis
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web

from barcode import get_barcode
from kola import log, utils, DB, City, KolatvServer


try:
    from barcode.writer import ImageWriter
except ImportError:
    ImageWriter = None


kolas = KolatvServer()

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        chipid  = self.get_argument('chipid', None)
        serial  = self.get_argument('serial', None)
        key = self.get_secure_cookie('user_id', None, 1)
        return kolas.CheckUser(key, self.request.remote_ip, chipid, serial)

    def prepare(self):
        if self.request.method == "POST" and self.request.body:
            body = unquote(self.request.body.decode())           # URLDecode
            body = base64.decodebytes(body.encode())             # BASE64_Decode
            if int(body[0]) == 0x5A and int(body[1]) == 0xA5:
                decompress = zlib.decompressobj(-zlib.MAX_WBITS) # ZLIB Decompress
                self.request.body = decompress.decompress(body[2:])
                self.request.body += decompress.flush()
            else:
                self.request.body = body


class AlbumVidCheckHandler(BaseHandler):
    def get(self):
        vids = self.get_argument('vid', '')
        ret = kolas.GetAlbumFailure(vids)

        self.finish(tornado.escape.json_encode(ret))

    def post(self):
        if self.request.body:
            vids = tornado.escape.to_basestring(self.request.body)
            ret = kolas.GetAlbumFailure(vids)

            self.finish(tornado.escape.json_encode(ret))

class AlbumListHandler(BaseHandler):
    def argument(self):
        args = {}
        cid = self.get_argument('cid', '')
        args['page']  = int(self.get_argument('page', 0))
        args['size']  = int(self.get_argument('size', 20))
        args['full']  = int(self.get_argument('full', 0))
        if cid:
            args['cid'] = cid

        engine = self.get_argument('engine', '')
        if engine:
            args['engine'] = engine

        key = self.get_argument('key', '')
        if key:
            args['key'] = key

        value = self.get_argument('value', '')
        if value: args['value'] = value

        return args, self.get_argument('menu', ''), cid, self.get_argument('vid', '')

    @tornado.web.authenticated
    def get(self):
        args, menu, cid, vid = self.argument()

        if cid:
            albumlist, args['total'] = kolas.GetMenuAlbumListByCid(cid, args)
        elif menu:
            albumlist, args['total'] = kolas.GetMenuAlbumListByName(menu, args)
        elif vid:
            albumlist, args['total'] = kolas.GetMenuAlbumListByVidList(vid, args)

        if albumlist: args['result'] = albumlist

        self.finish(tornado.escape.json_encode(args))

    @tornado.web.authenticated
    def post(self):
        args, menu, cid, vid = self.argument()

        if self.request.body:
            try:
                umap = tornado.escape.json_decode(self.request.body)
                if 'vid' in umap:
                    vid = umap['vid']
                args.update(umap)
            except:
                t, v, tb = sys.exc_info()
                log.error("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
                raise tornado.web.HTTPError(400)

        if cid:
            albumlist, args['total'] = kolas.GetMenuAlbumListByCid(cid, args)
        elif menu:
            albumlist, args['total'] = kolas.GetMenuAlbumListByName(menu, args)
        elif vid:
            albumlist, args['total'] = kolas.GetMenuAlbumListByVidList(vid, args)

        if albumlist: args['result'] = albumlist

        self.finish(tornado.escape.json_encode(args))

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
        videos, count = kolas.GetVideoListByPid(pid, args)

        args['count'] = count
        args['videos'] = videos
        self.finish(tornado.escape.json_encode(args))

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
    def post(self):
        body = self.request.body.decode()
        url = self.request.protocol + '://' + self.request.host  + '/video/urls'
        if body and len(body) > 0:
            text = self.sohuVideoUrl(body, url)
            if text == '':
                text = self.QQVideoUrl(body, url)
            self.finish(text)
        else:
            raise tornado.web.HTTPError(404)

    def QQVideoUrl(self, text, url):
        try:
            urls_list = tornado.escape.json_decode(text)
            if type(urls_list) == str:
                urls_list = tornado.escape.json_decode(urls_list)

            max_duration = 0.0
            m3u8 = ''
            for u in urls_list:
                duration = u['time']
                m3u8 += '#EXTINF:%.0f\n%s\n' % (duration, u['url'])
                if duration > max_duration:
                    max_duration = duration

            m3u8 = '#EXTM3U\n#EXT-X-TARGETDURATION:%.0f\n%s#EXT-X-ENDLIST\n' % (max_duration, m3u8)
            name = hashlib.md5(m3u8.encode()).hexdigest()[16:]
            kolas.db.SetVideoCache(name, m3u8)

            return url + name
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine._ParserRealUrlStep2: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return ''

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

                    url_key = url_tmp.split('|')
                    if len(url_key) < 4:
                        continue

                    start = url_key[0]
                    key = url_key[3]

                    #start, _, _, key, _, _, _, _,_ = url_tmp.split('|')
                    u_tmp = '%s%s?key=%s' % (start[:-1], new, key)

                    if video_count == 1:
                        return u_tmp
                    m3u8 += '#EXTINF:%.0f\n%s\n' % (duration, u_tmp)
                    if duration > max_duration:
                        max_duration = duration

                m3u8 = '#EXTM3U\n#EXT-X-TARGETDURATION:%.0f\n%s#EXT-X-ENDLIST\n' % (max_duration, m3u8)

                name = hashlib.md5(m3u8.encode()).hexdigest()[16:]
                kolas.db.SetVideoCache(name, m3u8)

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
    def initialize(self):
        super().initialize()

    @tornado.web.authenticated
    def get(self):
        ret = []
        cid = self.get_argument('cid', '')
        name  = self.get_argument('name', '')
        if cid:
            cid = cid.split(',')
            ret = kolas.GetMenuJsonInfoById(cid)
        elif name != '':
            name = name.split(',')
            ret =  kolas.GetMenuJsonInfoByName(name)
        else:
            ret =  kolas.GetMenuJsonInfoByName([])

        self.finish(tornado.escape.json_encode(ret))

class GetKolaInfoHandler(BaseHandler):
    def get(self):
        ret =  kolas.GetVideoSource()

        self.finish(tornado.escape.json_encode(ret))

class CityHandler(BaseHandler):
    city = City()
    def get(self):
        name = self.get_argument('name', '');
        cid = self.get_argument('cid', '')
        if cid == '':
            ret = self.city.GetListByFullName(name)

            self.finish(tornado.escape.json_encode(ret))
        else:
            self.finish(self.city.GetCiyByFullName(name))

class ADHandler(BaseHandler):
    def initialize(self):
        pass

    def GetUrl(self, ret):
        return '/'

    def get(self):
        ret = {}
        _type = self.get_argument('type', '')
        video_name = self.get_argument('video', '')

        if _type == 'image':
            pass
        elif _type == 'video':
            pass

        ret[_type] = _type
        ret['video'] = video_name

        self.redirect(self.GetUrl(ret))

class RandomVideoUrlHandle(BaseHandler):
    def initialize(self):
        pass

    def get(self, name):
        self.finish(kolas.db.GetVideoCache(name))

    def post(self, name):
        if name == '':
            body = self.request.body
            name = hashlib.md5(body).hexdigest().upper()
            self.db.set(name, body.decode())
            self.db.expire(name, 60) # 1 分钟有效
            self.finish(name)

# / userinfo?client_id=100&number=10&serial=sssssss
class UserInfoHandler(BaseHandler):
    user_table = DB().user_table

    def initialize(self):
        pass

    def get(self):
        ret = []
        _filter = {}

        value = self.get_argument('serial', '')
        if value:
            _filter['serial'] = value

        value = self.get_argument('client_id', '')
        if value:
            _filter['client_id'] = utils.autoint(value)

        value = self.get_argument('number', '')
        if value:
            _filter['number'] = utils.autoint(value)

        cursor = self.user_table.find(_filter)
        for x in cursor:
            del x['_id']
            ret.append(x)

        self.finish(tornado.escape.json_encode(ret))

class SerialHandler(BaseHandler):
    user_table = DB().user_table
    def initialize(self):
        pass

    def GenBarcode(self, path, codes):
        ret = []
        for code in codes:
            bcode = get_barcode('code39', code)
            fn = os.path.join(path, code)
            filename = bcode.save(fn)
            fn = os.path.join('../images', os.path.basename(filename))
            ret.append((code, fn))

        return ret

    def GetClientMaxNumber(self, client_id):
        cursor = self.user_table.find({'client_id' : client_id})
        if cursor.count() > 0:
            cursor.sort([('number',  -1)])
            return cursor[0]['number']

        return 0

    def Serial(self, client_id, sid, skip=True, create=True):
        while True:
            key = str(sid) + '-' + str(client_id)
            key = hashlib.sha1(key.encode()).hexdigest().upper()
            key = hashlib.md5(key.encode()).hexdigest().upper()[:16]

            # 系统中不存在该序列号
            json = self.user_table.find_one({'serial' : key})
            if json == None: # 序列号不存在，则生成序号加入数据库中
                if create:
                    self.user_table.insert({'serial': key, 'client_id' : client_id, 'number' : sid, 'chipid': ''})
                break
            else:
                if skip:
                    print("Found seiral client: %d, number: %d,  serial: %s", client_id, sid, key)
                    sid += 1
                else:
                    break

        return key, sid

    # /serial?client_id=1&number=1&start=1
    def get(self):
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, 'images')

        if not os.path.isdir(path):
            try:
                os.mkdir(path)
            except OSError as e:
                print('Error:', e)

        client_id = utils.autoint(self.get_argument('client_id', 0))
        number    = utils.autoint(self.get_argument('number', 0))
        start     = utils.autoint(self.get_argument('start', 0))
        image     = self.get_argument('image', '0')

        codes = []
        skip = False
        if start == 0:
            start = self.GetClientMaxNumber(client_id) + 1
            skip = True

        for i in range(start, start + number):
            s,sid = self.Serial(client_id, i, skip, image=='0')
            codes.append((sid, s))

        enableImage = image=='1'
        if enableImage:
            ret  = self.GenBarcode(path, codes)
        else:
            ret = []
            for num, v in codes:
                ret.append((num, v, ''))
        if type == 'text':
            for num, v in codes:
                self.write("%s %s\n" % (num, v))
        else:
            self.render("barcode.html", barcodes=ret, image=enableImage)

class OnlineUserHandler(tornado.web.RequestHandler):
    def get(self):
        onlines = kolas.GetOnline()
        allusers = kolas.GetAllUser()
        self.render("online.html", onlines=onlines, allusers=allusers)

class LoginHandler(BaseHandler):
    def initialize(self):
        self.chipid  = self.get_argument('chipid', '')
        self.serial  = self.get_argument('serial', '')
        self.area    = self.get_argument('area', '')
        self.cmd     = self.get_argument('cmd', '0')
        self.version = self.get_argument('version', '')

    def post(self):
        js = tornado.escape.json_decode(self.request.body)
        if js:
            if 'cmd'     in js: self.cmd     = js['cmd']
            if 'chipid'  in js: self.chipid  = js['chipid']
            if 'serial'  in js: self.serial  = js['serial']
            if 'area'    in js: self.area    = js['area']
            if 'version' in js: self.version = js['version']

        key = kolas.Login(self.chipid, self.serial, self.request.remote_ip, self.area)

        if key:
            nextTime = kolas.ActiveTime
            self.set_secure_cookie("user_id", key, 1)
        else:
            print('(%s) Missing serial: %s, chipid: %s' % (self.request.remote_ip, self.serial, self.chipid))
            nextTime = 3600

        ret = {
            'key'   : key,
            'server': self.request.protocol + '://' + self.request.host,
            'next'  : nextTime,   # 下次登录时间
        }

        if not key:
            ret['message'] = '序列号错误，请与供应商联系.'

        #if self.cmd == '1':
        #    timeout = 0.3
        #    cmd = tv.command.GetCommand(timeout, 1)
        #    if cmd:
        #        ret['dest'] =  self.request.protocol + '://' + self.request.host + '/video/upload'
        #        ret['command'] = cmd
        #        if self.serial == '000001':
        #            ret['next'] = 0
        #        ret['script'] = utils.GetScript('command', 'test', [json.dumps(cmd), ''])


        self.finish(json.dumps(ret))

class EncryptFileHandler(tornado.web.StaticFileHandler):
    def initialize(self, path, default_filename=None):
        super().initialize(path, default_filename)
        self.crypt = True

    def validate_absolute_path(self, root, absolute_path):
        if absolute_path.find('.lua') > 0:
            self.crypt = False
        else:
            self.crypt = True
            absolute_path += '.lua'

        return super().validate_absolute_path(root, absolute_path)

    def Encrypt(self, data):
        if type(data) == str:
            data = data.encode()
        r = bytearray()
        for i in range(0, len(data) - 1):
            x = data[i] ^ 0x4A
            r += bytes([x])

        return bytes(r)

    def write(self, chunk):
        if self._finished:
            raise RuntimeError("Cannot write() after finish().  May be caused "
                               "by using async operations without the "
                               "@asynchronous decorator.")
        if self.crypt:
            chunk = self.Encrypt(chunk)

        self._write_buffer.append(chunk)

class DownloadFileHandler(tornado.web.StaticFileHandler):
    def should_return_304(self):
        return False

class UploadFileHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('update.html')

    def post(self):
        ret = {}
        check_pass = False

        projectName = self.get_argument('projectname', '')
        password = self.get_argument('password', '')
        ret['version'] = self.get_argument('version', '')
        ret['chanagelog'] = self.get_argument('changelog', '')

        if not (projectName and password and ret['version'] and len(self.request.files['file'])):
            self.write('项目名、密码、版本号不能加空，至少要上传一个文件！')
            return

        passwd_md5 = hashlib.md5(password.encode()).hexdigest()

        upload_path=os.path.join(os.path.dirname(__file__), 'files')  #文件的暂存路径
        upload_path=os.path.join(upload_path, projectName)

        if not os.path.exists(upload_path):
            os.mkdir(upload_path)

        pwdfile = os.path.join(upload_path, 'passwd')

        if not os.path.isfile(pwdfile):
            with open(pwdfile,'wb') as up:
                up.write(passwd_md5.encode())

            check_pass = True
        else:
            with open(pwdfile) as up:
                if up.read() == passwd_md5:
                    check_pass = True

        if check_pass == False:
            self.write('密码与项目不符，请重新上传！')
            return

        file_metas=self.request.files['file']    #提取表单中‘name’为‘file’的文件元数据
        ret['files'] = []
        for meta in file_metas:
            segment = {}
            filename = meta['filename']
            jsonfile = os.path.basename(filename)

            segment['name'] = jsonfile
            segment['md5']  = hashlib.md5(meta['body']).hexdigest()
            segment['href'] = self.request.protocol + '://' + self.request.host  + '/files/' + projectName + '/' + filename
            ret['files'].append(segment)

            filepath=os.path.join(upload_path,filename)
            with open(filepath,'wb') as up:      #有些文件需要已二进制的形式存储，实际中可以更改
                up.write(meta['body'])

        infofile = os.path.join(upload_path, 'info.json')
        with open(infofile,'wb') as up:
            up.write(json.dumps(ret, indent=4, ensure_ascii=False).encode())

        self.redirect(self.request.protocol + '://' + self.request.host  + '/files/' +  projectName + '/info.json')

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
            (r'/video/vidcheck',   AlbumVidCheckHandler),
            (r'/video/list',       AlbumListHandler),
            (r'/video/getvideo',   GetVideoHandler),
            (r'/video/getplayer',  GetPlayerHandler),       # 得到下载地位
            (r'/video/getmenu',    GetMenuHandler),         #
            (r'/video/getinfo',    GetKolaInfoHandler),     #

            (r'/video/urls(.*)',   RandomVideoUrlHandle),
            (r'/login',            LoginHandler),           # 登录认证
            (r'/ad',               ADHandler),              # 广告
            (r'/city',             CityHandler),            # 城市编码

            (r'/admin/userinfo',   UserInfoHandler),        # 用户信息
            (r'/admin/serial',     SerialHandler),          # 生成序列号
            (r'/admin/update',     UploadFileHandler),
            (r'/admin/online',     OnlineUserHandler),

            (r"/files/(.*)",       DownloadFileHandler, {"path": "files"}),
            (r"/static/(.*)",      tornado.web.StaticFileHandler, {"path": "static"}),
            (r"/images/(.*)",      tornado.web.StaticFileHandler, {"path": "images"}),
            (r"/scripts/(.*)",     EncryptFileHandler, {"path": "scripts"}),
        ]

        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    db = redis.Redis(host='127.0.0.1', port=6379, db=4)
    db.flushdb()

    # debug|info|warning|error|none
    tornado.options.options.logging = "none"
    tornado.options.parse_command_line()
    ViewApplication().listen(9991, xheaders = True)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
