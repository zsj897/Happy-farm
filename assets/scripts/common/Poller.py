# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
import tornado.httpclient
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


def onTornadoIOLoop(timerID):
	tornado.ioloop.IOLoop.current().start()
	

class LoginPoller:
	def __init__(self):
		DEBUG_MSG("======================= LoginPoller .__init__ =======================")
		self._loginName = ""
		KBEngine.addTimer(0.3, 0.3, onTornadoIOLoop)
		#登录列表，解决登录时的意外状况，导致用户下一次登录异常
		self._loginList = []
		KBEngine.addTimer(5, 5, self.CheckTimeOut)

	def AddLoginList(self,loginName, password, datas, CallBack):
		endTime = int(time.time()) + 8  #设置8秒超时时间
		info = {'loginName':loginName,'password':password,'datas':datas,'CallBack':CallBack,'endTime':endTime}
		self._loginList.append(info)
		DEBUG_MSG("AddLoginList: %s" % (str(info)))
	
	def DelLoginList(self,loginName):
		for index,info in enumerate(self._loginList):
			if info['loginName'] == loginName:
				DEBUG_MSG("DelLoginList: %s" % (info['loginName']))
				del self._loginList[index]

	def CheckTimeOut(self, timerID):
		for index,info in enumerate(self._loginList):
			if int(time.time()) >= info['endTime']:
				self.ZLLogin(info['loginName'], info['password'], info['datas'], info['CallBack'])
				DEBUG_MSG("超时CheckTimeOut: %s" % (info['loginName']))
				del self._loginList[index]

	#众联登录
	def ZLLogin(self, loginName, password, datas, CallBack):
		url = 'http://user.zgzlwy.top:9090/v1/user/loginnew?'
		param = "account="+ loginName + "&password=" + password
		http_client =  tornado.httpclient.AsyncHTTPClient()
		http_client.fetch(url, method='POST', body=param, callback=Functor.Functor(self.onZLLoginResult,loginName,password,datas,CallBack) )
		self.AddLoginList(loginName,password,datas,CallBack)

	def onZLLoginResult(self, loginName, password, datas, CallBack, response):
		DEBUG_MSG("onZLLoginResult ...............................")
		if response.error:
			ERROR_MSG("ZLLogin Error: %s" % (response.error))
			self.ZLLogin(loginName, password, datas, CallBack)
		else:
			ZLLoginResult = response.body.decode('utf8')
			Result = json.loads(ZLLoginResult)
			DEBUG_MSG('ZLLoginResult:%s' % ZLLoginResult)
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
			self.DelLoginList(loginName)
			CallBack(loginName, realAccountName, response.body, err)


class IndexHandler(tornado.web.RequestHandler):
	def get(self):		
		DBID = self.get_argument('DBID')
		errMsg = self.get_argument('errMsg')
		moneyType = self.get_argument('moneyType')
		moneyValue = self.get_argument('moneyValue')
		DEBUG_MSG('IndexHandler:%s,%s,%s,%s' % (DBID, errMsg, moneyType, moneyValue) )
		KBEngine.globalData["Halls"].ReChange(int(DBID), errMsg, int(moneyType), int(moneyValue) )

