#!/usr/bin/env python
#coding=utf8

import datetime
import time
import urllib
import simplejson
import logging
import string
import json
from tornado.web import HTTPError
from handler import BaseHandler
from lib.route import route
from lib.util import sendmsg
from model import Category, CategoryAttr, Shop, ShopAttr, ShopPic, Order, OrderItem, Distribution, User, CreditLog
from wxpay import JsApi_pub, UnifiedOrder_pub,WxPayConf_pub,Notify_pub   
        
@route(r'/recomm/', name='recomm') #产品推荐
class RecommHandler(BaseHandler):
    
    def get(self):
        page = int(self.get_argument("page", 1))
        pagesize = self.settings['admin_pagesize']
        
        sq = Shop.select(Shop.name, Shop.ename, Shop.cover, Shop.price).where(Shop.status == 1)
        total = sq.count()
        shops = sq.paginate(page, pagesize)
        
        self.render("shop/recomm.html", shops = shops, total = total, page = page, pagesize = pagesize)
    
@route(r'/list/([^/]+)?', name='list') # 产品列表
class ListHandler(BaseHandler):
    
    def get(self, slug):
        ccategory= None
        if slug:
            try:
                ccategory = Category.get(slug = slug)
            except:
                self.redirect("/list/")
                return
        
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
        
        self.render("shop/list.html", ccategory = ccategory, categorys = categorys, shops = shops, total = total, page = page, pagesize = pagesize)

@route(r'/shop/([^/]+)?', name='shop') #商品详细页
class ShopHandler(BaseHandler):
    
    def get(self, ename):
        
        try:
            shop = Shop.get(ename = ename)
            shop.views = shop.views + 1
            shop.save()
            category = Category.get(id = shop.cid)
        except:
            raise HTTPError(404)
            return
        
        categoryattrs = CategoryAttr.select().where(CategoryAttr.cid == shop.cid)
        shopattrs = ShopAttr.select().where(ShopAttr.sid == shop.id)
        if shop.args:
            shop.args = simplejson.loads(shop.args)
        pics = ShopPic.select().where(ShopPic.sid == shop.id)
        
        recomshops = Shop.select().where((Shop.status == 1) & (Shop.id != shop.id)).paginate(1, 5)
        self.render("/responsive/shop.html", shop = shop, category = category, categoryattrs = categoryattrs, shopattrs = shopattrs, pics = pics, recomshops = recomshops)

@route(r'/order', name='order') #购物车
class OrderHandler(BaseHandler):
    
    def prepare(self):
        if not self.current_user:
            url = self.get_login_url()
            if "?" not in url:
                url += "?" + urllib.urlencode(dict(next=self.request.full_url()))
            self.redirect(url)
        
        super(BaseHandler, self).prepare()
    
    def get(self):
        orderitems = []
        user = self.current_user
        
        try:
            order = Order.get(uid = user.id, status = 0)
            
            for orderitem in OrderItem.select().where(OrderItem.oid == order.id).dicts():
                try:
                    orderitem['shop'] = Shop.get(id = orderitem['sid'])
                    if orderitem['said'] > 0:
                        orderitem['shopattr'] = ShopAttr.get(id = orderitem['said'])
                    orderitems.append(orderitem)
                except:
                    pass
        except:
            order = Order()
        
        ashops = Shop.select().where((Shop.cid == 2) & (Shop.status != 9))
        self.render("/responsive/order.html", orderitems = orderitems, order = order, ashops = ashops)

