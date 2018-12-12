# -*- coding: utf-8 -*-
import KBEngine
import d_card_dis
import d_MaskWord
import random
import math
import types
from KBEDebug import *
from array import *
import copy
import Functor
from GameRecord import *
from Poller import *
from ComFunc import *

class Account(KBEngine.Proxy):

	def __init__(self):
		KBEngine.Proxy.__init__(self)

		"""
		在在线玩家列表注册自己
		"""
		#KBEngine.globalData["Halls"].reqAddPlayer(self)

		self.cardSum = 134
		
		# 存放将要使用的卡组
		self.willUseKz = -1
		self.getClientTimeID = 0
		# 存放已经匹配过的次数 在匹配过程中会用
		self.HaveMarchSum = 0

		self.battleResult = -1
		self.clientControl = True

		#第一次登陆
		if self.Data["FirstLogin"] == 0:
			self.Data["FirstLogin"] = 1
			self.FirstLogin()
	
		if self.Data["rank"]<1000:
			self.Data["rank"] = 10001000
		
		self.onPlayingBattlefiled = None
		self.onPlayingDestroy = False

		self.TimerDestroyID = None
		#两秒后更新E币，
		self.addTimer(2,2,1)

	def FirstLogin(self):
		# 初始化金钱
		self.Data["money"] = 100000
		# 随机生成人物头像，展示不支持自定义
		self.Data["Icon"] = random.randint(1,5)
		self.Data["gender"] = 0

	def onTimer(self, id, userArg):
		"""
		KBEngine method.
		使用addTimer后， 当时间到达则该接口被调用
		@param id		: addTimer 的返回值ID
		@param userArg	: addTimer 最后一个参数所给入的数据
		"""
		#DEBUG_MSG(id, userArg)
		if userArg == 1:
			#self.GiveCardList()
			self.delTimer(id)
			#更新E币和开元通宝
			self.UpdateData()
		elif userArg == 2:
			self.onGetClient()
		elif userArg == 3:
			INFO_MSG("destroy :%i,%s" % (self.id,self.Data['name']))
			self.destroy()
			self.TimerDestroyID = None

	def onEntitiesEnabled(self):
		"""
		KBEngine method.
		该entity被正式激活为可使用， 此时entity已经建立了client对应实体， 可以在此创建它的
		cell部分。
		"""
		INFO_MSG("account[%i] entities enable. mailbox:%s" % (self.id, self.client))
		self.onPlayingDestroy = False

		if len(self.Avatar_List) == 0:
			self.randomInitKZ()

	def onLogOnAttempt(self, ip, port, password):
		"""
		KBEngine method.
		客户端登陆失败时会回调到这里
		"""
		INFO_MSG(ip, port, password)
		return KBEngine.LOG_ON_ACCEPT
		
	def onClientEnabled(self):
		"""
		KBEngine method.
		该entity被正式激活为可使用， 此时entity已经建立了client对应实体， 可以在此创建它的
		cell部分。
		"""
		INFO_MSG("account[%i]::onClientEnabled:entities enable." % (self.id))
		if self.TimerDestroyID is not None:
			self.delTimer(self.TimerDestroyID)
			self.TimerDestroyID = None

		self.InitClientData()

	def InitClientData(self):
		if hasattr(self,'client'):
			self.reqData(0)

	def onClientDeath(self):
		"""
		KBEngine method.
		客户端对应实体已经销毁
		"""
		DEBUG_MSG("Account[%i].onClientDeath:" % self.id)
		# 1:第一次登陆 2：不是第一次登陆
		self.Data["FirstLogin"] = 2
		#8秒后销毁实体,以适应断线重连
		self.TimerDestroyID = self.addTimer(8,0,3)
		#self.destroy()
		if self.onPlayingBattlefiled == None:
			pass
		else:
			self.onPlayingDestroy = True

	def reqInf(self):
		INFO_MSG("reqInf")
		self.client.onInf("测试版本，不代表最终品质！~")
	
	#是否游客 true 是游客
	def IsYK(self):
		Name = self.AccountName()
		if Name.find('yk') != -1:
			return True
		return False
	#创建createEntityFromDBID 时无法获得__ACCOUNT_NAME__ ，所以只能保存
	def AccountName(self):
		if hasattr(self, '__ACCOUNT_NAME__'):
			self.UID = self.__ACCOUNT_NAME__
		return self.UID

	def UpdateData(self):
		if not self.IsYK():
			g_Poller.GetEglod(self.AccountName(),self.onUpdateEglod)
			g_Poller.GetKglod(self.AccountName(),self.onUpdateKglod)
	
	def onUpdateEglod(self, Result):
		if	Result['code'] == 1:
			if Result['info']['uid'] == self.AccountName():
				eglod = float(Result['info']['total'])
				self.Data['eglod'] = int(round(eglod * 100))
				INFO_MSG("onUpdateEglod:%f,%i" % (eglod*100,self.Data['eglod']) )
				if self.client is not None:
					self.client.onEglod(self.Data['eglod']) 
		else:
			INFO_MSG("onUpdateEglod error:%s" % ( Result['info']))

	def onUpdateKglod(self, Result):
		if	Result['code'] == 1:
			if Result['info']['uid'] == self.AccountName():
				kglod = float(Result['info']['total'])
				self.Data['kglod'] = int(round(kglod * 100))
				INFO_MSG("onUpdateKglod:%f,%i" % (kglod*100,self.Data['kglod']) )
				if self.client is not None:
					self.client.onKglod(self.Data['kglod'])
		else:
			INFO_MSG("onUpdateKglod error:%s" % ( Result['info']))

	#查找，找到屏蔽字返回True，否则返回false
	def is_contain(self,message):
		for item in d_MaskWord.MaskWord[1]['word']:
			if message.find(item) !=-1:
				return True, item  
		return False,'' 

	def reqChangeName(self, name):
		INFO_MSG("reqChangeName:%s" % (name) )
		#名字是否有屏蔽字	
		IsMaskWord, word = self.is_contain(name)
		if IsMaskWord:
			self.client.onChangeName('屏蔽字', word )
			return
		else:
			sql = '''select * from tbl_Account where sm_Data_name ="%s" and id <> %d ;''' % (name,self.databaseID)
			KBEngine.executeRawDatabaseCommand(sql, Functor.Functor(self.sqlChangeName, name))

	def sqlChangeName(self, name, result, rows, insertid, error):
		if result is not None and len(result) <= 0:
			self.Data['name']=name
			self.client.onChangeName('成功', name)
		else:
			self.client.onChangeName('昵称已被使用', name )

	def reqChangeData(self, gender, Icon, IsFristChange):
		INFO_MSG("reqChangeData:%i,%i" % (gender, Icon) )
		#性别		
		self.Data['gender']=gender
		#头像
		self.Data['Icon']=Icon
		self.client.onChangeData('成功', self.Data, IsFristChange)
		
	#修改玩家基础数据，如金币，金蛋，开元通宝
	def ChangeBaseData(self, priceType, value, Des):
		if priceType == 1: #用游戏币购买
			money = self.Data['money']
			if value < 0 and money < abs(value):
				return -1
			self.Data['money'] += value
			if self.client is not None:
				self.client.onMoney(self.Data['money'])
		elif priceType == 2:#用砖石购买
			diamond = self.Data['diamond']
			if value < 0 and diamond < abs(value):
				return -2
			self.Data['diamond'] += value
			if self.client is not None:
				self.client.onDiamond(self.Data['diamond'])
		elif priceType == 3:#开元通宝
			kglod = self.Data['kglod']
			if value < 0 and kglod < abs(value):
				return -3
			self.Data['kglod'] += value
			if self.client is not None:
				self.client.onKglod(self.Data['kglod'])
			g_Poller.ChangeKglod(self.AccountName(),abs(value)/100.00, 1 if value>=0 else 2,'众联农场',Des)
		elif priceType == 4:#E币
			eglod = self.Data['eglod']
			if value < 0 and eglod < abs(value):
				return -4
			self.Data['eglod'] += value
			if self.client is not None:
				self.client.onEglod(self.Data['eglod'])
			g_Poller.ChangeEglod(self.AccountName(),abs(value)/100.00, 1 if value>=0 else 2,'众联农场',Des)
		#游戏金钱日志
		GameMoneyRecord(self.AccountName(),self.databaseID,priceType,value,Des)
		return 0

	def reqMoney(self):
		INFO_MSG("reqMoney")
		self.client.onMoney(self.Money)

	def reqData(self, DBID = 0):
		if DBID == 0:
			self.client.onData(self.Data,self.databaseID)
			DEBUG_MSG("reqData:%s" % str(self.Data))
		else:
			KBEngine.createEntityFromDBID("Account",DBID,Functor.Functor(self.CallBackData))

	def CallBackData(self,baseRef,databaseID,wasActive):
		if baseRef is None:
			DEBUG_MSG("CallBackData baseRef error:%i" % databaseID)
			g_Generator.Set(databaseID,self.CallBackData)
		else:
			self.client.onData(baseRef.Data,databaseID)
			if not wasActive:
				baseRef.destroy()

	#绑定游客账号
	def reqBindAccount(self,AccountName,Password):
		g_Poller.CheckAccount(AccountName, Password, self.OnBindAccount)

	def OnBindAccount(self, Result):
		if Result['status'] == 0:
			self.client.onBindAccount('参数缺失')
		elif Result['status'] == 1:
			uid = Result['content']['uid']
			sql = "UPDATE kbe_accountinfos SET accountName='%s' where accountName='%s';" % (uid,self.AccountName() )
			KBEngine.executeRawDatabaseCommand(sql, Functor.Functor(self.sqlBindAccount, uid))
			DEBUG_MSG("OnBindAccount sql:%s" % sql)
		elif Result['status'] == 2:
			self.client.onBindAccount('密码错误')
		elif Result['status'] == 3:
			self.client.onBindAccount('该账户不存在')
		elif Result['status'] == 4:
			self.client.onBindAccount('手机号码格式错误')

	def sqlBindAccount(self,uid, result, rows, insertid, error):
		if error is None:
			self.client.onBindAccount('成功')
			self.__ACCOUNT_NAME__ = uid
		else:
			self.client.onBindAccount('绑定失败，账号已有游戏数据')
			

	def reqBuyWithGold(self,sum1):
		DEBUG_MSG("Account[%i].BuyWithGold:" % self.id)
		sum=int(sum1)
		if self.Data['money'] > sum*100-1:
			self.Data['money']=self.Data['money']-sum*100
			self.Data['kabao']=self.Data['kabao']+sum
			self.client.onbuycard(0)
		else:
			self.client.onbuycard(1)

	def reqBuyWithRMB(self,sum1):
		DEBUG_MSG("Account[%i].BuyWithGold:" % self.id)
		sum=int(sum1)
		if self.Data['diamond'] > sum*2-1:
			self.Data['diamond']=self.Data['diamond']-sum*2
			self.Data['kabao']=self.Data['kabao']+sumsum
			self.client.onbuycard(0)
		else:
			self.client.onbuycard(1)


	def reqOpeningPack(self):
		DEBUG_MSG("Account[%i].reqOpeningPack:" % self.id)
		self.Data['kabao']=self.Data['kabao']-1

		data =  {'card1':0, 'card2':0, 'card3':0, 'card4':0, 'card5':0}
		namedata =  {'card1':"", 'card2':"", 'card3':"", 'card4':"", 'card5':""}

		for i in range(5): 
			data['card%i'%(i+1)]=random.randint(10000001,10000000+self.cardSum)
			namedata['card%i'%(i+1)]=(d_card_dis.datas[data['card%i'%(i+1)]]["name"])
			self.Card_Data['values'].append(data['card%i'%(i+1)])

		self.client.onOpeningPackResult(data,namedata)

	def reqAccountCardData(self):
		self.client.onAccountCardData(self.Card_Data)

	def reqPlayerSum(self):
		KBEngine.globalData["Halls"].reqPlayerSum(self)

	def OnPlayerSum(self,PlayerSum,MarcherSum):
		self.client.onGetPlayerSum(PlayerSum)
		self.client.OnMarcherSum(MarcherSum)

	def reqStartMarch(self,whichKz):
		DEBUG_MSG("Account[%i].reqStartMarch: Kzid[%i]" % (self.id,whichKz))
		self.OnClientMsg_March("正在匹配对手")
		KBEngine.globalData["Halls"].reqAddMarcher(self)
		self.willUseKz = whichKz

	def reqStopMarch(self):
		DEBUG_MSG("Account[%i].reqStopMarch" % self.id)
		KBEngine.globalData["Halls"].reqDelMarcher(self)
		self.willUseKz = -1

	def OnEnterBattelField(self,battlefiled,_playerID):
		DEBUG_MSG("Account[%i].OnEnterBattelField" % self.id)
		self.BattleField = battlefiled
		self.playerID = _playerID
		self.BattleField.AccountReady(self.playerID)

	def OnClientMsg_March(self,msg):
		if self.client == None:
			return
		self.client.onMarchMsg(msg)

	def BattleFailed(self):#战斗匹配失败
		DEBUG_MSG("Account[%i].BattleInitFailed" % self.id)
		
		if not self.hasClient:
			if self.Avatar0 == None:
				self.destroy()
			else:
				self.Avatar0.BattleFailed()

			return

		self.reqStartMarch(self.willUseKz)

	def onGetClient(self):
		DEBUG_MSG("Account[%s]::onGetClient" % (self.id))
		if self.getClientTimeID == 0:
			self.getClientFailSum = 0
			if self.client!=None and self.clientControl:
				self.getClientPrc()
			else:
				self.getClientTimeID = self.addTimer(1,1,2)
		else:
			if self.client!=None and self.clientControl:
				self.getClientPrc()
				self.delTimer(self.getClientTimeID)
				self.getClientTimeID = 0
				self.getClientFailSum = 0
			else:
				self.getClientFailSum += 1
				if self.getClientFailSum > 5:
					self.delTimer(self.getClientTimeID)
					self.destroy()

	def waitClient(self):
		pass

	def reqGetClient(self):
		DEBUG_MSG("Account[%s]::reqGetClient" % (self.id))
		self.clientControl = True

	def getClientPrc(self):
		DEBUG_MSG("Account[%s]::getClientPrc battleResult:[%s]" % (self.id,self.battleResult))
		if self.battleResult == -1:
			pass
		else:
			self.battleResultClientDisplay()

	def BattleEndResult(self,result):#1成功 0失败
		DEBUG_MSG("Account[%s]::BattleEndResult  result[%s]" % (self.id, result))

		if self.isDestroyed:
			DEBUG_MSG("Account[%s]::BattleEndResult processResultFail  self is destroyed" % (self.id))
			return

		# if result == 1:
		# 	self.Data["rank"] +=  8 + self.WinStreakSum*self.WinStreakSum
		# 	self.WinStreakSum += 1

		# else:
		# 	self.Data["rank"] = int(0.996*	self.Data["rank"])
		# 	self.WinStreakSum = 0

		
		self.onPlayingBattlefiled = None

		#self.Data["rank"] = 1000
		if self.onPlayingDestroy:
			self.destroy()
			return


		if self.client is not None:
			self.battleResultClientDisplay(result)
		else:
			self.battleResult = result

	def battleResultClientDisplay(self,success = -1):
		if success == -1:
			success == self.battleResult
		self.battleResult = -1

		if success == -1:
			self.getClientPrc()
			return

		rank = self.Data["rank"]

		if self.client == None:
			return

		self.client.battleResultClientDisplay(success,rank)

	def displayBattleResult(self):
		pass

	def onInitBattleField(self,oppoHero):
		self.client.onInitBattleField(oppoHero)

	def reqChangeAvatar(self,roleType,cardList,name,index):
		DEBUG_MSG("reqChangeAvatar Account[%s] roleType[%s] cardList[%s] index[%s]" % (self.id,roleType,str(len(cardList))+"__"+str(cardList),index))

		if index == -1:
			if len(self.Avatar_List) > 17:
				self.client.onChangeAvatar('卡组添加失败达到上限')
				return

			props = {
				"name"				: name,
				"roleType"			: roleType,
				"cardList"			: cardList
				}

			self.Avatar_List.append(props)
			self.client.onChangeAvatar('卡组添加成功')
		else:
			DEBUG_MSG("reqChangeAvatar Account[%s]  index[%s]  cardList[%s]" % (self.id,index,str(len(cardList))+"__"+str(cardList)))
			if index > len(self.Avatar_List)-1:
				self.client.onChangeAvatar('序号出错，大于上限')
				return		
			self.Avatar_List[int(index)]['cardList'] = cardList
			if name != '':
				self.Avatar_List[int(index)]['name'] = namename
			self.client.onChangeAvatar('修改卡组成功')
		self.reqAvatarList()

	def randomInitKZ(self):
		ls = []
		for i in range(30):
			ls.append(random.randint(10000001,10000000+self.cardSum))
		roleType = 0
		name = "随机生成卡组"
		index = -1
		self.reqChangeAvatar(roleType,ls,name,index)

	def reqRemoveAvatar(self, index):
		"""
		exposed.
		客户端请求删除一个角色
		"""
		DEBUG_MSG("Account[%i].reqRemoveAvatar: %s" % (self.id, index))

		if index > len(self.Avatar_List)-1:
			self.client.onChangeAvatar('序号出错，大于上限')
			return
		del self.Avatar_List[int(index)]
		self.client.onChangeAvatar('删除卡组成功')
		self.reqAvatarList()

		
	def reqAvatarList(self):
		"""
		exposed.
		客户端请求查询角色列表
		"""
		DEBUG_MSG("Account[%i].reqAvatarList: size=%i." % (self.id, len(self.Avatar_List)))
		self.client.onReqAvatarList(self.Avatar_List)

	def creatAvatar(self,battleFiled):
		'''
		'''
		DEBUG_MSG("Account[%i].creatAvatar" %(self.id))
		prarm = {
			"battlefiled":battleFiled,
			'nameA':self.Data['name'],
			'roleType':self.Avatar_List[self.willUseKz]['roleType'],
			'cardList':self.Avatar_List[self.willUseKz]['cardList'],
			'playerIDB':self.playerID,
			'account':self					
			}
		self.Avatar0 = KBEngine.createEntityLocally("Avatar", prarm)
		self.client.onInitBattleField()
		self.onPlayingBattlefiled = battleFiled

	def reqHasEnteredBattlefiled(self):
		DEBUG_MSG("Account[%i].reqHasEnteredBattlefiled" %(self.id))
		self.giveClientTo(self.Avatar0)
		self.clientControl = False
		self.Avatar0.onClientInit()

	#--------------------------------------------------------------------------------------------
	#                              Callbacks
	#--------------------------------------------------------------------------------------------

	def onGiveClientToFailure(self):
		ERROR_MSG("Account::onGiveClientToFailure:(%i)" % (self.id))
		