class Poller:
	def __init__(self):
		DEBUG_MSG("======================= Poller .__init__ =======================")
		
	def StartServer(self):
		app = tornado.web.Application(handlers=[(r"/recharge", IndexHandler )])   
		http_server = tornado.httpserver.HTTPServer(app) 
		http_server.bind(8888)
		http_server.start()
		
	def tickTornadoIOLoop(self):
		tornado.ioloop.IOLoop.current().start()
		
	#获得好友列表
	def	GetFriendList(self, uid, callBack):
		url = 'http://user.zgzlwy.top:9090/v1/user/friendlist?uid=' + uid
		http_client = tornado.httpclient.AsyncHTTPClient()
		http_client.fetch(url, method='GET', body=None, callback=Functor.Functor(self.onGetFriendList, callBack) )
		DEBUG_MSG("GetFriendList:"+url)

	def onGetFriendList(self, callBack, response):
		DEBUG_MSG("onGetFriendList ...............................")
		if response.error:
			ERROR_MSG("onGetFriendList Error: %s" % (response.error))
			callBack(None)
		else:
			strResult = response.body.decode('utf8')
			Result = json.loads(strResult)
			callBack(Result)

	#获得E币, 众联的E币*100
	def	GetEglod(self, uid, callBack):
		Value = (uid+'ZLNC123').encode(encoding='utf-8')
		url = 'http://trade.zgzlwy.top:7070/v3/game/getecoin?uid=%s&sign=%s' % (uid,md5Value(Value) )
		http_client = tornado.httpclient.AsyncHTTPClient()
		http_client.fetch(url, method='GET', body=None, callback=Functor.Functor(self.onGetEglod,uid,callBack) )
		DEBUG_MSG("GetEglod:"+url)

	def onGetEglod(self,uid,callBack, response):
		if response.error:
			ERROR_MSG("onGetEglod Error: %s" % (response.error))
			self.GetEglod(uid, callBack)
		else:
			strResult = response.body.decode('utf8')
			Result = json.loads(strResult)
			DEBUG_MSG('onGetEglod Result:%s' % strResult)
			callBack(Result)
	
	#修改E币 本地E币 除 100
	def ChangeEglod(self, uid, amount, ctype,item,comment):
		url = 'http://trade.zgzlwy.top:7070/v3/game/changeecoin?'
		Value = (uid+'ZLNC123').encode(encoding='utf-8')
		param = 'uid=%s&amount=%f&ctype=%d&item=%s&comment=%s&sign=%s' % (uid,amount,ctype,item,comment,md5Value(Value))
		http_client = tornado.httpclient.AsyncHTTPClient()
		http_client.fetch(url, method='POST', body=param, callback=Functor.Functor(self.onChangeEglod,uid, amount, ctype,item,comment) )
		DEBUG_MSG("ChangeEglod:"+url+param)

	def onChangeEglod(self, uid, amount, ctype,item,comment,response):
		if response.error:
			ERROR_MSG("onChangeEglod Error: %s" % (response.error))
			self.ChangeEglod(uid, amount, ctype,item,comment)
		else:
			strResult = response.body.decode('utf8')
			Result = json.loads(strResult)
			DEBUG_MSG('onChangeEglod Result:%s' % strResult)
			

	#获得开元通宝
	def	GetKglod(self, uid, callBack):
		Value = (uid+'ZLNC123').encode(encoding='utf-8')
		url = 'http://trade.zgzlwy.top:7070/v3/game/getkcoin?uid=%s&sign=%s' % (uid,md5Value(Value))
		http_client = tornado.httpclient.AsyncHTTPClient()
		http_client.fetch(url, method='GET', body=None, callback=Functor.Functor(self.onGetKglod,uid,callBack) )
		DEBUG_MSG("GetEglod:"+url)

	def onGetKglod(self, uid,callBack,response):
		if response.error:
			ERROR_MSG("onGetKglod Error: %s" % (response.error))
			self.GetKglod(uid, callBack)
		else:
			strResult = response.body.decode('utf8')
			Result = json.loads(strResult)
			DEBUG_MSG('onGetKglod Result:%s' % strResult)
			callBack(Result)

	#修改开元通宝
	def ChangeKglod(self, uid, amount, ctype,item,comment):
		url = 'http://trade.zgzlwy.top:7070/v3/game/changekcoin?'
		Value = (uid+'ZLNC123').encode(encoding='utf-8')
		param = 'uid=%s&amount=%f&ctype=%d&item=%s&comment=%s&sign=%s' % (uid,amount,ctype,item,comment,md5Value(Value))
		http_client = tornado.httpclient.AsyncHTTPClient()
		http_client.fetch(url, method='POST', body=param, callback=Functor.Functor(self.onChangeKglod, uid, amount, ctype, item, comment))
		DEBUG_MSG("ChangeKglod:"+url+param)

	def onChangeKglod(self, uid, amount, ctype, item, comment, response):
		if response.error:
			ERROR_MSG("onChangeKglod Error: %s" % (response.error))
			self.ChangeKglod(uid, amount, ctype, item, comment)
		else:
			strResult = response.body.decode('utf8')
			Result = json.loads(strResult)
			DEBUG_MSG('onChangeKglod Result:%s' % strResult)

	#获得充值订单
	def	GetRechargeOrder(self, device_type, diamond, RMB,uid,callBack):
		url = 'http://120.79.192.49:80/pay/wxpayrecharge?'
		param = 'device_type=%d&gain_amount=%d&pay_amount_fee=%d&remark=%s&uid=%s' % (device_type, diamond, RMB,'', uid)
		http_client = tornado.httpclient.AsyncHTTPClient()
		http_client.fetch(url, method='POST', body=param, callback=Functor.Functor(self.onRechargeOrderd, device_type, diamond, RMB,uid,callBack))
		DEBUG_MSG("GetRechargeOrder:"+url+param)

	def onRechargeOrderd(self, device_type, diamond, RMB, uid, callBack, response):
		if response.error:
			ERROR_MSG("onRechargeOrderd Error: %s" % (response.error))
			self.GetRechargeOrder(device_type, diamond, RMB, uid, callBack)
		else:
			strResult = response.body.decode('utf8')
			DEBUG_MSG('onRechargeOrderd Result:%s' % strResult)
			callBack(strResult)

	#检查账号密码
	def	CheckAccount(self, AccountName, Password, callBack):
		url = 'http://user.zgzlwy.top:9090/v1/user/validateaccount?account=%s&passwd=%s' % (AccountName, Password) 
		http_client = tornado.httpclient.AsyncHTTPClient()
		http_client.fetch(url, method='GET', body=None, callback=Functor.Functor(self.onCheckAccount,AccountName, Password, callBack))
		DEBUG_MSG("CheckAccount:"+url)

	def onCheckAccount(self, AccountName, Password, callBack, response):
		if response.error:
			ERROR_MSG("onCheckAccount Error: %s" % (response.error))
			self.CheckAccount(AccountName, Password, callBack)
		else:
			strResult = response.body.decode('utf8')
			Result = json.loads(strResult)
			DEBUG_MSG('onCheckAccount Result:%s' % strResult)
			callBack(Result)	

	#建验公众号是否绑定
	def CheckBindWeChat(self, uid, callBack):
		url = 'http://120.79.192.49:80/weixinmp/querysub?uid=%s' % uid
		http_client = tornado.httpclient.AsyncHTTPClient()
		http_client.fetch(url, method='GET', body=None, callback=Functor.Functor(self.onCheckBindWeChatd,uid, callBack) )
		DEBUG_MSG("CheckBindWeChat:"+url)

	def onCheckBindWeChatd(self,uid, callBack, response):
		if response.error:
			ERROR_MSG("onCheckBindWeChatd Error: %s" % (response.error))
			self.CheckBindWeChat(uid, callBack)
		else:
			strResult = response.body.decode('utf8')
			Result = json.loads(strResult)
			DEBUG_MSG('onCheckBindWeChatd Result:%s' % strResult)
			callBack(Result)

g_Poller = Poller()