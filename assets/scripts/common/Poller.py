# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
import tornado.httpserver  
import tornado.web
from urllib import parse
import json
import time
import hashlib
import Functor

#md5加密
def md5Value(value):
    m=hashlib.md5()
    m.update(value)
    sign=m.hexdigest()
    return sign

'''
	游戏登录
'''
class LoginPoller:
	def __init__(self):
		DEBUG_MSG("======================= LoginPoller .__init__ =======================")
		
	#众联登录
	def ZLLogin(self, loginName, password, datas, callBack):
		url = 'http://user.zgzlwy.top:9090/v1/user/loginnew?'
		param = "account="+ loginName + "&password=" + password
		KBEngine.urlopen(url, Functor.Functor(self.onZLLoginResult, loginName, callBack, datas), param.encode())

	def onZLLoginResult(self, loginName, callBack, datas, httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			DEBUG_MSG('onZLLoginResult:%s' % data)
			loginName = Result['content']['account']
			err = KBEngine.SERVER_SUCCESS
			realAccountName = Result['content']['uid']
			if Result['status'] == 1:
				err = KBEngine.SERVER_SUCCESS
			elif Result['status'] == 2:
				err = KBEngine.SERVER_ERR_NAME_PASSWORD
			elif Result['status'] == 3:
				err = KBEngine.SERVER_ERR_USER2 #此账号尚未注册
			elif Result['status'] == 6:
				err = KBEngine.SERVER_ERR_USER3 #手机号码格式错误
			else:
				err = KBEngine.SERVER_ERR_USER4 #登录失败
			callBack(loginName, realAccountName, datas, err)
		else:
			ERROR_MSG("onZLLoginResult Error: %i" % (httpcode) )
			callBack(loginName, loginName, datas, KBEngine.SERVER_ERR_OP_FAILED)

'''
	游戏web服务
'''
class IndexHandler(tornado.web.RequestHandler):
	def get(self):		
		DBID = self.get_argument('DBID')
		errMsg = self.get_argument('errMsg')
		moneyType = self.get_argument('moneyType')
		moneyValue = self.get_argument('moneyValue')
		DEBUG_MSG('IndexHandler:%s,%s,%s,%s' % (DBID, errMsg, moneyType, moneyValue) )
		KBEngine.globalData["Halls"].ReChange(int(DBID), errMsg, int(moneyType), int(moneyValue) )

class MailHandler(tornado.web.RequestHandler):
	def get(self):
		DBID = self.get_argument('DBID')
		awardTypelist = self.get_argument('awardTypelist')
		awardValuelist = self.get_argument('awardValuelist')
		MessageTEXT = self.get_argument('MessageTEXT')
		timeinterval = self.get_argument('timeinterval')
		DEBUG_MSG('MailHandler:%s,%s,%s,%s,%s' % (DBID, awardTypelist, awardValuelist, MessageTEXT, timeinterval) )
		KBEngine.globalData["Halls"].SendMailMessage(int(DBID),1001,awardTypelist.split(','),awardValuelist.split(','),MessageTEXT,int(timeinterval))

class WebPoller:
	def __init__(self):
		DEBUG_MSG("======================= WebPoller .__init__ =======================")
		
	def StartServer(self):
		app = tornado.web.Application(handlers=[(r"/recharge", IndexHandler ), (r'/Mail', MailHandler)])   
		http_server = tornado.httpserver.HTTPServer(app) 
		http_server.bind(8888)
		http_server.start()
		
	def tickTornadoIOLoop(self):
		tornado.ioloop.IOLoop.current().start()

'''
	玩家http请求
'''
class Poller:
	def __init__(self):
		DEBUG_MSG("======================= Poller .__init__ =======================")		
	#获得好友列表
	def	GetFriendList(self, uid, callBack):
		url = 'http://user.zgzlwy.top:9090/v1/user/friendlist?uid=' + uid
		KBEngine.urlopen(url, Functor.Functor(self.onGetFriendList, callBack))
		DEBUG_MSG("GetFriendList:"+url)

	def onGetFriendList(self,callBack, httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			callBack(Result)
			DEBUG_MSG('onGetFriendList:%s' % data)
		else:
			ERROR_MSG("onGetEglod Error: %i" % (httpcode) )
			callBack(None)

	#获得E币, 众联的E币*100
	def	GetEglod(self, uid, callBack):
		Value = (uid+'ZLNC123').encode(encoding='utf-8')
		url = 'http://trade.zgzlwy.top:7070/v3/game/getecoin?uid=%s&sign=%s' % (uid,md5Value(Value) )
		KBEngine.urlopen(url, Functor.Functor(self.onGetEglod, callBack))
		DEBUG_MSG("GetEglod:"+url)

	def onGetEglod(self,callBack,httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			callBack(Result)
			DEBUG_MSG('onGetEglod:%s' % data)
		else:
			ERROR_MSG("onGetEglod Error: %i" % (httpcode) )
	
	#修改E币 本地E币 除 100
	def ChangeEglod(self, uid, amount, ctype,item,comment):
		url = 'http://trade.zgzlwy.top:7070/v3/game/changeecoin?'
		Value = (uid+'ZLNC123').encode(encoding='utf-8')
		param = 'uid=%s&amount=%f&ctype=%d&item=%s&comment=%s&sign=%s' % (uid,amount,ctype,item,comment,md5Value(Value))
		KBEngine.urlopen(url, self.onChangeEglod, param.encode())
		DEBUG_MSG("ChangeEglod:"+url+param)

	def onChangeEglod(self,httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			DEBUG_MSG('onChangeEglod:%s' % data)
		else:
			ERROR_MSG("onChangeEglod Error: %i" % (httpcode) )
			
	#获得开元通宝
	def	GetKglod(self, uid, callBack):
		Value = (uid+'ZLNC123').encode(encoding='utf-8')
		url = 'http://trade.zgzlwy.top:7070/v3/game/getkcoin?uid=%s&sign=%s' % (uid,md5Value(Value))
		KBEngine.urlopen(url, Functor.Functor(self.onGetKglod, callBack))
		DEBUG_MSG("GetKglod:"+url)

	def onGetKglod(self,callBack, httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			callBack(Result)
			DEBUG_MSG('onGetKglod:%s' % data)
		else:
			ERROR_MSG("onGetKglod Error: %i" % (httpcode) )

	#修改开元通宝
	def ChangeKglod(self, uid, amount, ctype,item,comment):
		url = 'http://trade.zgzlwy.top:7070/v3/game/changekcoin?'
		Value = (uid+'ZLNC123').encode(encoding='utf-8')
		param = 'uid=%s&amount=%f&ctype=%d&item=%s&comment=%s&sign=%s' % (uid,amount,ctype,item,comment,md5Value(Value))
		KBEngine.urlopen(url, self.onChangeKglod, param.encode())
		DEBUG_MSG("ChangeKglod:"+url+param)

	def onChangeKglod(self, httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			DEBUG_MSG('onChangeKglod:%s' % data)
		else:
			ERROR_MSG("onChangeKglod Error: %i" % (httpcode) )
	
	#获得凤凰链
	def GetHFL(self, uid, callBack):
		Value = (uid+'ZLNC123').encode(encoding='utf-8')
		url = 'http://121.201.80.40:7070/v3/game/getphc?uid=%s&sign=%s' % (uid,md5Value(Value))
		KBEngine.urlopen(url,  Functor.Functor(self.onGetHFL, callBack))
		DEBUG_MSG("GetHFL:"+url)

	def onGetHFL(self,callBack, httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			callBack(Result)
			DEBUG_MSG('onGetHFL:%s' % data)
		else:
			ERROR_MSG("onGetHFL Error: %i" % (httpcode) )
			
	#修改凤凰链
	def ChangeHFL(self, uid, amount, ctype, item, comment):
		url = 'http://121.201.80.40:7070/v3/game/changephc?'
		Value = (uid+'ZLNC123').encode(encoding='utf-8')
		param = 'uid=%s&amount=%f&ctype=%d&item=%s&comment=%s&sign=%s' % (uid,amount,ctype,item,comment,md5Value(Value))
		KBEngine.urlopen(url, self.onChangeHFL, param.encode())
		DEBUG_MSG("ChangeHFL:"+url+param)

	def onChangeHFL(self, httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			DEBUG_MSG('onChangeHFL:%s' % data)
		else:
			ERROR_MSG("onChangeHFL Error: %i" % (httpcode) )

	#获得充值订单
	def	GetRechargeOrder(self, device_type, diamond, RMB,uid,callBack):
		url = 'http://120.79.192.49:80/pay/wxpayrecharge?'
		param = 'device_type=%d&gain_amount=%d&pay_amount_fee=%d&remark=%s&uid=%s' % (device_type, diamond, RMB,'', uid)
		KBEngine.urlopen(url, Functor.Functor(self.onRechargeOrderd, callBack), param.encode())
		DEBUG_MSG("GetRechargeOrder:"+url+param)

	def onRechargeOrderd(self,callBack, httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			callBack(Result)
			DEBUG_MSG('onRechargeOrderd:%s' % data)
		else:
			ERROR_MSG("onRechargeOrderd Error: %i" % (httpcode) )

	#检查账号密码
	def	CheckAccount(self, AccountName, Password, callBack):
		url = 'http://user.zgzlwy.top:9090/v1/user/validateaccount?account=%s&passwd=%s' % (AccountName, Password) 
		KBEngine.urlopen(url, Functor.Functor(self.onCheckAccount, callBack))
		DEBUG_MSG("CheckAccount:"+url)

	def onCheckAccount(self,callBack, httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			callBack(Result)
			DEBUG_MSG('onCheckAccount:%s' % data)
		else:
			ERROR_MSG("onCheckAccount Error: %i" % (httpcode) )

	#建验公众号是否绑定
	def CheckBindWeChat(self, uid, callBack):
		url = 'http://120.79.192.49:80/weixinmp/querysub?uid=%s' % uid
		KBEngine.urlopen(url, Functor.Functor(self.onCheckBindWeChatd, callBack))
		DEBUG_MSG("CheckBindWeChat:"+url)

	def onCheckBindWeChatd(self,callBack,httpcode, data, headers, success, url):
		if success:
			Result = json.loads(data)
			callBack(Result)
			DEBUG_MSG('onCheckBindWeChatd:%s' % data)
		else:
			ERROR_MSG("onCheckBindWeChatd Error: %i" % (httpcode) )
	
	#金蛋充值
	# def JiDangRecharge(self, shouji, pas, yzm, num, callBack):
	# 	order = 'dfadf'
	# 	QG_USERKEY = "f9948861afd6e7aa280dbcab7f9747e0"
	# 	QG_APPKEY  = "e794642c02c8e968ddcbd1d2e116376f"
	# 	weini = 'kdfa'
	# 	url = 'http://public.api.ebimall.cn/?' + \
	# 	'''key={"app":"123","type":"pay_public","request":{"order":"%s","shouji":"%i","pay_type":"8","bi_type":"1","pas":"%s","yzm":"%i","num":"%i","st":"众联农场金蛋充值","weini":"%s"}}''' \
	# 	% (shouji, pas, yzm, -num)
	# 	http_client = tornado.httpclient.AsyncHTTPClient()
	# 	http_client.fetch(url, method='GET', body=None, callback=Functor.Functor(self.onJiDangRecharge, uid, callBack) )
	# 	DEBUG_MSG("JiDangRecharge:"+url)

	# def onJiDangRecharge(self, response):
	# 	if response.error:
	# 		ERROR_MSG("onJiDangRecharge Error: %s" % (response.error))
	# 	else:
	# 		strResult = response.body.decode('utf8')
	# 		Result = json.loads(strResult)
	# 		DEBUG_MSG('onJiDangRecharge Result:%s' % strResult)
	# 		callBack(Result)


