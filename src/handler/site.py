#!/usr/bin/env python
#coding=utf8

import logging
from tornado.web import HTTPError
from handler import BaseHandler
from lib.route import route
from model import Oauth, User, UserVcode, Page, Apply, Shop, Ad
import weixin
@route(r'/', name='index') #首页
class IndexHandler(BaseHandler):
    
    def get(self):
        ads = Ad.select().limit(6)
        newest = []
        for shop in Shop.select(Shop.name, Shop.ename, Shop.cover, Shop.price).where((Shop.cid != 2) & (Shop.status != 9)).order_by(Shop.views.desc()).limit(6):
            shop.price = shop.price.split("~")[0]
            newest.append(shop)
        
        recomm = []
        for shop in Shop.select(Shop.name, Shop.ename, Shop.cover, Shop.price).where(Shop.status == 1).limit(6):
            shop.price = shop.price.split("~")[0]
            recomm.append(shop)
 
	ccategory= None
        keyword = self.get_argument("keyword", None)
        
        page = int(self.get_argument("page", 1))
        order = self.get_argument("order", None)
        
        pagesize = self.settings['admin_pagesize']
        
        categorys = self.get_categorys()
        
        sq = Shop.select(Shop.name, Shop.ename, Shop.cover, Shop.price)
        total = sq.count()
        
        if ccategory:
            sq = sq.where((Shop.cid == ccategory.id) & (Shop.status != 9))
        elif keyword:
            keyword = "%" + keyword + "%"
            sq = sq.where((Shop.name % keyword) & (Shop.status != 9))
        else:
            sq = sq.where((Shop.cid != 2) & (Shop.status != 9))
        
        if order:
            sq = sq.order_by(Shop.orders.desc())
        else:
            sq = sq.order_by(Shop.views.desc())
        
        shops = []
        for shop in sq.paginate(page, pagesize):
            shop.price = shop.price.split("~")[0]
            shops.append(shop)
        
        self.render("responsive/index.html", ads = ads, newest = newest, recomm = recomm,ccategory = ccategory, categorys = categorys, shops = shops, total = total, page = page, pagesize = pagesize)

@route(r'/apply', name='apply') #集团购买/会员特惠
class ApplyHandler(BaseHandler):
    
    def get(self):
        self.render("site/apply.html")
    
    def post(self):
        coname = self.get_argument("coname", None)
        city = self.get_argument("city", None)
        region = self.get_argument("region", None)
        address = self.get_argument("address", None)
        try:
            pnumber = int(self.get_argument("pnumber", 1))
        except:
            pnumber = 1
        name = self.get_argument("name", None)
        tel = self.get_argument("tel", None)
        mobile = self.get_argument("mobile", "")
        
        applyed = Apply()
        applyed.coname = coname
        applyed.city= city
        applyed.region = region
        applyed.address = address
        applyed.pnumber = pnumber
        applyed.name = name
        applyed.tel = tel
        applyed.mobile = mobile
        
        try:
            applyed.validate()
            applyed.save()
            self.flash("申请成功，请等待我们的消息。", "ok")
            self.redirect("/apply")
            return
        
        except Exception, ex:
            self.flash(str(ex))
        
        self.render("site/apply.html")
@route(r'/share', name='share') #分享
class ShareHandler(BaseHandler):

    def get(self):
	sharer = self.get_argument("sharer", None)
        user=self.get_current_user()

        oauth = None
        if 'oauth' in self.session:
            oauth = self.session['oauth']
	if sharer:
	    if user:
                self.render("responsive/share.html", oauth = oauth, next = self.next_url)
	    else:
		print sharer
		share_url="/signup?sharer="+sharer
                self.redirect(share_url)
	else:
	    if user:
	        url="/share?sharer="+user.mobile
                self.redirect(url)
	    else:
                self.redirect("/signup")	
@route(r'/signin', name='signin') #登录
class SignInHandler(BaseHandler):
    
    def get(self):
        if self.get_current_user():
            self.redirect("/")
            return
        
        oauth = None
        if 'oauth' in self.session:
            oauth = self.session['oauth']
        
        self.render("responsive/signin.html", oauth = oauth, next = self.next_url)
    
    def post(self):
        if self.get_current_user():
            self.redirect("/")
            return
        
        mobile = self.get_argument("mobile", None)
        password = self.get_argument("password", None)
        
        if mobile and password:
            try:
                user = User.get(User.mobile == mobile)
                
                if user.check_password(password):
                    if user.group > 0:
                        user.updatesignin()
                        
                        self.session['user'] = user
                        
                        if 'oauth' in self.session:
                            oauth = self.session['oauth']
                            
                            o = Oauth()
                            o.uid = user.id
                            o.openid = oauth['id']
                            o.src = oauth['src']
                            o.save()
                            
                            del self.session['oauth']
                        
                        self.session.save()
                       	if mobile != "root":
			    self.redirect(self.next_url)
			else:
			    self.redirect("/admin")    
                        return
                    else:
                        self.flash("此账户被禁止登录，请联系管理员。")
                else:
                    self.flash("密码错误")
            except Exception, ex:
                logging.error(ex)
                self.flash("此用户不存在")
        else:
            self.flash("请输入用户名或者密码")
        
        self.render("responsive/signin.html", next = self.next_url)

