#! /usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib
import json
import sys, os, time
import traceback
import uuid

import redis
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
from barcode import get_barcode

try:
    from barcode.writer import ImageWriter
except ImportError:
    ImageWriter = None

from kola import BaseHandler, log, utils, KolaCommand, element, DB, City


class KolatvServer:
    def __init__(self):
        self.db = DB()
        self.command = KolaCommand()
        self.MenuList = {}
        self.UpdateAlbumFlag = False
        self.MenuList['直播']   = element.LivetvMenu('直播')           # 200
        self.MenuList['电影']   = element.MovieMenu('电影')            # 1
        self.MenuList['电视剧'] = element.TVMenu('电视剧')              # 2
        self.MenuList['动漫']   = element.ComicMenu('动漫')            # 3
        self.MenuList['记录片'] = element.DocumentaryMenu('记录片')     # 4
        self.MenuList['综艺']   = element.ShowMenu('综艺')             # 5
        #self.MenuList['教育']   = element.EduMenu('教育')              # 6
        #self.MenuList['娱乐']   = element.YuleMenu('娱乐')             # 7
        #self.MenuList['旅游']   = element.TourMenu('旅游')             # 8

    def GetVideoSource(self):
        return {
            'source' : ['腾讯', '搜狐', '爱奇艺'],
            'resolution' : ['1080P', '原画质', '720P', '超清', '高清', '标清', '默认']
        }

    def GetMenuJsonInfoById(self, cid_list):
        ret = []
        count = len(cid_list)
        for _, menu in list(self.MenuList.items()):
            if count == 0 or str(menu.cid) in cid_list:
                ret.append(menu.GetJsonInfo())

        return ret

    def GetMenuJsonInfoByName(self, name_list):
        ret = []
        count = len(name_list)
        for name, menu in list(self.MenuList.items()):
            if count == 0 or name in name_list:
                ret.append(menu.GetJsonInfo())

        return ret

    def _GetMenuAlbumList(self, menu, argument):
        if menu:
            menu.CheckQuickFilter(argument)
            menu.FixArgument(argument)
            return self.db.GetAlbumListJson(argument, menu.cid)

        return [], 0

    def GetAlbumFailure(self, vids):
        return self.db.GetAlbumFailure(vids)

    def GetMenuAlbumListByVidList(self, vids, argument):
        if 'filter' not in argument:
            argument['filter'] = {}
        argument['filter']['vids'] = vids
        return self.db.GetAlbumListJson(argument)

    def GetMenuAlbumListByName(self, menuName, argument):
        menu = self.FindMenu(menuName)
        return self._GetMenuAlbumList(menu, argument)

    def GetMenuAlbumListByCid(self, cid, argument):
        cid = utils.autoint(cid)
        menu = self.FindMenuById(cid)
        return self._GetMenuAlbumList(menu, argument)

    def GetVideoByVid(self, vid):
        video = self.db.FindVideoJson(vid=vid)

        return video

    def GetVideoListByPid(self, pid, argument):
        return self.db.GetVideoListJson(pid=pid, arg=argument)

    def FindMenuById(self, cid):
        for _, menu in list(self.MenuList.items()):
            if menu.cid == cid:
                return menu

        return None

    def FindMenu(self, name):
        if name in self.MenuList:
            return self.MenuList[name]
        else:
            return None

    def CommandEmptyMessage(self):
        if self.UpdateAlbumFlag == True:
            self.UpdateAlbumFlag = False

tv = KolatvServer()

class AlbumVidCheckHandler(BaseHandler):
    def get(self):
        vids = self.get_argument('vid', '')
        ret = tv.GetAlbumFailure(vids)
        self.finish(json.dumps(ret, indent=4, ensure_ascii=False))

    def post(self):
        if self.request.body:
            vids = tornado.escape.to_basestring(self.request.body)
            ret = tv.GetAlbumFailure(vids)
            self.finish(json.dumps(ret, indent=4, ensure_ascii=False))

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
                if 'vid' in umap:
                    vid = umap['vid']
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
    def initialize(self):
        pass

    def get(self):
        pass

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
            tv.db.SetVideoCache(name, m3u8)

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
    def initialize(self):
        super().initialize()

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

class CityHandler(BaseHandler):
    city = City()
    def get(self):
        name = self.get_argument('name', '');
        cid = self.get_argument('cid', '')
        if cid == '':
            ret = self.city.GetListByFullName(name)
            self.finish(json.dumps(ret, indent=4, ensure_ascii=False))
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
        if 'Score' in album:
            album['Score'] = '%.2f' % (float(album['Score']))
        else:
            album['Score'] = ''

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
    def initialize(self):
        pass

    def get(self, name):
        self.finish(tv.db.GetVideoCache(name))

    def post(self, name):
        if name == '':
            body = self.request.body
            name = hashlib.md5(body).hexdigest().upper()
            self.db.set(name, body.decode())
            self.db.expire(name, 60) # 1 分钟有效
            self.finish(name)

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
        self.finish(json.dumps(ret, indent=4, ensure_ascii=False))

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

        return key

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
            s = self.Serial(client_id, i, skip, image=='0')
            codes.append(s)

        enableImage = image=='1'
        if enableImage:
            ret  = self.GenBarcode(path, codes)
        else:
            ret = []
            for v in codes:
                ret.append((v, ''))
        self.render("barcode.html", barcodes=ret, image=enableImage)

