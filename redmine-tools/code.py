#!env python3
#encoding=utf8
#coding=utf8


import hashlib
import json
import math
import os
import random
import re
import sys
import time
import traceback
import urllib.request

import httplib2


######################################################################################
# 规则：
#   1. 二进制文件以及二进制转化成的代码，不记入代码统计
#   2. 一次性提交新增代码超过3000行的，不记入代码统计 ?
#   3. 由程序生成的文件，不记入代码统计
#   4. 代码评审小组认定为不良提交，不记入代码统计
#
# 提倡：
#   1. 对各种产生实际意义、实际工作输出的行为都是提倡的，所有工作输入都可以被纳入原始统计数据
#   2. 提倡高频度的提交代码，可以增加更代代码行总数，但可能会造成有效代码率的下降
#   3. 提倡低频度的提交代码，可以提交有效代码率，但影响变更代码行总数
#   4. 提倡代码可追溯性
######################################################################################

# 进入标准差统计的变更行数
MAX_LINE = 5000

# 有效代码文件的扩展名，代码提交者可以提出异意，由评审小组确定
ExtensName = [
    '.*?\.ld|.*?\.[sS]|.*?\.[ch]|.*?\.[ch]pp|.*?\.[ch]xx|.*?\.mk|Makefile|build|config|env\.sh|.*?\.mak',
]

# 全局排除文件，代码提交者可以提出异意，由评审小组确定
GlobalExcludeName = [
    'firmware',
    'serialboot/gx3201-.*?_boot\.c',
    'Bit_Mach\.h',
    'txtlib\.c',
    '.*?\.bin|.*?\.ecc|.*?\.so$|.*?\.a|.*?\.elf',
]

# Change 需要部分文件剔除，由提交者提出申请，由评审小组确定
CustomChanges = {
    11944: ['vodsystem'],
    12058: ['tlsf'],
    12163: ['httpd', 'upnp'],
    '9f899da0840bcd29425a3d7e2fcdc523796fe72b': ['gx_vq_malloc'],                 # 12057
    '37bb3ffad5d5b091ae7971310ebe90bebb877168': ['nand_rootfs', 'rootfs_src_di'], # 12145
    '4f4f15d84d4c3eb77fda1a2c464ed41f983baf96': ['gx_vq_malloc'],                 # 11995
    'fc9763dcbc7a50a7e4efa2fa52be99a6b7ac9d35': ['gx_vq_malloc'],                 # 12016
}

# 黑名单的 change 直接剔除，由评审小组提出，评审后确定，代码提交者可以提出审议
Blacklist = [
    11913,
    11903,
    11704,
    9, 13,     # 记录不全了

]

# 白名单中 chage 当经过筛选后仍不达标，可直接加入， 由提交者提出申请，需要评审小组确定
WhiteList = [
    'a70b25e7a3f1cba87653ffc20fab94c577b4dfea',  # 12195
    '948a879050c325f276e3cb298f8b8ee2fa5db620',  # 11891
    '59807d04f7203af58b19e7144cbc558eb44451e2',  # 12151
    #'1a8e15d41352317cb5745b1a3d7aafc9259de536',  # 11210
    #'49593ea7fc2043564844a578f3b45d9d54066344',  # 10633
    #'f76247574b9ab0652205a9541c914102b575ab76',  # 11668
    #'b74071c1e27e21a5060eca4a5dec79a491bb54c6',  # 11032
]

class Statistics():
    def __init__(self, data):
        self.count = len(data)
        self.data = data
        self.avg = sum(data) / float(self.count)
        self.std = math.sqrt(sum(map(lambda x: (x - self.avg)**2, data)) / self.count)

gerrit = None

def wget(url, times = 0):
    username = 'zhuzhg'
    password = 'uagvPAs4csIZ'
    socket_timeout = 3000
    MAX_TRY = 3
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

def GetCacheUrl(url):
    response = ''
    key = hashlib.md5(url.encode('utf8')).hexdigest().upper()
    filename = './cache/' + key
    # print(filename, url)
    exists = os.path.exists(filename)
    if exists:
        f = open(filename, 'rb')
        response = f.read()
        f.close()
        response = response.decode()
    else:
        response = wget(url)
        if response:
            try:
                f = open(filename, 'wb')
                f.write(response.encode())
                f.close()
            except:
                pass

    return response

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
        self.limit = 50

    def __getattr__(self, key):
        if self.resource and key in self.resource:
            if key in ['created', 'updated']:
                t = self.resource[key]
                t = re.sub('\.\d*', '', t)
                return time.mktime(time.strptime(t,'%Y-%m-%d %H:%M:%S'))
            return self.resource[key]
        elif key == 'lines':
            #return self.lines_inserted + self.lines_deleted
            return self.lines_inserted - self.lines_deleted
            #return max(self.lines_inserted, self.lines_deleted)
            #return int((self.lines_inserted + self.lines_deleted) / 2)

    def __getitem__(self, item):
        if len(self.children) <= item:
            self.Query()
        if len(self.children) > item:
            return self.children[item]

        raise StopIteration()