@route(r'/wxpay/settle', name='wxpay_settle') #结算
class SettleHandler(BaseHandler):
    def prepare(self):
        if not self.current_user:
            url = self.get_login_url()
            if "?" not in url:
                url += "?" + urllib.urlencode(dict(next=self.request.full_url()))
            self.redirect(url)
        
        super(BaseHandler, self).prepare()
    
    def get(self):
        orderitems = []
        user = self.current_user
        
        order = None
        
        distributions = self.get_distributions()
        price = 0.0
        credit = 0.0
        
        try:
            order = Order.get(uid = user.id, status = 0)
            
            try:
                mobile = '18014349809'
                sendmsg(self.settings, mobile, '新订单')
            except:
                pass
                
            for orderitem in OrderItem.select().where(OrderItem.oid == order.id).dicts():
                try:
                    orderitem['shop'] = Shop.get(id = orderitem['sid'])
                    _oiprice = orderitem['shop'].price
                    
                    if orderitem['said'] > 0:
                        orderitem['shopattr'] = ShopAttr.get(id = orderitem['said'])
                        if orderitem['shop'].cid == 1:
                            _oicredit = orderitem['shopattr'].price
                            credit = credit + _oicredit * orderitem['num']
                            _oiprice = orderitem['shopattr'].price
                        else:
                            _oiprice = orderitem['shopattr'].price
                    else:
                        _oiprice = float(_oiprice)
                        
                    orderitems.append(orderitem)
                    price = price + float(_oiprice) * orderitem['num']
                except:
                    pass
            order.price = price
            order.save()
            
        except:
            pass
        
        if orderitems:
            self.render("/responsive/settle.html", tmday = datetime.date.today() + datetime.timedelta(days=1), order  = order, orderitems = orderitems, distributions = distributions.values(), credit = credit)
    
    def post(self):
        order = None
        user = self.get_current_user()
        
        try:
            order = Order.get(uid = user.id, status = 0)
            print "user.id:"
            print user.id
            
            mobile = self.get_argument("mobile", user.mobile)
            uaid = self.get_argument("uaid", None)
            distrid = self.get_argument("distrid", None)
            day = self.get_argument("day", datetime.date.today() + datetime.timedelta(days=1))
            hour = int(self.get_argument("hour", 10))
            payment = self.get_argument("payment", 0)
            message = self.get_argument("message", "")
            isinvoice = self.get_argument("isinvoice", 0)
            invoicesub = self.get_argument("invoicesub", 0)
            invoicename = self.get_argument("invoicename", "")
            invoicecontent = self.get_argument("payment", 1)
            shippingprice = self.get_argument("shippingprice", 0.0)
            
            if uaid and distrid:
                try:
                    distrib = Distribution.get(id = distrid)
                    shippingprice = distrib.price
                except:
                    pass
                
                order.mobile = mobile
                order.uaid = uaid
                order.distrid = distrid
                order.distribbed = "%s %d:00:00" % (str(day), hour)
                order.payment = payment
                order.message = message
                
                order.isinvoice = isinvoice
                
                if isinvoice:
                    order.invoicesub = invoicesub
                    order.invoicename = invoicename
                    order.invoicecontent = invoicecontent
                
                order.shippingprice = shippingprice
                
                order.save()
                
                
                    
                body = ""
                for orderitem in OrderItem.select().where(OrderItem.oid == order.id).dicts():
                        
                    try:
                        shop = Shop.get(id = orderitem['sid'])
                            
                        sname = ""
                        if orderitem['said'] > 0:
                            shopattr = ShopAttr.get(id = orderitem['said'])
                            
                            if shop.cid == 1:
                                print 'a'
                                l = [shopattr.price,orderitem['num']]
                                print l
                                credits = shopattr.price * orderitem['num']
                                print credits
                                if credits > user.credit:
                                    print 'b'
                                    OrderItem.delete().where(OrderItem.id == orderitem['id']).execute()
                                else:
                                    print 'c'
                                    user = User.get(id = user.id)
                                    user.credit = user.credit - credits
                                    user.save()
                                    
                                    clog = CreditLog()
                                    clog.uid = user.id
                                    clog.mobile = user.mobile
                                    clog.ctype = 1
                                    clog.affect = int(credits)
                                    clog.log = u"购买" + shop.name
                                    clog.save()
                                    
                                    self.session['user'] = user
                                    self.session.save()
                                    
                            sname = shopattr.name
                            
                        body = body + shop.name + " " + sname + " " + str(orderitem['num']) + "个\n"
                    except Exception, ex:
                        logging.error(ex)
                
                tn = "U%d-S%d" % (user.id, order.id)
                
                if int(payment) == 1:
                    self.redirect("/wxpay/pay")
                else:
                    self.flash(u"请选择地址和收货方式")
                    self.redirect("/user/orders")
            else:
                self.flash(u"请选择地址和收货方式")
                self.redirect(self.request.headers["Referer"])
        except Exception, ex:
            logging.error(ex)
            self.flash(u"此订单不存在或者已过期")
            
