#!/usr/bin/env python
#coding=utf8

import datetime
import logging
from handler import UserBaseHandler
from lib.route import route
from lib.util import vmobile
from model import User, Order, OrderItem, Shop, ShopAttr, UserAddr, Consult, Mark, CreditLog

@route(r'/responsive', name='responsive') #用户后台首页
class UserHandler(UserBaseHandler):
    
    def get(self):
        user = self.get_current_user()
        try:
            user = User.get(id = user.id)
            self.session['user'] = user
            self.session.save()
        except:
            pass
        
        self.render('user/index.html')

@route(r'/user/delmark/(\d+)', name='user_delmark')
class DelMark(UserBaseHandler):
    
    def get(self, mid):
        user = self.get_current_user()
        Mark.delete().where(Mark.uid == user.id, Mark.id == mid).execute()
        self.flash("删除成功")
        self.redirect("/user/marks")