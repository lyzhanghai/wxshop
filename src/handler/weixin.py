#!/usr/bin/env python
#coding=utf8

import logging
import hashlib
from tornado.web import HTTPError
from handler import BaseHandler
from lib.route import route
from model import Oauth, User, UserVcode, Page, Apply, Shop, Ad
import xml.etree.ElementTree as ET
import time

@route(r'/weixin', name='weixin_index')
class indexHandler(BaseHandler):
    def message(self , body):
	data = ET.fromstring(body)
        tousername = data.find('ToUserName').text
        fromusername = data.find('FromUserName').text
        createtime = data.find('CreateTime').text
        msgtype = data.find('MsgType').text
        content = data.find('Content').text
        msgid = data.find('MsgId').text
	textTpl = """<xml>
            <ToUserName><![CDATA[%s]]></ToUserName>
            <FromUserName><![CDATA[%s]]></FromUserName>
            <CreateTime>%s</CreateTime>
            <MsgType><![CDATA[%s]]></MsgType>
            <Content><![CDATA[%s]]></Content>
            </xml>"""
        out = textTpl % (fromusername, tousername, str(int(time.time())), msgtype, content)
        self.write(out)

    def get(self):
        token=self.settings['weixin_token']
        signature = self.get_argument("signature")
        timeStamp = self.get_argument("timestamp")
        nonce = self.get_argument("nonce")

        tmp = [token, timeStamp, nonce]
        tmp.sort()
        raw = ''.join(tmp).encode()
        sha1Str = hashlib.sha1(raw).hexdigest()
        print sha1Str
        print signature
	if sha1Str == signature:
	    echostr = self.get_argument("echostr", "default")
            if echostr != "default":
                self.write(echostr)
	    else:
		pass
    def post(self):
        signature = self.get_argument("signature")
        timeStamp = self.get_argument("timestamp")
	body = self.request.body
	self.message(body)
