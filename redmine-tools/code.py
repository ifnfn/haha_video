#!env python3
#encoding=utf8
#coding=utf8

import json
import re
import sys
import time
import traceback
import urllib.request

import httplib2


username = 'zhuzhg'
password = 'uagvPAs4csIZ'
gerrit = None
socket_timeout = 3000
MAX_TRY = 3

def wget(url, times = 0):
    if times > MAX_TRY:
        return ''

    try:
        h = httplib2.Http(timeout=socket_timeout)
        h.add_credentials( username, password)
        resp, content = h.request(url, 'GET' )

        status = resp['status']
        if status != '200' and status != '304':
            print('status %s, try %d ...' % (status, times + 1))
            return wget(url, times + 1)

        return content.decode();
    except:
        t, v, tb = sys.exc_info()
        print("KolaClient.GetUrl: %s %s, %s, %s" % (url, t, v, traceback.format_tb(tb)))
        return wget(url, times + 1)

def autostr(i):
    if i == None:
        return ''
    if type(i) == int:
        return str(i)
    else:
        return i

def autoint(i):
    if i == None:
        return 0

    if type(i) == str:
        return i and int(i) or 0
    else:
        return i

class Resource:
    def __init__(self, js=None):
        self.resource = js
        self.params = {}
        self.children = []
        self.offset = 0
        self.limit = 400

    def __getattr__(self, key):
        if self.resource and key in self.resource:
            if key in ['created', 'updated']:
                t = self.resource[key]
                t = re.sub('\.\d*', '', t)
                return time.mktime(time.strptime(t,'%Y-%m-%d %H:%M:%S'))
            return self.resource[key]

    def __getitem__(self, item):
        if len(self.children) <= item:
            self.Query()
        if len(self.children) > item:
            return self.children[item]

        raise StopIteration()

class Auther:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.lines_deleted = 0
        self.lines_inserted = 0
        self.changes = []

    def Show(self):
        print('%-20s %-40s %6d %6d' %( self.name, self.email, self.lines_deleted, self.lines_inserted))
        for c in self.changes:
            c.Show()

class File(Resource):
    '''
    "drivers/vout/gx3113C_vout.c": {
      "status": "A",
      "lines_inserted": 1794
    },
    "script/rule_gx3113C.mk": {
      "lines_inserted": 2,
      "lines_deleted": 1
    }
    '''
    def __init__(self, name, res):
        self.name = name
        self.resource = res

    def __str__(self):
        return self.name

class Revision(Resource):
    '''
    "3d85f951a237e90b4f30ebb2df6c40226775003c": {
      "_number": 1,
      "commit": {
        "subject": "13091: flv 的网络播放一段时间退出",
        "parents": [
          {
            "subject": "Merge \"12717: <V5100>seek后马上操作快进，有时画面会闪一下（6605 ecos）\" into v1.9-dev",
            "commit": "62d8a9d09da86c190555587432c7f3267d5b9ff1"
          }
        ],
        "message": "13091: flv 的网络播放一段时间退出\n\nChange-Id: Id62ce28a5306d27dc1e347ecfac6952fe55f6f49\n",
        "committer": {
          "email": "linxsh@nationalchip.com",
          "tz": 480,
          "name": "linxsh",
          "date": "2014-07-29 07:00:30.000000000"
        },
        "author": {
          "email": "linxsh@nationalchip.com",
          "tz": 480,
          "name": "linxsh",
          "date": "2014-07-29 07:00:30.000000000"
        }
      }
    }
    '''
    def __init__(self, change, name, res, base):
        super().__init__()
        self.change = change
        self.project = change.project
        self.name = name
        self.resource = res
        self.base = base           # 跟哪个版本比较文件
        self.files = []
        self.lines_inserted = 0
        self.lines_deleted = 0
        self.ExtensName = ['.*?\.[ch]|.*?.\.[ch]pp|.*?\.[ch]xx|.*?\.mk|Makefile|build|config|env.sh'] # 文件扩展名
        self.ExcludeName = [ # 排除文件
                'firmware',
                '(.*?)\.bin',
        ]

        self.GetChangeLine()

        auther_js = None
        if 'commit' in res:
            if 'author' in res['commit']:
                auther_js = res['commit']['author']
            elif 'committer' in res['commit']:
                auther_js = res['commit']['committer']

        if auther_js:
            auther = gerrit.GetAuther(auther_js['name'], auther_js['email'])
            auther.lines_inserted += self.lines_inserted
            auther.lines_deleted += self.lines_deleted
            auther.changes.append(self.change)

    def NewFile(self, name, res):
        for p in list(self.ExcludeName):
            if re.findall(p, name):
                print('Exclude file:', name)
                return None

        if name in self.ExcludeName:
            print('Exclude file:', name)
            return None

        for p in list(self.ExtensName):
            if re.findall(p, name):
                return File(name, res)

        if name in self.ExtensName:
            return File(name, res)

        print(name, res)

    def GetChangeLine(self):
        url = '/changes/%s/revisions/%s/files' % (self.change._number, self.name)

        if self.base:
            url += '?base=' + self.base
        file_js = gerrit.arrayGet(url)
        for (k, v) in file_js.items():
            if k != '/COMMIT_MSG':
                f = self.NewFile(k,v)
                if f:
                    self.lines_inserted += autoint(f.lines_inserted)
                    self.lines_deleted += autoint(f.lines_deleted)
                    self.files.append(f)

    def __str__(self):
        return self.name

    def Show(self):
        print('\t\t%s  %6d%6d' % (self.name, self.lines_inserted, self.lines_deleted))

