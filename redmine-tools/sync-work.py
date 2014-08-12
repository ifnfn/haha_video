#!env python3
# -*- coding: utf-8 -*-

import sys
from redmine import Redmine
import pymysql
import subprocess
import hashlib
import datetime, time
import threading
import db

class UserInfo:
    def __init__(self, db, uid, name):
        self.db = db
        self.uid = uid
        self.name = name

    def execute(self):
        issues_new = self.db.issue.filter(assigned_to_id=self.uid,
                                               status_id=1)
        issues_affirm = self.db.issue.filter(assigned_to_id=self.uid,
                                                  status_id=2)
        new_count = 0
        affirm_count = 0
        new_description = ''
        affirm_description = ''
        description = ''

        if issues_new:
            for issue in issues_new:
                if self.IssueActive(issue):
                    new_count += 1
                    new_description += "* #%d %s\n" % (issue.id, issue.subject)

        if issues_affirm:
            for issue in issues_affirm:
                if self.IssueActive(issue):
                    affirm_count += 1
                    affirm_description += "* #%d %s\n" %(issue.id, issue.subject)

        if new_count or affirm_count:
            subject = '新建问题（%d 条）， 已确认问题（%d 条）' % (new_count, affirm_count)

            if new_count:
                description += '新建问题列表：\n%s' % new_description

            if affirm_count:
                description += '\n已确认问题列表：\n%s' % affirm_description

            print(self.name, subject)
            #print(description)

            #self.NewOvertime(subject, description, self.uid)

    def NewOvertime(self, subject, description, user_id):
        issue = self.db.issue.new()
        issue.project_id = 'overtime'
        issue.tracker = 3
        issue.subject = subject
        issue.description = description
        issue.assigned_to_id = user_id

        issue.save()

    def IssueActive(self, issue):
        ret = True
        if issue.project.id == 213:
            return False
        start_date = datetime.date.today()
        today      = datetime.date.today()

        try:
            start_date = time.strptime(issue.start_date, "%Y-%m-%d")
        except:
            pass

        if today < start_date:
            ret = False
        try:
            for cf in issue.custom_fields:
                if cf.id == 21 and cf.value == '暂不处理':
                    ret = False
        except:
            pass

        return ret

class RedmineDB(db.RedmineBase):
    def UpdateWork(self):
        group = self.group.get(2561)

        work_manager =  db.WorkManager(10)
        for user in group.users:
            work_manager.add_job(UserInfo(self, user.id, user.name))
        work_manager.wait_allcomplete()

def weekend():
    x=time.localtime(time.time())
    return time.strftime("%w",x) in ['0', '6']

def main():
    if not weekend():
        db = RedmineDB()
        db.UpdateWork()

if __name__ == '__main__':
    main()
