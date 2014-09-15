#!env python3
# -*- coding: utf-8 -*-

import sys
from redmine import Redmine
import subprocess
import hashlib
import datetime, time
import threading
import redminedb

class ProjectInfo:
    def __init__(self, db, name, start_date=None, end_date=None):
        self.db = db
        self.name = name
        self.start_date = start_date
        self.end_date = end_date

        if not self.end_date:
            today = datetime.date.today()
    return time.strftime("%w",x) in ['0', '6']

    def execute(self):
        issues_new = self.db.issue.filter(project_id=self.name, created_on='><%s|%s' % (self.start_date, self.end_date),
                                               status_id=1)
        issues_affirm = self.db.issue.filter(project_id=self.name, created_on='><%s|%s' % (self.start_date, self.end_date),
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

class RedmineDB(redminedb.RedmineBase):
    def UpdateWork(self):
        projects =  ['goxceed', 'goxtend']
 
        work_manager = redminedb.WorkManager(2)
        for name in projects:
            work_manager.add_job(ProjectInfo(self, name))
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