@route(r'/wxpay/pay', name='wxpay_pay') #支付
class WxpayHandler(BaseHandler):
    def prepare(self):
        if not self.current_user:
            url = self.get_login_url()
            if "?" not in url:
                url += "?" + urllib.urlencode(dict(next=self.request.full_url()))
            self.redirect(url)
        
        super(BaseHandler, self).prepare()
        
    def get(self):
        orderitems = []
        user = self.current_user
        
        order = None
        
        distributions = self.get_distributions()
        price = 0.0
        credit = 0.0
        
        try:
            order = Order.get(uid = user.id, status = 0)
            print order.id
            '''
            try:
                mobile = '18014349809'
                sendmsg(self.settings, mobile, '新订单')
            except:
                pass
            '''    
            for orderitem in OrderItem.select().where(OrderItem.oid == order.id).dicts():
                try:
                    orderitem['shop'] = Shop.get(id = orderitem['sid'])
                    _oiprice = orderitem['shop'].price
                    
                    if orderitem['said'] > 0:
                        orderitem['shopattr'] = ShopAttr.get(id = orderitem['said'])
                        if orderitem['shop'].cid == 1:
                            _oicredit = orderitem['shopattr'].price
                            credit = credit + _oicredit * orderitem['num']
                            _oiprice = orderitem['shopattr'].price
                        else:
                            _oiprice = orderitem['shopattr'].price
                    else:
                        _oiprice = float(_oiprice)
                        
                    orderitems.append(orderitem)
                    price = price + float(_oiprice) * orderitem['num']
                except:
                    pass
            print price
            price_pay = str(int(price*100))
            print 'price_pay:' + price_pay
            openid = user.openid
            print 'wx_pay:'+ openid
            jsApi = JsApi_pub()
            unifiedOrder = UnifiedOrder_pub()
            unifiedOrder.setParameter("openid",openid) #商品描述
            unifiedOrder.setParameter("body","菜市优品购物") #商品描述
            timeStamp = time.time()
            print timeStamp
            out_trade_no = "{0}{1}".format(WxPayConf_pub.APPID, int(timeStamp*100))
            unifiedOrder.setParameter("out_trade_no", out_trade_no) #商户订单号
            print 'out_trade_no:' + out_trade_no
            Order.update(wxid = out_trade_no).where(Order.id == order.id).execute()
            unifiedOrder.setParameter("total_fee", price_pay) #总金额
            print WxPayConf_pub.NOTIFY_URL
            unifiedOrder.setParameter("notify_url", WxPayConf_pub.NOTIFY_URL) #通知地址 
            unifiedOrder.setParameter("trade_type", "JSAPI") #交易类型
            
            prepay_id = unifiedOrder.getPrepayId()
            jsApi.setPrepayId(prepay_id)
            jsApiParameters = jsApi.getParameters()
            print jsApiParameters
            appid = json.loads(jsApiParameters).get("appId")
            timestamp = json.loads(jsApiParameters).get("timeStamp")
            noncestr = json.loads(jsApiParameters).get("nonceStr")
            package = json.loads(jsApiParameters).get("package")
            signtype = json.loads(jsApiParameters).get("signType")
            paysign = json.loads(jsApiParameters).get("paySign")
            print appid + timestamp + noncestr + package + signtype +paysign
            if orderitems:
                self.render("/responsive/wxpay.html", tmday = datetime.date.today() + datetime.timedelta(days=1), order  = order, orderitems = orderitems, distributions = distributions.values(), credit = credit, appid = appid, timestamp = timestamp, noncestr = noncestr, package = package, signtype = signtype, paysign = paysign)
        except:
            pass
        

@route(r'/wxpay/callback', name='wxpay_callback') #回调通知
class CallbackHandler(BaseHandler):
        
    def post(self):
        notify = Notify_pub()
        xml = self.request.body
        notify.saveData(xml)
        if not notify.checkSign:
            notify.setParameter("return_code", "FAIL")
            notify.setReturnParameter("return_msg", "签名失败")
            print "签名失败"
        else:
            result = notify.getData()
            print "result:"
            print result
            
            if result["return_code"] == "FAIL":
                notify.setReturnParameter("return_code", "FAIL")
                notify.setReturnParameter("return_msg", "通信错误")
                print "通信错误"
            elif result["result_code"] == "FAIL":
                notify.setReturnParameter("return_code", "FAIL")
                notify.setReturnParameter("return_msg", result["err_code_des"])
            else:
                notify.setReturnParameter("return_code", "SUCCESS")
                out_trade_no = result["out_trade_no"]
                time_end = result["time_end"]
                print "支付成功:" + out_trade_no
                print "交易时间:" + time_end
                print "更改订单状态"
                Order.update(status = 1).where(Order.status == 0 and Order.wxid == out_trade_no).execute() #支付成功订单状态改为1
        return self.write(notify.returnXml()) 

        


    
