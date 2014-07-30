#!env python3
# -*- coding: utf-8 -*-

import time
import re
import threading
import redminedb

def dameraulevenshtein(seq1, seq2):
    oneago = None
    thisrow = list(range(1, len(seq2) + 1)) + [0]
    for x in range(len(seq1)):
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
        for y in range(len(seq2)):
            delcost = oneago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = oneago[y - 1] + (seq1[x] != seq2[y])
            thisrow[y] = min(delcost, addcost, subcost)
            if (x > 0 and y > 0 and seq1[x] == seq2[y - 1]
                and seq1[x-1] == seq2[y] and seq1[x] != seq2[y]):
                thisrow[y] = min(thisrow[y], twoago[y - 2] + 1)

    return thisrow[len(seq2) - 1]

def NoteComp(str1, str2):
    len1 = len(str1)
    len2 = len(str2)

    m1 = min(len1, len2)
    m2 = max(len1, len2)

    if m1 < m2 < m1 * 2.5:
        ld = dameraulevenshtein(str1, str2)
        return ld / m2
    else:
        return 1

def invalidNote(note):
    keyword = ('我', '你', '他', '她', '它', '也许', '大概', '好象', '啊', '哇', '呀')

    for key in keyword:
        if key in note:
            return True

def NoteLen(note):
    note_len = 0
    for c in note:
        if ord(c) < 512:
            note_len += 1
        else:
            note_len += 3

    fix_len = 0
    if note_len > 4096:
        fix_len += (note_len - 4096) * 0.5
        note_len = 4096
    if note_len > 2048:
        fix_len += (note_len - 2048) * 0.7
        note_len = 2048
    if note_len > 1024:
        fix_len += (note_len -  1024) * 0.8
        note_len = 1024
    if note_len > 512:
        fix_len += (note_len -  512) * 0.9
        note_len = 512
    fix_len += note_len
    return int(round(fix_len))
            
class UserInfo:
    def __init__(self, db, uid, uname):
        self.db = db
        self.id = uid
        self.username = uname
        self.dateData = {}

        self.doc_size = 0

        self.issue_count = 0
        self.issue_doc_size = 0

        self.forum_count = 0
        self.forum_doc_size = 0

        self.isssue_avg_doc_size = 0
        self.notes = []
        self.mutex = threading.Lock()
        self.updated_on = time.strftime("=%Y-%m-%d", time.localtime())

    def AddNote(self, note):
        note = re.sub("<pre>[\s\S]*?</pre>", '', note)
        note = re.sub("> [\s\S]*?\n", "", note).strip()

        if not note:
            return 0

        note_len = NoteLen(note)
        #if note_len > 512:
        #    print(note)

        if note_len < 500 and False:
            self.mutex.acquire()
            for n in self.notes:
                x = NoteComp(note, n)
                if x < 0.3:
                    #print("-------------------------------------------------------------------------------------")
                    #print(x, mx, ld)
                    print('_____________________________________________________________________________________')
                    print(note)
                    print('_____________________________________________________________________________________')
                    print(n)
                    print("=====================================================================================")

                    self.mutex.release()
                    return 0

            self.notes.append(note)
            self.mutex.release()

            if invalidNote(note):
                note_len = note_len / 2

        self.doc_size += note_len
        return note_len

    def __lt__(self, other):
        if isinstance(other, UserInfo):
            return self.issue_count > other.issue_count

        return NotImplemented

    def IssueAvg(self):
        if self.issue_count:
            return self.issue_doc_size / self.issue_count
        else:
            return 0

    def ForumAvg(self):
        if self.forum_count:
            return self.forum_doc_size / self.forum_count
        else:
            return 0

class UserDocument:
    def __init__(self):
        pass

    def execute(self):
        try:
            self.Calc()
        except:
            pass

class IssueJournalsDocument(UserDocument):
    def __init__(self, db, issue):
        self.issue = issue
        self.db = db

    def Calc(self):
        for i in self.issue.journals:
            if not i.notes:
                continue
            uinfo = self.db.GetUserInfo(i.user.id)
            if uinfo:
                uinfo.issue_count += 1
                note_len = uinfo.AddNote(i.notes)
                uinfo.issue_doc_size += note_len
                #if note_len > 0:
                #    print("%-6s \t%-6d %5d(%5d)" % (i.user.name, self.issue.id, note_len, len(i.notes)))
    