class Author(Resource):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.lines_deleted = 0
        self.lines_inserted = 0
        self.percent = 0.0
        self.changes = []

    def __lt__(self, other):
        if isinstance(other, Author):
            return self.lines > other.lines

        return NotImplemented

    def AddChange(self, change):
        found = False
        for c in self.changes:
            if c._number == change._number:
                found = True
                break
        if not found:
            self.lines_inserted += change.lines_inserted
            self.lines_deleted +=  change.lines_deleted
            self.changes.append(change)

    def Show(self):
        all = self.lines_inserted + self.lines_deleted
        if all != 0:
            all =  (self.lines_inserted - self.lines_deleted) / all
        #print('%-20s %6d %6d %7.3f, %6.3f%%' %(self.name, self.lines_inserted, self.lines_deleted, all, self.percent * 100.0))
        print('%-20s %6d %6d %7.3f, %6.3f%%' %('', self.lines_inserted, self.lines_deleted, all, self.percent * 100.0))
        #for c in self.changes:
        #    c.Show()

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
        self.name = name
        self.resource = res
        self.base = base           # 跟哪个版本比较文件
        self.files = []
        self.lines_inserted = 0
        self.lines_deleted = 0
        self.invalid = False
        self.Sigma = 0.0
        self.authorName = res['commit']['author']['name']
        self.GetChangeLine()

    def __lt__(self, other):
        if isinstance(other, Revision):
            return self.lines > other.lines

        return NotImplemented

    def SetInvalid(self):
        if self.name == 'be4de46f871911ea7e9cf36762c03c6d47d7abf7':
            pass
        if self.name not in WhiteList:
            self.invalid = True

    def NewFile(self, name, res):
        # 全局匹配
        for p in list(GlobalExcludeName):
            if re.findall(p, name):
                #print('Exclude file:', name)
                return None

        # 具体 Change 匹配
        if self.change._number in CustomChanges.keys():
            exclude = CustomChanges[self.change._number]
            for p in list(exclude):
                if re.findall(p, name):
                    #print('Exclude file:', name)
                    return None

        # 具体 Revision 匹配
        if self.name in CustomChanges.keys():
            exclude = CustomChanges[self.name]
            for p in list(exclude):
                if re.findall(p, name):
                    #print('Exclude file:', name)
                    return None

        for p in list(ExtensName):
            if re.findall(p, name):
                return File(name, res)

        if name in ExtensName:
            return File(name, res)

        #print(name, res)
        return File(name, res)

    def GetChangeLine(self):
        url = '/changes/%s/revisions/%s/files' % (self.change._number, self.name)

        if self.base:
            url += '?base=' + self.base
        file_js = gerrit.arrayGet(url)
        for (k, v) in file_js.items():
            if k != '/COMMIT_MSG' and 'binary' not in v:
                f = self.NewFile(k,v)
                if f:
                    self.lines_inserted += autoint(f.lines_inserted)
                    self.lines_deleted += autoint(f.lines_deleted)
                    self.files.append(f)

    def __str__(self):
        return '[%s] %8.3f %s  +%d\t-%d' % (self.invalid and 'X' or ' ', self.Sigma, self.name, self.lines_inserted, self.lines_deleted)

    def Show(self):
        print('\t%s' % self)

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
    def __init__(self, res):
        super().__init__()
        self.resource = res
        self.revisions = []
        self.lines_inserted = 0
        self.lines_deleted = 0

    def __lt__(self, other):
        if isinstance(other, Change):
            return self.lines > other.lines

        return NotImplemented

    def Update(self):
        rev_js = {}
        set_total = 0
        for (k, v) in self.resource['revisions'].items():
            v['name'] = k
            rev_js[v['_number']] = v
            set_total += 1

        base = None
        for i in range(set_total):
            r = rev_js[i + 1]
            k = r['name']
            rev = Revision(self, k, v, base)
            self.revisions.append(rev)
            self.lines_inserted += rev.lines_inserted
            self.lines_deleted += rev.lines_deleted
            base = k

    def LinesCalc(self, st):
        self.lines_inserted = 0
        self.lines_deleted = 0
        for rev in self.revisions:
            if not rev.invalid:
                self.lines_inserted += rev.lines_inserted
                self.lines_deleted += rev.lines_deleted

    def Show(self):
        print('%d [+%d,-%d] %s %s' % (self._number, self.lines_inserted, self.lines_deleted,
                              time.strftime('%Y-%m-%d %X', time.gmtime(self.created)), self.subject[:80]))
        for rev in self.revisions:
            rev.Show()
        print()

