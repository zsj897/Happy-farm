# -*- coding: utf-8 -*-
import KBEngine
import Functor
from KBEDebug import *
import d_game
import time
import copy
import random
from GlobalDefine import *
from GameRecord import *
from ComFunc import *

#LandType 土地编号（d_game)
#ItemType 物品编号 (d_game)
LAND_TYPE_HUA = 101  #黄土地

class Land(KBEngine.EntityComponent):
	"""
	土地管理
	"""
	def __init__(self):
		 KBEngine.EntityComponent.__init__(self)

	def onAttached(self, owner):
		#DEBUG_MSG("Land::onAttached(): owner=%i" % (owner.id))
		self.CheckALLCDTime()
		
	def onDetached(self, owner):
		#DEBUG_MSG("Land::onDetached(): owner=%i" % (owner.id))
		pass

	def onClientEnabled(self):
		"""
		KBEngine method.
		该entity被正式激活为可使用， 此时entity已经建立了client对应实体， 可以在此创建它的
		cell部分。
        """
		DEBUG_MSG("Land[%i]::onClientEnabled:entities enable." % (self.ownerID))
		self.InitLandData()
		self.InitClientData()

	def InitClientData(self):
		if hasattr(self,'client') and self.client:
			self.reqClientLandInfo()
			#清空管家日志
			self.IsHaveGJ()
			self.Component('Friends').reqAllSysMessage('管家日志')

	def onClientDeath(self):
		"""
		KBEngine method.
		客户端对应实体已经销毁
		"""
		DEBUG_MSG("Land[%i].onClientDeath:" % self.ownerID)	

	def onTimer(self, id, userArg):
		if userArg == TIMER_CD_LAND_5:
			#检测所有倒计时
			self.CheckALLCDTime()

	def Component(self,name):
		return self.owner.getComponent(name)

	def GetGenerator(self,TypeName):
		return self.owner.generatorFac.GetGenerator(TypeName)

	def BuildGenerator(self,TypeName):
		if self.owner is not None:
			self.owner.generatorFac.BuildGenerator(TypeName)

	#检查所有结束时间，土地，管家
	def CheckALLItemEndTime(self, nowTime):
		for LandInfo in self.LandData:
			#检查土地
			self.CheckItemEndTime(nowTime, LandInfo)
			#设置管家收获时间
			self.SetGetEndtime(LandInfo)


	#检查土地时间是否已过，跳到下一个阶段
	def CheckItemEndTime(self, nowTime, LandInfo):
		ItemType = LandInfo['ItemType']
		if ItemType == 0:
			return
		Cstage = self.GetStagebyName(ItemType,'成熟')
		Ystage = self.GetStagebyName(ItemType,'摇树')
		Gstage = self.GetStagebyName(ItemType,'枯树')
		#如果当前时间一直大于当前阶段，就一直跳阶段
		while nowTime >= LandInfo['EndTime']:
			stage = LandInfo['stage']
			if stage >= Gstage :
				self.ClearLandInfo(LandInfo)
				DEBUG_MSG("ClearLandInfo 1:%d,%d" % (stage,Gstage ) )
				return
			if stage == Cstage:
				return
			if stage == Ystage:
				return
			self.NextLandStage(LandInfo)
			#DEBUG_MSG("CheckItemEndTime:%d,%d,%d" % (stage,Cstage,Ystage ) )

	#跳到下一个阶段
	def NextLandStage(self, LandInfo, NowTime = None):
		ItemType = LandInfo['ItemType']
		#改变阶段
		self.ChangeLandInfo2(LandInfo,'stage', LandInfo['stage'] + 1)
		lastStage = LandInfo['stage'] + 1
		Gstage = self.GetStagebyName(ItemType,'枯树')
		if LandInfo['stage'] > Gstage:
			self.ClearLandInfo(LandInfo)
			DEBUG_MSG("ClearLandInfo 2:%d,%d" % (LandInfo['stage'],Gstage ) )
			return
		#枯树期处理
		Ystage = self.GetStagebyName(ItemType,'摇树')
		#当前阶段摇树期计算收获
		Harvest = 0 
		if LandInfo['stage'] == Ystage:
			Harvest = self.CalLandHarvest(LandInfo)
		#下一阶段的倒计时时间
		needTime = self.GetStageNeedTime(ItemType, lastStage)
		if NowTime is None:
			NowTime = LandInfo['EndTime']
		endTime = NowTime + needTime*60
		InfoDcit = {'ItemType':ItemType,'EndTime':endTime ,'surpHarvest':Harvest,'Harvest':Harvest }
		self.ChangeLandInfo(LandInfo, InfoDcit )
		#有管家的话管家处理
		if self.IsHaveGJ():
			self.GJEffect(LandInfo)
		DEBUG_MSG("NextLandStage:%s" % (str(LandInfo) ) )

	#登录的时给客户端发送土地数据
	def reqClientLandInfo(self):
		self.client.onServerTime(int(time.time()))	
		self.client.onAllLandInfo('成功',self.owner.databaseID,self.LandData)
		self.client.onGJInfo(self.owner.databaseID,self.GJData,False)
	'''
	  请求所有土地信息
	'''
	def	reqAllLandInfo(self,DBID):
		self.client.onServerTime(int(time.time()))	
		if DBID == 0:
			self.client.onAllLandInfo('成功',self.owner.databaseID,self.LandData)
			self.client.onGJInfo(self.owner.databaseID,self.GJData,False)
			self.Component("Pet").reqAllPetInfo(0)
			self.Component("bags").reqBags()
		else:
			self.BuildGenerator('CallBackLandInfo') 
			KBEngine.createEntityFromDBID("Account",DBID,Functor.Functor(self.CallBackLandInfo))
		
	def CallBackLandInfo(self,baseRef,databaseID,wasActive):
		INFO_MSG("onFriendLandInfo:%i,%i" % (databaseID, wasActive) )
		if baseRef is None:
			DEBUG_MSG("CallBackLandInfo baseRef error:%i" % databaseID)
			if self.owner is not None:
				self.GetGenerator('CallBackLandInfo').Set(databaseID,self.CallBackLandInfo)
		else:
			Land = baseRef.getComponent("Land")
			Pet = baseRef.getComponent("Pet")
			bags = baseRef.getComponent("bags")
			self.client.onAllLandInfo('成功',databaseID, Land.LandData)
			self.client.onGJInfo(databaseID,Land.GJData,False)
			self.owner.client.onData(baseRef.Data,databaseID)
			self.Component("Pet").client.onAllPetInfo(databaseID,Pet.PetData)
			self.Component("bags").client.onBags(bags.Bags)
			#DEBUG_MSG("CallBackLandInfo Land:%s" % str(Land.LandData))
			if not wasActive:
				baseRef.destroy()
			
	'''
	  请求土地信息
	'''
	def reqLandInfo(self, LandID):
		LandInfo = self.GetLandInfo(LandID)
		if LandInfo is None:
			self.client.onLandInfo('LandID错误', {})
			return
		self.CheckLandCDTime(LandInfo)
		self.client.onLandInfo('成功', LandInfo)
		DEBUG_MSG("reqLandInfo:%s" % str(LandInfo) )
	
	'''
	  购买土地
	'''
	#Land 赠送对象的土地
	def BuyLand(self, DBID,LandType, Land):
		#判断金钱
		d_Land = self.GetConfigLandInfo(LandType)
		if d_Land is None:
			self.client.onBuyLand('LandType错误')
			return -3
		priceType = d_Land['priceType']
		Value = d_Land['Value']
		if Value == 0: 
			self.client.onBuyLand('黄土地非卖品' )
			return -4
		errcode = self.owner.ChangeBaseData(priceType, -Value,'减少，购买土地')
		if errcode < 0 :
			self.client.onBuyLand('金币不够')
			return -5
		LandID = Land.AddLand( LandType, d_Land['useNum'])
		LandInfo = Land.GetLandInfo(LandID)
		self.client.onBuyLand('成功')
		self.Component("Friends").SYSMessage(DBID, 4001, int(time.time()) , d_Land['Value'],d_Land['LandType'])
		return LandID

	def	reqBuyLand(self,DBID,LandType):
		INFO_MSG("reqBuyLand:%i,%i" % (DBID, LandType) )
		#判断ID是否超出
		if DBID == 0:
			self.BuyLand(DBID,LandType,self)	
		else:
			self.BuildGenerator('CallBackBuyLand')
			KBEngine.createEntityFromDBID("Account",DBID,Functor.Functor(self.CallBackBuyLand,LandType))
	
	def CallBackBuyLand(self,LandType,baseRef,databaseID,wasActive):
		INFO_MSG("onFriendBuyLand:%i,%i" % (databaseID, wasActive) )
		if baseRef is None:
			DEBUG_MSG("CallBackBuyLand baseRef error:%i" % databaseID)
			if self.owner is not None:
				self.GetGenerator('CallBackBuyLand').Set(databaseID,self.CallBackBuyLand,LandType)
		else:
			Land = baseRef.getComponent("Land")
			LandID = self.BuyLand(databaseID,LandType, Land)	
			if LandID > 0:
				if wasActive:
					baseRef.client.onFriendBuyLand(self.owner.databaseID)
			INFO_MSG("onFriendBuyLand:%i,%i,%s" % (LandID,LandType,str(Land.LandData) ) )
			if not wasActive:
				baseRef.destroy()
		
	'''
	  赠送土地
	'''
	def	reqGiveLand(self, DBID, LandID):
		INFO_MSG("reqGiveLand:%i,%i" % (DBID, LandID) )
		#判断是否已经有这个块土地
		Maxid = len(self.LandData)
		if LandID > Maxid or LandID == 1:
			self.client.onGiveLand('没有这块土地')
			return -1
		#土地有种子也不能送
		LandInfo = self.GetLandInfo(LandID)

		if LandInfo['ItemType'] != 0:
			self.client.onGiveLand('种植中的土地不能赠送')
			return -2
		if LandInfo['LandType'] == 0:
			self.client.onGiveLand('未购买')
			return -3
		self.BuildGenerator('CallFriendGiveLand')
		KBEngine.createEntityFromDBID("Account",DBID,Functor.Functor(self.CallFriendGiveLand,LandInfo))
		return 0

	def CallFriendGiveLand(self,LandInfo,baseRef,databaseID,wasActive):
		if baseRef is None:
			DEBUG_MSG("CallFriendGiveLand baseRef error:%i" % databaseID)
			if self.owner is not None:
				self.GetGenerator('CallFriendGiveLand').Set(databaseID,self.CallFriendGiveLand,LandInfo)
		else:
			selfLandInfo = copy.deepcopy(LandInfo)
			Land = baseRef.getComponent("Land")
			#增加好友的土地
			if Land.AddLand2(selfLandInfo):
				#删除自己土地
				self.DelLand(LandInfo['ID'],'赠送给别人')
				self.client.onGiveLand('成功')
				#记录消息
				d_land = self.GetConfigLandInfo(selfLandInfo['LandType'] )
				self.Component("Friends").SYSMessage(databaseID, 3004, int(time.time()) , self.owner.Data['name'],d_land['LandType'],selfLandInfo['UseNum'])
			else:
				self.client.onGiveLand('对方土地数量已达上限')
			if not wasActive:
				baseRef.destroy()
	'''
	  土地种植
	'''
	def reqPlant(self, LandID, ItemType):
		INFO_MSG("reqPlant:%i,%i" % (LandID, ItemType) )
		#有种子不能播
		LandInfo = self.GetLandInfo(LandID)
		if LandInfo is None:
			self.client.onPlant('LandID错误')
			return -1
		if LandInfo['ItemType'] != 0 :
			self.client.onPlant('已经有种子')
			return -2
		#判断土地的使用次数
		if LandInfo['LandType'] != LAND_TYPE_HUA:
			if LandInfo['UseNum'] <= 0:
				self.client.onPlant('土地使用次数已用完')
				return -3
		#使用道具
		argDict = {'LandId':LandID, 'LandType':LandInfo['LandType'] }
		err = self.Component("bags").UseItem(ItemType, argDict,Des='土地种植,土地ID:%d' % LandID)
		if err != 0:
			self.client.onPlant('背包没有该物品')
			DEBUG_MSG("reqLandInfo UseItem:%i" % err )
			return -4
		needtime = self.GetStageNeedTime(ItemType, 1)
		if needtime <0:
			self.client.onPlant('获得该物品的阶段时间错误')
			return -5
		nowtime = int(time.time() )	
		endTime = nowtime + needtime*60
		InfoDcit = {'ItemType':ItemType,'stage':0, 'EndTime':endTime }
		self.ChangeLandInfo(LandInfo, InfoDcit )
		self.CheckLandCDTime(LandInfo)
		self.client.onPlant('成功')
		INFO_MSG("reqPlant 成功 当前时间:%i,土地：%s" % (nowtime,str(LandInfo)) )
		return 0

	'''
	  土地施肥
	'''
	def reqfertilization(self, LandID, ItemType, num):
		LandInfo = self.GetLandInfo(LandID)
		if LandInfo is None:
			self.client.onfertilization('LandID错误' )
			return -1
		if num < 1:
			self.client.onfertilization('数量错误' )
			return -2
		if LandInfo['ItemType'] == 0:
			self.client.onfertilization('该土地没有种子')
			return
		stageName = self.GetNamebyStage(LandInfo['ItemType'],LandInfo['stage'])
		#使用道具
		argDict = {'LandId':LandID, 'stageName': stageName}
		err = self.Component("bags").UseItem(ItemType, argDict, num,Des='土地施肥,土地ID:%d' % LandID)
		if err == -1:
			self.client.onfertilization('无法在该阶段使用该化肥')
			return -3
		if err == -2:
			self.client.onfertilization('化肥数量不够')
			return -4
		if err == -3:
			self.client.onfertilization('背包没有该化肥')
			return -5
		return 0			

	def fertilization(self, LandID, delTime):
		LandInfo = self.GetLandInfo(LandID)
		if LandInfo is None:
			self.client.onfertilization('LandID错误' )
			return
		endtime = LandInfo['EndTime']
		self.ChangeLandInfo2(LandInfo,'EndTime', endtime - delTime)
		nowtime = int(time.time() )	
		self.CheckItemEndTime(nowtime, LandInfo)
		self.CheckLandCDTime(LandInfo)
		self.client.onfertilization('成功')
		INFO_MSG("fertilization 成功 当前时间:%i,土地：%s" % (nowtime,str(LandInfo)) )

	def fertilization2(self, LandID):
		LandInfo = self.GetLandInfo(LandID)
		if LandInfo is None:
			self.client.onfertilization('LandID错误')
			return
		self.NextLandStage(LandInfo, int(time.time()))
		self.CheckLandCDTime(LandInfo)
		self.client.onfertilization('成功')
		INFO_MSG("fertilization2  土地：%s" % (str(LandInfo)) )

	'''
	  获取配置
	'''
	def GetLandData(self):
		return self.LandData
	def GetLandInfo(self, LandID):
		try:
			LandInfo = self.LandData[LandID-1]
		except (IndexError, KeyError) as e:
			return None
		return LandInfo 
	def GetConfigLandInfo(self, LandType):
		try:
			Info = d_game.LandInfo[LandType]
		except (IndexError, KeyError) as e:
			ERROR_MSG("GetConfigLandInfo error:%s, LandType:%i" % (str(e), LandType))
			return None
		return Info
	def GetConfigLandSeed(self, ItemType):
		try:
			Info = d_game.LandSeed[ItemType]
		except (IndexError, KeyError) as e:
			ERROR_MSG("GetConfigLandSeed error:%s, ItemType:%i" % (str(e), ItemType))
			return None
		return Info
	
	#只有摇树阶段才需要摇树
	def GetItemListByStage(self, Name):
		ItemIDList = []
		for info in d_game.LandSeed.values():
			stageName = info['stageName']
			if Name in stageName:
				ItemIDList.append(info['ItemID'])
		return ItemIDList

	def GetConfigGJInfo(self):
		try:
			Info = d_game.GJInfo[self.GJData['GJType'] ]
		except (IndexError, KeyError) as e:
			ERROR_MSG("GetConfigGJInfo error:%s, GJType:%i" % (str(e), self.GJData['GJType'] ))
			return None
		return Info

	
	'''
	 管家功能
	'''
	#请求管家收获
	def reqGJInfo(self):
		pass

	def YaoShuStatus(self, GJGetEndtime):
		if self.Component("Friends").YaoEndTime != 0:
			return self.Component("Friends").MasterYaoShuHandler(GJGetEndtime)
		return False

	def CheckGJGetEndtime(self,nowtime):
		if self.GJData['GJGetEndtime'] != 0 and nowtime > self.GJData['GJGetEndtime']:
			#此时有摇树状态,直接结算摇树。
			if self.YaoShuStatus(self.GJData['GJGetEndtime']):
				INFO_MSG("YaoShu is success! ")
				return
			HarvestList = []
			LandList = []
			for LandInfo in self.LandData:
				if LandInfo['ItemType'] == 0:
					continue
				Ystage = self.GetStagebyName(LandInfo['ItemType'],'摇树')
				if LandInfo['stage'] == Ystage:
					self.ChangeLandInfo2(LandInfo, 'EndTime', self.GJData['GJGetEndtime'])
					self.TotalHarvest(HarvestList,LandList,LandInfo)
					self.NextLandStage(LandInfo)
					self.CheckItemEndTime(int(time.time()), LandInfo)
			INFO_MSG("HarvestList :%s,%s" % (str(HarvestList),str(LandList)) )
			#收获 
			for Harvest in HarvestList:
				self.Component("bags").AddItem(Harvest['ItemType'],Harvest['Harvest'], '管家收益')
			#管家日志
			self.GJLog(HarvestList,LandList)
			#清空管家收获时间
			self.SetGJGetEndtime(0)

	#统计
	def TotalHarvest(self, HarvestList, LandList, LandInfo):
		#统计收获列表
		ItemType = LandInfo['ItemType']
		surpHarvest = LandInfo['surpHarvest']
		d_Item = self.GetOutItem(ItemType)
		if d_Item is None:
			ERROR_MSG("TotalHarvest error ItemType:%i" % (ItemType))
			return
		hasItemType = False
		for Harvest in HarvestList:
			if Harvest['ItemType'] == d_Item['ID']:
				Harvest['Harvest'] += surpHarvest
				hasItemType = True
				break
		if not hasItemType:
			HarvestList.append({'ItemType':d_Item['ID'], 'Harvest':surpHarvest,'ItemName':d_Item['ItemName']})
		#统计收获的土地信息
		LandType = LandInfo['LandType']
		hasLandType = False
		for land in LandList:
			if land['LandType'] == LandType:
				land['LandNum'] += 1
				hasLandType = True
				break
		if not hasLandType:
			d_Land = self.GetConfigLandInfo(LandType)
			LandList.append({'LandType':LandType, 'LandNum':1, 'LandName':d_Land['LandType']})

	#记录管家日志
	def GJLog(self, HarvestList, LandList):
		if not HarvestList:
			return
		arg1 = ''
		arg2 = ''
		for land in LandList:
			arg1 += ',' + str(land['LandNum']) + '块' + land['LandName']
		arg1 = arg1[1:]
		for Harvest in HarvestList:
			TotalValue = Harvest['Harvest']
			ItemType = Harvest['ItemType']
			if ItemType == 3 or ItemType == 4:
				TotalValue = float(TotalValue/100)
			arg2 += ',' + str(TotalValue) + '个' + Harvest['ItemName']
		arg2 = arg2[1:]
		self.Component("Friends").SYSMessage(0, 5001, self.GJData['GJGetEndtime'], arg1, arg2)
		INFO_MSG("GJLog :%s,%s" % (arg1, arg2) )
	
	#管家影响摇树，枯树
	def GJEffect(self, LandInfo):
		self.GuShuEffect(LandInfo)
		return 0

	#设置收获倒计时
	def SetGetEndtime(self,LandInfo):
		if not self.IsHaveGJ():
			return -1
		if self.GJData['GJGetEndtime'] != 0:
			return -2
		ItemType = LandInfo['ItemType']
		if ItemType == 0:
			return -3
		Ystage = self.GetStagebyName(ItemType,'摇树')
		if LandInfo['stage'] != Ystage:
			return -4
		d_GJInfo = self.GetConfigGJInfo()
		if d_GJInfo is None:
			return -5
		timeInterval = d_GJInfo['timeInterval']
		Time = random.randint(timeInterval[0],timeInterval[1])
		endTime = int(time.time()) + Time*60
		self.SetGJGetEndtime(endTime)
		return 0

	def GuShuEffect(self,LandInfo):
		ItemType = LandInfo['ItemType']
		if ItemType == 0:
			return -1
		Gstage = self.GetStagebyName(ItemType,'枯树')
		if LandInfo['stage'] != Gstage:
			return -2
		d_GJInfo = self.GetConfigGJInfo()
		if d_GJInfo is None:
			return -3
		self.ChangeLandStageTime(LandInfo, Gstage, -d_GJInfo['delTime'])
		return 0
	
	def IsHaveGJ(self):
		nowtime = int(time.time())
		if self.GJData['GJEndtime'] == 0:
			return False
		if self.GJData['GJEndtime'] > nowtime:
			return True
		else:
			#离线不清理管家，因为要通知客户端弹框
			if hasattr(self,'client') and self.client:
				self.clearGJ()
			return False

	#改变种子某阶段的时间
	def ChangeLandStageTime(self, LandInfo, stage, Time):
		if LandInfo['stage'] == stage:
			endtime = LandInfo['EndTime']
			if endtime == 0:
				endtime = int(time.time() )
			self.ChangeLandInfo2(LandInfo,'EndTime', endtime + Time*60)	
		INFO_MSG("ChangeLandStageTime :%i,%i,%i" % (stage, endtime, Time*60 ) )

	#设置管家属性
	def SetGJ(self , GJType, endtime):
		if self.GJData['GJType'] == 0:
			self.GJData['GJType'] = GJType
			self.GJData['GJEndtime'] = endtime
			self.GJData['GJGetEndtime'] = 0
			nowtime = int(time.time() )	
			self.client.onGJInfo(self.owner.databaseID,self.GJData,False)
			INFO_MSG("SetGJ DBID:%i, :%s" % ( self.owner.databaseID,str(self.GJData)) )
			
	#清空管家,已到期
	def clearGJ(self):
		if self.GJData['GJType'] != 0:
			INFO_MSG("clearGJ DBID:%i,:%s" % (self.owner.databaseID, str(self.GJData)) )
			self.GJData['GJType'] = 0
			self.GJData['GJEndtime'] = 0
			self.client.onGJInfo(self.owner.databaseID,self.GJData,True)
			self.Component('Friends').ClearMessage('管家日志')
			
	def SetGJGetEndtime(self, Time):
		self.GJData['GJGetEndtime'] = Time
		if hasattr(self,'client') and self.client:
			self.client.onGJInfo(self.owner.databaseID,self.GJData,False)
		INFO_MSG("SetGJGetEndtime  DBID:%i,:%s" % (self.owner.databaseID, str(self.GJData)) )

	
	'''
	 土地收获 土地类型收益 + 种子收益 - 好友摇树获得的收益 - 被偷的收益
	'''
	#计算某块的土地收益
	def CalLandHarvest(self, LandInfo):
		stage = self.GetStagebyName(LandInfo['ItemType'],'摇树')
		if LandInfo['stage'] != stage:
			return 0
		d_LandInfo = self.GetConfigLandInfo(LandInfo['LandType'])
		if d_LandInfo is None:
			return 0
		output = d_LandInfo['output']
		if output :
			result = random.randint(output[0], output[1]) 
			return result
		return 0

	#获得服务器保存的某种产品的产量
	def GetAllLandHarvest(self, ItemType, name):
		result = 0
		for LandInfo in self.LandData:
			result += self.GetLandHarvest(LandInfo , ItemType, name)
		return result

	def GetLandHarvest(self, LandInfo, ItemType, name):
		if LandInfo['ItemType'] == 0:
			return 0
		stage = self.GetStagebyName(LandInfo['ItemType'],'摇树')
		if LandInfo['stage'] != stage:
			return 0
		if LandInfo['ItemType'] != ItemType:
			return 0
		return LandInfo[name]

	#偷取所有土地
	def StealAllLand(self, CanStealLandlist):
		StealTotalInfo = {} #记录E币或其他物品偷取数量
		StealLandInfo = []  #记录某块土地被偷值
		for LandInfo in CanStealLandlist:
			prob = None  
			if self.IsHaveGJ():  #  管家的概率抓取偷盗者
				d_GJInfo = self.GetConfigGJInfo()
				if d_GJInfo is None:
					continue
				prob = d_GJInfo['probability']
			value = self.StealLand(LandInfo,prob)
			if value <= 0:
				continue
			StealLandInfo.append({'LandID':LandInfo['ID'], 'StealValue':value })
			d_OutItem = self.GetOutItem(LandInfo['ItemType'])
			ItemType = d_OutItem['ID']
			if ItemType in StealTotalInfo.keys():
				StealTotalInfo[ItemType] += value
			else:
				StealTotalInfo[ItemType] = value
		return StealTotalInfo,StealLandInfo

	#偷取某块土地
	def StealLand(self, LandInfo , prob = None):
		#判断管家是否抓到偷盗者,true : 代表抓到，什么也没偷到
		if prob is not None and IsProbability(prob)[0]:
			return -1
		#某块土地可以被偷的值
		d_LandInfo = self.GetConfigLandInfo(LandInfo['LandType'])
		if d_LandInfo is None:
			return -2
		StealHarvest = d_LandInfo['StealHarvest']
		if StealHarvest :
			Steal = random.randint(StealHarvest[0], StealHarvest[1])
			surpHarvest = LandInfo['surpHarvest']
			CanStealValue = surpHarvest - int(LandInfo['Harvest']/2)
			if Steal >= CanStealValue:
				Steal = CanStealValue
			if Steal != 0:
				self.ChangeLandInfo2(LandInfo,'surpHarvest', surpHarvest - Steal)
			return Steal
		return -3

	'''
	 摇树 功能
	'''
	#是否有成熟的土地
	def IsYaoShuLand(self):
		for LandInfo in self.LandData:
			if LandInfo['ItemType'] == 0:
				continue
			YaoStage = self.GetStagebyName(LandInfo['ItemType'],'摇树')
			if LandInfo['stage'] == YaoStage:
				return True
		return False
		
	#响应摇树处理
	def OnYaoshuEndHandler(self,ItemType,YaoEndTime, deltime):
		YaoStage = self.GetStagebyName(ItemType,'摇树')
		#所有摇树的土地跳到下一阶段
		for LandInfo in self.LandData:
			if LandInfo['ItemType'] == ItemType and LandInfo['stage'] == YaoStage:
				self.NextLandStage(LandInfo, YaoEndTime)
				#减短到空土地的时间
				self.ChangeLandStageTime(LandInfo, YaoStage+1, -deltime)
		INFO_MSG("OnYaoshuEndHandler:%d" % (ItemType ) )

	'''
	 偷树 功能
	'''
	#有一块土地可偷，便可以偷
	def IsAllCanSteal(self,DBID):
		LandList = []
		for LandInfo in self.LandData:
			if self.IsCanSteal(LandInfo,DBID):
				LandList.append(LandInfo)
		if LandList:
			return True, LandList
		else:
			return False, LandList

	# true：可偷  false: 不可偷
	def IsCanSteal(self,LandInfo,DBID):
		#土地是否摇树阶段
		if LandInfo['ItemType'] == 0:
			return False
		#黄土地不可被偷
		if LandInfo['LandType'] == LAND_TYPE_HUA:
			return False
		YaoStage = self.GetStagebyName(LandInfo['ItemType'],'摇树')
		if LandInfo['stage'] != YaoStage:
			#DEBUG_MSG("IsCanSteal stage error LandInfo:%s,%d" % (str(LandInfo) , DBID) )
			return False
		#该土地值是否小于总产量的一半
		if LandInfo['surpHarvest'] <= int(LandInfo['Harvest']/2):
			#DEBUG_MSG("IsCanSteal 0.5 error LandInfo:%s,%d,DBID:%d" % (str(LandInfo),LandInfo['Harvest']/2, DBID) )	
			return False
		#是否已偷过
		if	FindSplitStr(LandInfo['StealList'],str(DBID) ):
			DEBUG_MSG("IsCanSteal already steal LandInfo:%s,DBID:%d" % (LandInfo['StealList'] , DBID) )	
			return False
		return True

	# 被其他人偷树 DBID:偷树人 name：偷树人名字
	def BySteal(self, DBID):
		#查找所有土地的 当前是否可以被偷
		IsCan, LandList = self.IsAllCanSteal(DBID)
		if not IsCan:
			return -1,None,None
		#标记已偷过
		for LandInfo in LandList:
			self.AddSteal(LandInfo,DBID)
		# 计算土地被偷的值
		StealTotalInfo,StealLandInfo = self.StealAllLand(LandList)
		DEBUG_MSG("BySteal LandList:%s" % str(LandList)  )
		DEBUG_MSG("BySteal StealTotalInfo:%s" % str(StealTotalInfo)  )
		DEBUG_MSG("BySteal StealLandInfo:%s" % str(StealLandInfo)  )
		#有管家需要判断情况
		if self.IsHaveGJ():
			if not StealTotalInfo: #被管家抓住，毫无所获			
				return -2,None,None
			elif len(StealLandInfo) != len(LandList): #两个相等表示管家一块土地都没抓住，被管家抓住，有收获
				return -3,StealTotalInfo,StealLandInfo
		#没有被管家抓到，有收获
		return 0,StealTotalInfo,StealLandInfo

	'''
	 获得
	'''
	#客户端的土地结束时间需要直接倒计时，服务器记录的是时间戳
	def CheckLandCDTime(self,LandInfo):
		nowtime = int(time.time() )	
		self.CheckItemEndTime(nowtime,LandInfo)
	
	def CheckALLCDTime(self):
		nowtime = int(time.time() )	
		#检查所有土地种子时间
		self.CheckALLItemEndTime(nowtime)
		#检查管家收获时间
		self.CheckGJGetEndtime(nowtime)

	#获得阶段需要的成长时间
	def GetStageNeedTime(self,ItemType, stage):
		d_Seed	= self.GetConfigLandSeed(ItemType)
		if d_Seed is None:
			return -1
		if stage < 0:
			return -2
		if stage >= len(d_Seed['time']):
			ERROR_MSG("GetStageNeedTime error:%i,%i" %  (ItemType,stage) )
			return -3
		return d_Seed['time'][stage]
	#活动种子最大阶段	
	def GetStageLen(self, ItemType):
		d_Seed	= self.GetConfigLandSeed(ItemType)
		if d_Seed is None:
			return 0
		return len(d_Seed['stage'])
	#根据阶段名获得对应的阶段数
	def GetStagebyName(self, ItemType, StageName):
		d_Seed	= self.GetConfigLandSeed(ItemType)
		if d_Seed is None:
			return -1
		for i,name in enumerate(d_Seed['stageName']):
			if name == StageName:
				return d_Seed['stage'][i]
		return -2
	#根据阶段获得名称
	def GetNamebyStage(self, ItemType, Stage):
		d_Seed	= self.GetConfigLandSeed(ItemType)
		if d_Seed is None:
			return -1
		for i,stage in enumerate(d_Seed['stage']):
			if stage == Stage:
				return d_Seed['stageName'][i]
		return -2
	#获得种子的产出物品类型
	def GetOutItem(self, ItemType):
		INFO_MSG("GetOutItem:%i" % (ItemType) )
		d_Seed	= self.GetConfigLandSeed(ItemType)
		if d_Seed is None:
			return None
		d_Item = self.Component("bags").GetConfigItem(d_Seed['outputID'])
		return d_Item

	#初始化土地数据
	def InitLandData(self):
		if len(self.LandData)== 0:
			self.AddLand( LAND_TYPE_HUA ,0)
			
	#清除土地信息
	def ClearLandInfo(self,LandInfo):
		#黄土地可以一直使用
		InfoDcit = {'ItemType':0,'stage':0,'EndTime':0,'surpHarvest':0,'Harvest':0,'StealList':'' }
		if LandInfo['LandType'] == LAND_TYPE_HUA:
			self.ChangeLandInfo(LandInfo, InfoDcit )
			return
		if LandInfo['UseNum'] > 1:
			InfoDcit['UseNum'] = LandInfo['UseNum'] -1
			self.ChangeLandInfo(LandInfo, InfoDcit )
		else: #使用次数用完
			self.DelLand(LandInfo['ID'],'次数用完')
			
	#查找土地空闲的ID
	def FindFreeLandID(self):
		for LandInfo in self.LandData:
			if LandInfo['LandType'] == 0:
				return LandInfo['ID']
		Maxlen = len(self.LandData)
		if Maxlen >= 36:
			return 0
		else:
			return Maxlen + 1

	#添加土地
	def AddLand(self,LandType,UseNum):
		LandID = self.FindFreeLandID()
		LandInfo = self.GetLandInfo(LandID)
		LandDict = {'ID':LandID, 'LandType':LandType,'UseNum':UseNum,'ItemType':0,'stage':0,'EndTime':0,'surpHarvest':0,'Harvest':0,'StealList':''}
		if LandInfo is None:
			self.LandData.append(LandDict)
			if hasattr(self,'client') and self.client:
				self.client.onLandInfo('成功', LandDict)
			DEBUG_MSG("AddLand LandDict:%i,%s" %  (self.ownerID,str(LandDict)) )
		else:
			self.ChangeLandInfo(LandInfo, LandDict )
			DEBUG_MSG("AddLand LandInfo:%i,%s" %  (self.ownerID,str(LandInfo)) )
		GameLandRecord(self.owner.AccountName(),self.owner.databaseID,LandType,1,'增加土地：购买，LandID:%i' % (LandID) )
		return LandID
		
	def AddLand2(self,LandInfo):
		LandID = self.FindFreeLandID()
		if LandID == 0:
			return False
		LandInfo['ID'] = LandID
		land_info = self.GetLandInfo(LandID)
		if land_info is None:
			self.LandData.append(LandInfo)
		else:
			self.LandData[LandID-1] = LandInfo
		if hasattr(self,'client') and self.client:
			self.client.onLandInfo('成功', LandInfo)
		DEBUG_MSG("AddLand2 :%i,%s" %  (self.ownerID,str(self.LandData[LandID-1])) )
		GameLandRecord(self.owner.AccountName(),self.owner.databaseID,LandInfo['LandType'],1,'增加土地：赠送, LandID:%i,剩余次数:%i' % (LandID,LandInfo['UseNum']) )
		return True

	#删除土地
	def DelLand(self, LandID, Des):
		LandInfo = self.GetLandInfo(LandID)
		if LandInfo is None:
			return
		LandType = LandInfo['LandType']
		LandDict = {'LandType':0,'UseNum':0,'ItemType':0,'stage':0,'EndTime':0,'surpHarvest':0,'Harvest':0,'StealList':''}
		self.ChangeLandInfo(LandInfo, LandDict )
		DEBUG_MSG("DelLand:%i,%s" % (self.ownerID, str(LandInfo) ) )
		GameLandRecord(self.owner.AccountName(),self.owner.databaseID,LandType,1,'销毁土地：%s, LandID:%i' % (Des,LandID) )

	#修改土地信息
	def ChangeLandInfo(self, LandInfo, InfoDcit):
		if 'LandType' in InfoDcit.keys():
			LandInfo['LandType'] = InfoDcit['LandType'] 
		if 'ItemType' in InfoDcit.keys():
			LandInfo['ItemType'] = InfoDcit['ItemType']
		if 'UseNum' in InfoDcit.keys():
			LandInfo['UseNum'] = InfoDcit['UseNum']
		if 'stage' in InfoDcit.keys():
			LandInfo['stage'] = InfoDcit['stage']
		if 'EndTime' in InfoDcit.keys():
			LandInfo['EndTime'] = InfoDcit['EndTime']
		if 'surpHarvest' in InfoDcit.keys():
			LandInfo['surpHarvest'] = InfoDcit['surpHarvest']
		if 'Harvest' in InfoDcit.keys():
			LandInfo['Harvest'] = InfoDcit['Harvest']
		if hasattr(self,'client') and self.client:
			self.client.onLandInfo('成功', LandInfo)
		DEBUG_MSG("ChangeLandInfo:%i,%s" % (self.ownerID,str(LandInfo) ) )

	def ChangeLandInfo2(self, LandInfo, Key, value):
		if Key == 'ItemType':
			LandInfo['ItemType'] = value
		elif Key == 'UseNum':
			LandInfo['UseNum'] = value
		elif Key == 'stage':
			LandInfo['stage'] = value
		elif Key == 'EndTime':
			LandInfo['EndTime'] = value
		elif Key == 'surpHarvest':
			LandInfo['surpHarvest'] = value
		elif Key == 'Harvest':
			LandInfo['Harvest'] = value
		if hasattr(self,'client') and self.client:
			self.client.onLandInfo('成功', LandInfo)
		DEBUG_MSG("ChangeLandInfo2:%i,%s" % (self.ownerID,str(LandInfo) ) )

	def AddSteal(self, LandInfo, StealDBID):
		if LandInfo['StealList']:
			LandInfo['StealList'] += ',' + str(StealDBID)
		else: 
			LandInfo['StealList'] = str(StealDBID) 
		DEBUG_MSG("AddSteal:%i,%s" % (LandInfo['ID'],str(LandInfo['StealList']) ) )