class IssuesDocument(UserDocument):
    def __init__(self, db, date):
        super().__init__()
        self.db = db
        if date:
            self.updated_on = date
        else:
            self.updated_on = time.strftime("=%Y-%m-%d", time.localtime())

    def Calc(self):
        issues = self.db.issue.filter(project_id='goxceed',
                                      status_id='*',
                                      updated_on=self.updated_on,
                                      include="attachments,journals,relations")

        for issue in issues:
            try:
                #if issue.id != 3549:
                #    continue
                uinfo = self.db.GetUserInfo(issue.author.id)
                if uinfo:
                    note_len = uinfo.AddNote(issue.description)
                    uinfo.issue_doc_size += note_len
                self.db.AddJob(IssueJournalsDocument(self.db, issue))
            except:
                pass

class ForumsDocument(UserDocument):
    def __init__(self, db, fid):
        self.db = db
        self.fid = fid

    def Calc(self):
        url = '{0}/projects/goxceed/boards/{1}.json'.format(self.db.url, self.fid)
        x = self.db.request('get', url)
        for message in x['boards']['messages']:
            uinfo = self.db.GetUserInfo(message['author_id'])
            if uinfo:
                try:
                    note_len = uinfo.AddNote(message['subject'])
                    uinfo.forum_doc_size += note_len
                except:
                    pass

                try:
                    note_len = uinfo.AddNote(message['content'])
                    uinfo.forum_doc_size += note_len
                except:
                    pass

class RedmineDB(redminedb.RedmineBase):
    def __init__(self):
        super().__init__()
        self.users = {}
        self.GetSpd()
        self.work_manager = redminedb.WorkManager(10)

    def AddJob(self, job):
        self.work_manager.add_job(job)

    def GetUserInfo(self, uid):
        if uid in self.users:
            return self.users[uid]

    def GetSpd(self):
        self.groups = self.GetGroup(2561)
        for user in self.groups.users:
            #if user.name == 'Z朱治国':
            self.users[user.id] = UserInfo(self, user.id, user.name)

    def CleanData(self):
        for _, u in self.users.items():
            u.doc_size = 0

    def Issue(self, date=None):
        self.AddJob(IssuesDocument(self, date))

    def Forum(self):
        self.AddJob(ForumsDocument(self, 1))
        self.AddJob(ForumsDocument(self, 2))
        self.AddJob(ForumsDocument(self, 3))

    def UpdateDocument(self, date=None):
        self.Issue(date)
        self.Forum()

        self.work_manager.wait_allcomplete()
        self.Print(date)

    def Print(self, message):
        t_max = 0
        t_avg = 0
        for _, u in self.users.items():
            t_avg += u.doc_size
            if u.doc_size > t_max:
                t_max = u.doc_size

        t_avg = t_avg / len(self.users)

        print(t_avg)
        print("+-------------------------------------------------------------------+")
        print("| %s                                                      |" % message)
        print("+-------------------------------------------------------------------+")
        print("|%4s %-6s %6s %6s %4s %4s %4s %4s |" % ('UID', '姓名', '原字数', '折数', '提升', '文档行', '问题数', '平均字数'))
        print("+-------------------------------------------------------------------+")
        for (_, u) in sorted(self.users.items(), key=lambda d:d[1], reverse=True):
            if u.doc_size:
                fix_size = (u.doc_size ** 4 * t_avg) ** (1 / 5)
                print(" %4d %-6s %7d %8d %6.2f %7d %7d %8d" % (u.id, u.username, u.doc_size, fix_size, fix_size / u.doc_size, fix_size / 10,
                                                               u.issue_count, u.IssueAvg()))
        print()

def main():
    try:
        db = RedmineDB()
        db.UpdateDocument('>=2014-06-01')
        db.CleanData()
    except Exception as e:
        print(e)

    #db.UpdateDocument('=2014-06-04')
    #db.CleanData()
    #db.UpdateDocument('=2014-06-03')
    #db.CleanData()
    #db.UpdateDocument('=2014-06-02')
    #db.CleanData()

if __name__ == '__main__':
    main()
