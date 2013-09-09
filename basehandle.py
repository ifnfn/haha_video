# coding=utf-8

'''
Created on 2013-9-9

@author: zhuzhg
'''

import tornado.web
import tornado.escape

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user = self.get_secure_cookie('user')
        if not user:
            return
        return tornado.escape.json_decode(user)

class JSONPHandler(BaseHandler):
    CALLBACK = 'jsonp' # define callback argument name
    def finish(self, chunk=None):
        """Finishes this response, ending the HTTP request."""
        assert not self._finished
        if chunk: self.write(chunk)
        # get client callback method
        #callback = tornado.escape(self.get_argument(self.CALLBACK, None))
        #print "callback", callback
        # format output with jsonp
        #self._write_buffer.insert(0, callback + '(')
        #self._write_buffer.append(')')
        # call base class finish method
        super(JSONPHandler, self).finish() # chunk must be None
