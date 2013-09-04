#! /usr/bin/python

import datetime
from pymongo import Connection

con = Connection('localhost',27017)
db = con.test
posts = db.post

post1 = {"title":"I Love Python",
          "slug":"i-love-python",
          "author":"SErHo",
          "content":"I Love Python....",
          "tags":["Love","Python"],
          "key": {
              "a":11,
              "b":22
          },
          "time":datetime.datetime.now()}

post2 = {"title":"Python and MongoDB",
         "slug":"python-mongodb",
         "author":"SErHo",
         "content":"Python and MongoDB....",
         "tags":["Python","MongoDB"],
         "key": {
             "a":22,
             "b":55
         },
         "time":datetime.datetime.now()}

post3 = {"title":"SErHo Blog",
         "slug":"serho-blog",
         "author":"Akio",
         "content":"SErHo Blog is OK....",
         "tags":["SErHo","Blog"],
         "key": {
             "a":33,
             "b":33
         },
         "time":datetime.datetime.now()}

#posts.insert(post1)
#posts.insert(post2)
#posts.insert(post3)


posts = posts.find({"key.a":22})

count = posts.count()
print count
for post in posts:
    print type(post)
    print post