class Changes(Resource):
    def __init__(self, projectName, status='merged', created=0):
        super().__init__()
        self.status = status
        self.created = created
        self.projectName = projectName

    def Query(self, **params):
        self.params.update(**params)
        name = self.params.get('name', '.*')
        status = self.params.get('status', 'ACTIVE')

        url = '/changes/?q=status:%s+project:%s&o=ALL_REVISIONS&o=ALL_COMMITS&n=%d&S=%d' % (self.status, self.projectName, self.limit, self.offset)
        self.resource = gerrit.arrayGet(url)
        self.offset += len(self.resource)
        for res in self.resource:
            c = Change(res)
            if c._number in Blacklist:
                continue
            if c.created >= self.created or self.created == 0:
                c.Update()
                self.children.append(c)

class Projects(Resource):
    def __init__(self):
        super().__init__()
        self.invalidRevisionCount = 0
        self.created = 0
        self.ChangeList = []
        self.RevisionList = []
        self.authors = []
        self.status = [
            'merged',
            'abandoned',
            'open'
        ]

    def GetAuthor(self, name):
        for author in self.authors:
            if author.name == name:
                return author
        author = Author(name)
        self.authors.append(author)

        return author

    def Query(self, **params): #name, status):
        self.params.update(**params)
        name = self.params.get('name', '.*')
        status = self.params.get('status', 'ACTIVE')
        self.created = self.params.get('created', 0)

        if self.created:
            self.created = time.mktime(time.strptime(self.created,'%Y-%m-%d'))

        url = '/projects/?format=JSON&d'
        self.resource = gerrit.arrayGet(url)
        for (k, v) in self.resource.items():
            if re.findall(name, k) and v['state'] == status:
                for st in self.status:
                    changes = Changes(k, status=st, created=self.created)
                    for c in changes:
                        self.ChangeList.append(c)
                        self.RevisionList += c.revisions

        self.RevisionList = sorted(self.RevisionList, reverse=True)
        self.ChangeList = sorted(self.ChangeList, reverse=True)

    # 对变更提交进行正态分析， 3q 以上的不记入
    def NormalAnalysis(self):
        # 代码行超过2000行变更的提交直接不记入
        self.invalidRevisionCount = 0
        vlines = []
        print('超过 %s 行的变更，或者无代码变更:' % MAX_LINE)
        for r in self.RevisionList:
            if r.lines > 0 and max(r.lines_inserted, r.lines_deleted) < MAX_LINE:
                vlines.append(r.lines)
            else:
                r.Show()

        st = Statistics(vlines)
        print('总数: %d, 平均: %7.3f, 标准差: %8.3f' % (st.count, st.avg, st.std))

        for r in self.RevisionList:
            lines = r.lines
            r.Sigma = abs((lines - st.avg) / st.std)
            if r.Sigma > 1:
                self.invalidRevisionCount += 1
                r.SetInvalid()
                r.Show()

        for c in self.ChangeList:
            c.LinesCalc(st)

        #return
        print('--------------------------------------------------------------------------------------------------------------------')
        for c in self.ChangeList:
            for r in c.revisions:
                if r.invalid:
                    c.Show()
                    break

    def AuthorCalc(self):
        author_alias = {
            '黄俊斌': 'huangjb',
            '朱治国': 'zhuzhg',
            '刘非': 'liufei'
        }
        for r in self.RevisionList:
            name = r.authorName
            if name in author_alias:
                name = author_alias[name]
            author = self.GetAuthor(name)
            author.AddChange(r.change)
        total_inserted = 0
        total_deleted = 0
        for au in self.authors:
            total_inserted += au.lines_inserted
            total_deleted += au.lines_deleted

        for au in self.authors:
            au.percent = (au.lines_inserted + au.lines_deleted) / (total_inserted + total_deleted)

        self.authors = sorted(self.authors, key=lambda d:d.percent, reverse=True)

    def Sync(self):
        self.NormalAnalysis()
        self.AuthorCalc()

    def Show(self):
        total = len(self.RevisionList)
        print('总变更 %d 次, 有效变更 %d 次, 无效变更 %d 次，有效率：%4.1f%%' % (
                                               total,
                                               total - self.invalidRevisionCount,
                                               self.invalidRevisionCount,
                                               (total - self.invalidRevisionCount) / total * 100.0
                                               )
              )

        for au in self.authors:
            au.Show()

class Gerrit(object):
    def __init__(self, baseUrl):
        self.project = []
        self.baseUrl = baseUrl
        self.authors = {}

    def rawGet(self, url):
        if url.find('http://') < 0:
            url = self.baseUrl + url

        result = GetCacheUrl(url)
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
    projects = gerrit.GetProjects(name='goxceed', created='2014-06-01')
    projects.Sync()
    projects.Show()
