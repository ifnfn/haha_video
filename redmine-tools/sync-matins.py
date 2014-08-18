#!env python3
# -*- coding: utf-8 -*-

import sys
from redmine import Redmine
import pymysql
import subprocess
import hashlib

class UpdateDB:
    def __init__(self):
        HOST = 'git.nationalchip.com'
        self.src_db = pymysql.connect(host=HOST, user='root', passwd='cnsczd', db='bugtracker')
        self.src_cursor = self.src_db.cursor()
        REDMINE_BASE = 'http://' + HOST + '/redmine'
        KEY = '2aa29b01a3fd827d180efa3ecb5fb8cf19e2e542';
        self.redmine = Redmine(REDMINE_BASE, key=KEY)

    def UpdateIssues(self):
        #self.src_cursor.execute('select id, severity,summary from mantis_bug_table limit 1')
        self.src_cursor.execute('select id, severity, summary, reproducibility from mantis_bug_table')
        results = self.src_cursor.fetchall()

        maps = {}
        fields = self.redmine.custom_field.all()
        for f in fields:
            if f.id == 17:
                maps[20] = f.possible_values[0]['value']
                maps[50] = f.possible_values[1]['value']
                maps[60] = f.possible_values[2]['value']
                maps[80] = f.possible_values[3]['value']

        for r in results:
            try:
                issues = self.redmine.issue.get(r[0])
                if issues == None:
                    continue
                if issues.custom_fields == None:
                    continue
            except:
                continue

            custom_fields = []
            for cf in issues.custom_fields:
                if cf['id'] == 17 and False:
                    severity = int(r[1])
                    if severity in [10, 20, 30]:
                        severity = 20
                    elif severity in [40, 50]:
                        severity = 50
                    elif severity in [60, 70]:
                        severity = 60
                    elif severity >= 80:
                        severity = 80
                    if severity in [20, 50, 60, 80]:
                        custom_fields.append( {'id': 17, 'value' : maps[severity]} )
                elif cf['id'] == 20:
                    #10:总是,30:有时,50:随机,70:没有试验,90:无法重现,100:不适用
                    x = ''
                    repro = int(r[3])
                    if repro == 10:
                        x = '必现'
                    elif repro in[20, 30, 40, 50]:
                        x = '随机'
                    else:
                        x = '难复现'
                    if x:
                        custom_fields.append( {'id': 20, 'value' :x} )

            if custom_fields:
                print(issues.id, custom_fields)
                self.redmine.issue.update(resource_id=issues.id, custom_fields=custom_fields)

    def Close(self):
        self.src_cursor.close()
        self.src_db.close()

def main():
    db = UpdateDB()
    db.UpdateIssues()
    db.Close()

if __name__ == '__main__':
    main()