class Change(Resource):
    '''
    {
      "kind": "gerritcodereview#change",
      "id": "demo~master~Idaf5e098d70898b7119f6f4af5a6c13343d64b57",
      "project": "demo",
      "branch": "master",
      "change_id": "Idaf5e098d70898b7119f6f4af5a6c13343d64b57",
      "subject": "One change",
      "status": "NEW",
      "created": "2012-07-17 07:18:30.854000000",
      "updated": "2012-07-17 07:19:27.766000000",
      "mergeable": true,
      "insertions": 26,
      "deletions": 10,
      "_sortkey": "001e7057000006dc",
      "_number": 1756,
      "owner": {
        "name": "John Doe"
      },
    },
    '''
    def __init__(self, project, res):
        super().__init__()
        self.project = project
        self.resource = res
        self.revisions = []
        if self._number == 11556:
            pass
            #print(res)

        rev_js = {}
        set_total = 0
        for (k, v) in res['revisions'].items():
            v['name'] = k
            rev_js[v['_number']] = v
            set_total += 1

        base = None
        for i in range(set_total):
            r = rev_js[i + 1]
            k = r['name']
            rev = Revision(self, k, v, base)
            self.revisions.append(rev)
            base = k

    def Show(self):
        print('\t%d %s %s' % (self._number, time.strftime('%Y-%m-%d %X', time.gmtime(self.created)), self.subject[:80]))
        for rev in self.revisions:
            rev.Show()
        print()

class Changes(Resource):
    def __init__(self, project):
        super().__init__()
        self.project = project

    def Query(self, **params):
        self.params.update(**params)
        name = self.params.get('name', '.*')
        status = self.params.get('status', 'ACTIVE')

        url = '/changes/?q=status:merged+project:%s&o=ALL_REVISIONS&o=ALL_COMMITS&n=%d&S=%d' % (self.project.name, self.limit, self.offset)
        self.resource = gerrit.arrayGet(url)
        print(len(self.resource))
        for i in self.resource:
            c = Change(self.project, i)
            if c.created >= self.project.create_time or self.project.create_time == 0:
                self.children.append(c)
                self.offset += 1
            else:
                pass

    def Show(self):
        for c in self.children:
            c.Show()

class Project(Resource):
    def __init__(self, name, v, created=0):
        '''
          "androidtv/3601_bootloader": {
            "kind": "gerritcodereview#project",
            "id": "androidtv%2F3601_bootloader",
            "state": "ACTIVE"
          },
        '''
        super().__init__()
        self.number = 0
        self.reviews = []
        self.name = name
        self.resource = v
        self.create_time = created
        self.changes = Changes(self)

    def __str__(self):
        return self.name

    def Sync(self):
        for _ in self.changes:
            pass

    def Show(self):
        print(self.description)
        for c in self.changes:
            print(c._number, time.strftime('%Y-%m-%d %X', time.gmtime(c.created)), c.subject[:80])
            c.Show()

class Projects(Resource):
    def __init__(self):
        super().__init__()
        self.projects = []
        self.create_time = 0

    def Query(self, **params): #name, status):
        self.params.update(**params)
        name = self.params.get('name', '.*')
        status = self.params.get('status', 'ACTIVE')
        self.create_time = self.params.get('created', 0)

        if self.create_time:
            self.create_time = time.mktime(time.strptime(self.create_time,'%Y-%m-%d'))

        url = '/projects/?format=JSON&d'
        self.resource = gerrit.arrayGet(url)
        for (k, v) in self.resource.items():
            if re.findall(name, k) and v['state'] == status:
                p = Project(k, v, self.create_time)
                self.projects.append(p)

    def Sync(self):
        for p in self.projects:
            p.Sync()

    def Show(self):
        for (k,v) in gerrit.authers.items():
            v.Show()

class Gerrit(object):
    def __init__(self, baseUrl):
        self.project = []
        self.baseUrl = baseUrl
        self.authers = {}

        self.mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()

        self.opener = urllib.request.build_opener(urllib.request.HTTPDigestAuthHandler(self.mgr))
        urllib.request.install_opener(self.opener)

    def GetAuther(self, name, email):
        if name in self.authers:
            auther = self.authers[name]
        else:
            auther = Auther(name, email)
            self.authers[name] = auther

        return auther

    def rawGet(self, url):
        if url.find('http://') < 0:
            url = self.baseUrl + url

        result = wget(url)
        if result[:4] == ")]}'":
            return result[5:]

    def arrayGet(self, url):
        result = self.rawGet(url)
        return json.loads(result)

    def GetProjects(self, **param):
        projects = Projects()
        projects.Query(**param)

        return projects

if __name__ == '__main__':
    host = 'http://git.nationalchip.com/gerrit/a'
    #host = 'http://192.168.110.254/gerrit/a'
    gerrit=Gerrit(host)
    projects = gerrit.GetProjects(name='goxceed/gxavdev', created='2014-06-01')
    projects.Sync()
    projects.Show()
