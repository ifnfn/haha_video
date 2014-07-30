#!env python3
# -*- coding: utf-8 -*-

import sys
from redmine import Redmine
import pymysql
import subprocess
import hashlib

class UpdateDB:
    def __init__(self):
        self.src_db = pymysql.connect(host='172.18.0.10', user='root',passwd='Pa$$W0rd', db='redmine')
        self.src_cursor = self.src_db.cursor()
        REDMINE_BASE = 'http://192.168.110.254/redmine'
        self.redmine = Redmine(REDMINE_BASE, key='2aa29b01a3fd827d180efa3ecb5fb8cf19e2e542')

    def UpdateUserInfo(self):
        dest_db = pymysql.connect(host='192.168.110.254', user='root',passwd='cnsczd', db='redmine2')
        dest_cursor = dest_db.cursor()
        update_cursor = dest_db.cursor()

        self.src_cursor.execute('select hashed_password, firstname, lastname, mail, login, status, created_on from users WHERE type="User"')
        update_cursor.execute('SET NAMES utf8')

        users = []
        results = self.src_cursor.fetchall()
        for r in results:
            hash_password = r[0]
            firstname     = r[1]
            lastname      = r[2]
            mail          = r[3]
            login         = r[4]
            status        = r[5]
            created_on    = r[6]
            sql = 'SELECT salt FROM users WHERE login="%s"' % login
            dest_cursor.execute(sql)
            salt_results = dest_cursor.fetchall()
            if salt_results:
                for nr in salt_results:
                    p = nr[0] + hash_password
                    hashed_password = hashlib.sha1(p.encode()).hexdigest()

                    sql = "UPDATE users SET  hashed_password='%s', firstname='%s', lastname='%s', mail='%s', language='zh', status=%s, created_on='%s' WHERE login='%s'" % \
                            (hashed_password, firstname, lastname, mail, status, created_on, login)
                    # 只更新密码
                    #sql = "UPDATE users SET  hashed_password='%s', language='zh', created_on='%s' WHERE login='%s'" % \
                    #        (hashed_password, created_on, login)

                    update_cursor.execute(sql)
                    break
            else:
                print("No Found:", login)
                u = self.NewUser(login, firstname, lastname, mail)
                users.append(u)

        dest_db.commit()
        update_cursor.close()
        dest_cursor.close()
        dest_db.close()

        print('=====================================')
        for u in users:
            try:
                u.save()
            except:
                print('error:', u.login, u.mail)
                pass

    def NewUser(self, login, firstname, lastname, mail):
        user = self.redmine.user.new()
        user.login     = login
        user.firstname = firstname
        user.lastname  = lastname
        user.mail      = mail
        user.password  = login

        return user

    def UserInfo(self):
        users = self.redmine.user.all()
        for u in users:
            u.saved = False
            if u.firstname not in ['SOC', 'DAD', 'DAD ', 'SPD', 'BU1', 'BU2',
                               'BU3', 'BU4', 'PMD', 'CVD-PHD', 'CAR', 'CID', 'CVD', 'PHD', 'QAD', 'SALES', 'PAD', 'IMD', 'Sales']:
                u.lastname = u.lastname + u.firstname
            u.firstname = u.login[0].upper()
            u.saved = True

            a = u.firstname
            u.firstname = u.lastname
            u.lastname = a
            #if u.lastname == '-':
            #    u.lastname  = u.firstname[0:1]
            #    u.firstname = u.firstname[1:].strip()
            #    u.saved = True

            #if len(u.firstname) == 1:
            #    u.firstname = u.lastname + u.firstname
            #    u.lastname = '-'
            #    u.saved = True

            if u.saved:
                u.save()

    def Close(self):
        self.src_cursor.close()
        self.src_db.close()

def main():
    db = UpdateDB()
    db.UpdateUserInfo()
    db.UserInfo()
    db.Close()

if __name__ == '__main__':
    main()