class LoginHandler(BaseHandler):
    user_table = DB().user_table
    redis_db = redis.Redis(host='127.0.0.1', port=6379, db=1)

    def initialize(self):
        self.chipid = self.get_argument('chipid', '')
        self.serial = self.get_argument('serial', '')
        self.area   = self.get_argument('area', '')
        self.cmd    = self.get_argument('cmd', '0')

    def check_user_id(self):
        status = 'NO'

        if self.serial in ['000001', '000002', '000003', '000004']:
            status = 'YES'
        elif self.chipid and self.serial: # 默认的测试号
            json = self.user_table.find_one({'serial' : self.serial})
            if json and (json['chipid'] == '' or json['chipid'] == self.chipid):
                status = 'YES'
                self.user_table.update({'serial' : self.serial}, {'$set' : {'chipid': self.chipid, 'updateTime' : time.time()}})

        if status == 'YES':
            # 登录检查，生成随机 KEY
            if not self.redis_db.exists(self.chipid):
                key = (self.chipid + uuid.uuid4().__str__() + self.request.remote_ip).encode()
                key = hashlib.md5(key).hexdigest().upper()
                self.redis_db.set(self.chipid, key)
                self.redis_db.set(key, self.request.remote_ip)
            else:
                key = self.redis_db.get(self.chipid).decode()
                self.redis_db.set(key, self.request.remote_ip)
            self.redis_db.expire(self.chipid, 60) # 一分钟过期
            self.redis_db.expire(key, 60) # 一分钟过期

            return key
        else:
            return ''
            raise tornado.web.HTTPError(401, 'LoginHandler: Missing key %s' % self.chipid)

    def get(self):
        print("GET: [%s] [%s]: serial=%s, chipid=%s" % (self.request.remote_ip, self.area, self.serial, self.chipid))
        ret = {
            'key'    : self.check_user_id(),
            'server' : self.request.protocol + '://' + self.request.host,
            'next'   : 60,   # 下次登录时间
            'image'  : {
                'wallpaper' : '',
            }
        }

#        if self.cmd == '1':
#            ret['script'] = utils.GetScript('command', 'test', ['aaaaa', 'asdfasdfasd'])
#===============================================================================
#         if self.cmd == '1':
#             if self.user_id == '000001':
#                 timeout = 0
#             else:
#                 timeout = 0.3
#             count = self.get_argument('count', 1)
#
#             if self.user_id == '000001':
#                 cmd = tv.command.GetCommand(timeout, count)
#             else:
#                 cmd = None
#             if cmd:
#                 ret['dest'] =  self.request.protocol + '://' + self.request.host + '/video/upload'
#                 ret['command'] = cmd
#                 if self.user_id == '000001':
#                     ret['next'] = 0
#             else:
#                 tv.CommandEmptyMessage()
#===============================================================================

        self.finish(json.dumps(ret))

    def post(self):
        js = tornado.escape.json_decode(self.request.body)
        if js:
            if 'cmd'    in js: self.cmd    = js['cmd']
            if 'chipid' in js: self.chipid = js['chipid']
            if 'serial' in js: self.serial = js['serial']
            if 'area'   in js: self.area   = js['area']

        print("POST: [%s] [%s]: serial=%s, chipid=%s" % (self.request.remote_ip, self.area, self.serial, self.chipid))
        ret = {
            'key'    : self.check_user_id(),
            'server' : self.request.protocol + '://' + self.request.host,
            'next'   : 60,   # 下次登录时间
            'image'  : {
                'wallpaper' : '',
            }
        }

        self.finish(json.dumps(ret))

class IndexHandler(BaseHandler):
    def initialize(self):
        pass

    def get(self):
        args = {}
        args['page'] = 0
        args['size'] = 20
        args['sort'] = '昨日热播'

        _items, _ = tv.GetMenuAlbumListByName('电视剧', args)
        newtv = []
        for i in _items:
            _item = {}
            _item['id'] = i['vid']
            _item['title'] = i['albumName']
            if 'publishTime' in i:
                _item['time'] = time.strftime('%Y-%m-%d', time.gmtime(i['publishTime']))
            elif 'publishYear' in i:
                _item['time'] = i['publishYear']
            else:
                _item['time'] = ''

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
            if 'Score' in i:
                _item['score'] = '%.2f' % (float(i['Score']))
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
        args['sort'] = '昨日热播'
        _items, _ = tv.GetMenuAlbumListByName('电影', args)
        newmovie = []
        for i in _items:
            _item = {}
            _item['id'] = i['vid']
            _item['title'] = i['albumName']
            if 'publishTime' in i:
                _item['time'] = time.strftime('%Y-%m-%d', time.gmtime(i['publishTime']))
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

            if 'Score' in i:
                _item['score'] = '%.2f' % (float(i['Score']))
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
            (r'/',                 IndexHandler),
            (r'/video/vidcheck',   AlbumVidCheckHandler),
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
            (r'/ad',               ADHandler),              # 广告
            (r'/city',             CityHandler),            # 城市编码

            (r'/admin/userinfo',   UserInfoHandler),        # 用户信息
            (r'/admin/serial',     SerialHandler),          # 生成序列号
            (r'/admin/update',     UploadFileHandler),

            (r"/files/(.*)",       DownloadFileHandler, {"path": "files"}),
            (r"/static/(.*)",      tornado.web.StaticFileHandler, {"path": "static"}),
            (r"/images/(.*)",      tornado.web.StaticFileHandler, {"path": "images"}),
            (r"/scripts/(.*)",     EncryptFileHandler, {"path": "scripts"}),
        ]

        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    db = redis.Redis(host='127.0.0.1', port=6379, db=4)
    db.flushdb()

    tornado.options.options.logging = "warning"
    tornado.options.parse_command_line()
    ViewApplication().listen(9991, xheaders = True)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
