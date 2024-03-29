#!env python3
# -*- coding: utf-8 -*-

import datetime, time
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.utils import COMMASPACE, formatdate

import hashlib
import smtplib
import subprocess
import sys
import threading

import redminedb
import sync_code
import os

RedmineUrl = 'http://git.nationalchip.com/redmine'

class ProjectInfo:
    def __init__(self, db, name, start_date=None, end_date=None):
        self.db = db
        self.name = name
        self.project_name = ''
        self.log = ''
        project = self.db.project.get(name)
        if project:
            self.project_name = project.name
        self.start_date = start_date
        self.end_date = end_date

        today = datetime.date.today()
        if not self.end_date:
            self.end_date = today.strftime("%Y-%m-%d")

        if not self.start_date:
            weekday = today.weekday()
            start_day = today - datetime.timedelta(days=weekday + 5)
            self.start_date = start_day.strftime("%Y-%m-%d")

    def execute(self):
        created_on = '><%s|%s' % (self.start_date, self.end_date)
        issues_new    = self.db.issue.filter(project_id=self.name, created_on=created_on, status_id=1)
        issues_close  = self.db.issue.filter(project_id=self.name, created_on=created_on, status_id=2)
        issues_change = self.db.issue.filter(project_id=self.name, updated_on=created_on)

        def GetText(issues, subject):
            count = 0
            desc = '<ul><li><b>' + subject + '</b><ul>\n'
            if issues:
                for i in issues:
                    if self.IssueActive(i):
                        count += 1
                        li = '<li><a href="%s/issues/%d">#%-5d</a>: %s</li>\n' % (RedmineUrl, i.id, i.id, i.subject)
                        desc += li

            desc += '</ul></li></ul>\n'
            return count, desc

        count_new, description_new       = GetText(issues_new   , '新增问题列表')
        count_close, description_close   = GetText(issues_close , '关闭问题列表')
        count_change, description_change = GetText(issues_change, '更新问题列表')

        if count_new or count_close or count_change:
            subject = '新增问题 %d 条, 已解决问题 %d 条， 已更新问题 %d 条.' % (count_new, count_close, count_change)
            description = '<a href="%s/projects/%s/issues"><B>%s</B></a> (%s / %s): %s\n' % (RedmineUrl, self.name, self.project_name, self.start_date, self.end_date, subject)

            if count_new:
                description += description_new

            if count_close:
                description += description_close

            if count_change:
                description += description_change

            self.log = description

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
    def __init__(self):
        super().__init__()
        self.projects = []

    def UpdateWork(self, start=None, end=None):
        proNames = ['goxceed', 'goxtend']
        proNames = ['goxceed']

        work_manager = redminedb.WorkManager(2)
        for name in proNames:
            proj = ProjectInfo(self, name, start, end)
            self.projects.append(proj)
            work_manager.add_job(proj)

        work_manager.wait_allcomplete()
        text = ''
        for p in self.projects:
            text += p.log + "\n\n"

        return text[:-2]

def GerritUpdate(start, end):
    host = 'http://git.nationalchip.com/gerrit/a'
    #host = 'http://192.168.110.254/gerrit/a'
    sync_code.SIGMA = 4
    gerrit = sync_code.Gerrit(host)
    projects = gerrit.GetProjects(name='goxceed', start=start, end=end)
    projects.Sync()
    #projects.ShowChange()
    #projects.Show()

    lines_inserted = 0
    lines_deleted  = 0
    for au in projects.authors:
        lines_inserted += au.lines_inserted
        lines_deleted  += au.lines_deleted

    text = '<B>Gerrit 代码统计：</B>本周共提交 %s 次，增加代码 %d 行，删除代码 %d 行，新建代码 %d 行. ' % (
                                        len(projects.RevisionList), lines_inserted, lines_deleted, lines_inserted - lines_deleted)

    return text

def RedmineUpdate(start, end):
    db = RedmineDB()
    return db.UpdateWork(start, end)

def GetWeekDay(weekid):
    today = datetime.date.today()
    weekday = today.weekday()
    start = today - datetime.timedelta(days= weekday)
    end   = today + datetime.timedelta(days= 6 - weekday)

    now_weekid = int(time.strftime("%W"))
    start -= datetime.timedelta(days=(now_weekid - weekid) * 7)
    end   -= datetime.timedelta(days=(now_weekid - weekid) * 7)

    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

def SendEmail(msg, receiver):
    sender = 'zhuzhg@nationalchip.com'
    smtpserver = 'mail.nationalchip.com'
    username = 'zhuzhg'
    password = 'Zz#987987'

    smtp = smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    #smtp.set_debuglevel(1)

    smtp.login(username, password)
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()

def main():
    receiver = ['zhuzhg <zhuzhg@nationalchip.com>', 'yefeng <yefeng@nationalchip.com>']
    #receiver = ['zhuzhg <zhuzhg@nationalchip.com>']

    weekid = int(time.strftime("%W"))
    start_date, end_date = GetWeekDay(weekid)

    text1 = GerritUpdate(start_date, end_date)
    text2 = RedmineUpdate(start_date, end_date)
    print("\n---------------------------------------------------------------------")

    html_start = '<html><head><meta http-equiv="content-type" content="text/html; charset=GB2312"></head><body bgcolor="#FFFFFF" text="#000000">'
    html_end   = '</body></html>'
    subject    = 'SPD 第 %d 周工作日志 (%s 至 %s)' % (weekid, start_date, end_date)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['To']      = COMMASPACE.join(receiver)
    msg['From']    = 'zhuzhg <zhuzhg@nationalchip.com>'

    html = html_start + text1 + '<br>' + text2 + html_end
    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    SendEmail(msg, receiver)

if __name__ == '__main__':
    main()