@route(r'/signup', name='signup') #注册
class SignUpHandler(BaseHandler):
    
    def get(self):
        if self.get_current_user():
            self.redirect("/")
            return
        
        oauth = None
        if 'oauth' in self.session:
            oauth = self.session['oauth']
        code = self.get_argument("code", None)
        sharer = self.get_argument("sharer", None)
	appid = self.settings['weixin_appid']
        url_w = self.settings['weixin_url']
        print ''+appid
        print ''+url_w
        openid='openid'
        if code:
	       print "code"+sharer
	       openid = weixin.get_openid(self , code)
        else:
           print 'code null'+sharer
        print ''+openid
        
        self.render("/responsive/signup.html", oauth = oauth ,openid = openid,appid =appid,url_w = url_w,sharer = sharer)
    
    def post(self):
        if self.get_current_user():
            self.redirect("/")
            return
        
        mobile = self.get_argument("mobile", None)
        password = self.get_argument("password", None)
        apassword = self.get_argument("apassword", None)
        vcode = self.get_argument("vcode", None)
        sharer = self.get_argument("sharer", None)
        openid = self.get_argument("openid", None) 
        
        user = User()
        user.mobile = mobile
        user.openid = openid
        print openid
        user.password = User.create_password(password)
        
        try:
            user.validate()
            
            if password and apassword:
                if len(password) < 6:
                    self.flash("请确认输入6位以上新密码")
                elif password != apassword:
                    self.flash("请确认新密码和重复密码一致")
                else:
                    if UserVcode.select().where((UserVcode.mobile == mobile) & (UserVcode.vcode == vcode)).count() > 0:
                        UserVcode.delete().where((UserVcode.mobile == mobile) & (UserVcode.vcode == vcode)).execute()
                        user.save()
                        
                        if 'oauth' in self.session:
                            oauth = self.session['oauth']
                            o = Oauth()
                            o.uid = user.id
                            o.openid = oauth['id']
                            o.src = oauth['src']
                            o.save()
                            
                            del self.session['oauth']
                            self.session.save()
                        print sharer
			User.update(credit = User.credit + 1).where(User.mobile == mobile).execute()
                        #if sharer != None
                        User.update(credit = User.credit + 1).where(User.mobile == sharer).execute()
			self.flash("注册成功，请先登录。", "ok")
                        self.redirect("/signin")
                        return
                    else:
                        self.flash("请输入正确的验证码")
            else:
                self.flash("请输入密码和确认密码")
        except Exception, ex:
            self.flash(str(ex))
        self.render("/responsive/signup.html")

@route(r'/signout', name='signout') #退出
class SignOutHandler(BaseHandler):
    
    def get(self):
        if "user" in self.session:
            del self.session["user"]
            self.session.save()
        self.redirect(self.next_url)

@route(r'/resetpassword', name='resetpassword') #忘记密码
class ResetPasswordHandler(BaseHandler):
    
    def get(self):
        if self.get_current_user():
            self.redirect("/")
            return
        
        self.render("site/resetpassword.html")
        
    def post(self):
        if self.get_current_user():
            self.redirect("/")
            return
        
        mobile = self.get_argument("mobile", None)
        password = self.get_argument("password", None)
        apassword = self.get_argument("apassword", None)
        vcode = self.get_argument("vcode", None)
        
        try:
            user = User().get(mobile = mobile)
        except:
            self.flash("此用户不存在")
            self.redirect("/resetpassword")
            return
        
        try:
            if password and apassword:
                if len(password) < 6:
                    self.flash("请确认输入6位以上新密码")
                elif password != apassword:
                    self.flash("请确认新密码和重复密码一致")
                else:
                    if UserVcode.select().where((UserVcode.mobile == mobile) & (UserVcode.vcode == vcode)).count() > 0:
                        UserVcode.delete().where((UserVcode.mobile == mobile) & (UserVcode.vcode == vcode)).execute()
                        user.password = User.create_password(password)
                        user.save()
                        self.flash("重置密码成功，请先登录。", "ok")
                        self.redirect("/signin")
                        return
                    else:
                        self.flash("请输入正确的验证码")
            else:
                self.flash("请输入密码和确认密码")
        except Exception, ex:
            self.flash(str(ex))
        
        self.render("site/resetpassword.html")

@route(r'/p/([^/]+)', name='staticpage') #栏目页
class StaticPageHandler(BaseHandler):
    
    def get(self, slug):
        try:
            page = Page.get(slug = slug)
        except:
            raise HTTPError(404)
            return
        
        self.render("static/%s" % page.template, page = page)
