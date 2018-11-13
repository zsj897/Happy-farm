# -*- coding: utf-8 -*-
import KBEngine
import random
import time
from KBEDebug import *
import Functor
import datetime
from Poller import *
from ComFunc import *

Time_CD_AR = 60*3

class Hall(KBEngine.Entity):
	"""
	大厅管理器实体
	该实体管理该服务组上所有的大厅
	"""
	def __init__(self):
		DEBUG_MSG("Hall init")
		KBEngine.Entity.__init__(self)
		#储存大厅
		KBEngine.globalData["Halls"] = self
		# 存放所有正在匹配玩家ENTITYCALL
		self.OnMarchingPlayer = []
		# 存放所有在线玩家ENTITYCALL
		self.player = []
		# 检测是否正在匹配
		self.OnMarch = 0
		#定时更新当前玩家
		#self.addTimer(1, 120, 1)
		#匹配程序
		#self.addTimer(1,2,2)
		#从数据库读取AR配置数据
		self.addTimer(1,Time_CD_AR,1)
		#每隔10秒检查地图宠物是否过期，是否需要刷新
		self.addTimer(1,10,2)
		#http服务器
		self.addTimer(1,0.5,3)
		g_Poller.StartServer()

	def onTimer(self, id, userArg):
		#DEBUG_MSG(id, userArg)
		#更新在线人数
		# if userArg == 1:
		# 	self.UpdataPlayer()
		# elif userArg ==2:
		# 	self.March()
		if userArg == 1:
			self.UpdatePetMapConfig()
		elif userArg == 2:
			self.CreatePetMapInfo()
		elif userArg == 3:
			g_Poller.tickTornadoIOLoop()
			g_Generator.Get()

	#充值
	def ReChange(self, DBID, errMsg, moneyType, moneyValue):
		KBEngine.createEntityFromDBID("Account",DBID,Functor.Functor(self.onReChange,errMsg,moneyType,moneyValue))
			
	def onReChange(self,errMsg,moneyType,moneyValue,baseRef,databaseID,wasActive):
		if baseRef is None:
			DEBUG_MSG("onReChange baseRef error:%i" % databaseID)
			g_Generator.Set(databaseID,self.onReChange,errMsg,moneyType,moneyValue)
		else:
			if errMsg == 'success':
				baseRef.ChangeBaseData(moneyType,moneyValue,'充值')
				baseRef.Data['FirstRecharge'] = 1
			bags = baseRef.getComponent("bags")
			bags.client.onRecharge(errMsg,moneyType,moneyValue)
			INFO_MSG("onReChange:%s,%i,%i" % (errMsg,databaseID, moneyValue ) )
			if not wasActive:
				baseRef.destroy()

	def March(self):
		#正在匹配则返回
		if self.OnMarch == 1:
			return
		self.OnMarch = 1
		#DEBUG_MSG("Server Start A March")
		for i in range(len(self.OnMarchingPlayer)):
			IsSuccessed = 0
			for j in range(len(self.OnMarchingPlayer)):
				if i == j:
					continue
				if (self.OnMarchingPlayer[j].Data["rank"] > self.OnMarchingPlayer[i].Data["rank"]*(1-0.01*self.OnMarchingPlayer[i].HaveMarchSum) - self.OnMarchingPlayer[i].HaveMarchSum and 
					self.OnMarchingPlayer[j].Data["rank"] < self.OnMarchingPlayer[i].Data["rank"]*(1+0.01*self.OnMarchingPlayer[i].HaveMarchSum) + self.OnMarchingPlayer[i].HaveMarchSum):
					DEBUG_MSG("March Successed player1:%i player2:%i" %(self.OnMarchingPlayer[i].id,self.OnMarchingPlayer[j].id))
					self.CreatBattleField(self.OnMarchingPlayer[i],self.OnMarchingPlayer[j])
					IsSuccessed = 1
			if IsSuccessed == 0:
				self.OnMarchingPlayer[i].HaveMarchSum +=1
			else:
				break
		# 匹配成功后跳出匹配 防止再次匹配时再弄到J那个
		# 通过添加定时器调用此函数
		self.OnMarch = 0

	def CreatBattleField(self,player1,player2):
		#成功匹配完成后再调用一次匹配 增加匹配的效率
		DEBUG_MSG("Start a battle player1:%i player2:%i" %(player1.id,player2.id))
		if player1.isDestroyed or player2.isDestroyed:
			if player1.isDestroyed:
				self.OnMarchingPlayer.remove(player1)
			if player2.isDestroyed:
				self.OnMarchingPlayer.remove(player2)
			DEBUG_MSG("March Fail because One is destroyed")
			return
		DEBUG_MSG("Battle March Successed player1:%i player2:%i" %(player1.id,player2.id))
		 
		KBEngine.createEntityAnywhere("BattleField", 
									{"player0":player1,\
									 "player1":player2},  Functor.Functor(self.onBattleCreatedCB) )

		if player1 in self.OnMarchingPlayer:
			self.OnMarchingPlayer.remove(player1)
		if player2 in self.OnMarchingPlayer:		
			self.OnMarchingPlayer.remove(player2)
		self.March()

	def onBattleCreatedCB(self, BattleEntity):
		DEBUG_MSG("Spaces::onBattleCreatedCB: entityID=%i" % ( BattleEntity.id) )

	def UpdataPlayer(self):
		#此函数更新在线人数和正在匹配的玩家人数 删除实体被销毁的
		for i in range(len(self.player)):
			if self.player[i].isDestroyed == True:
				DEBUG_MSG("del_self.player::player")
				del self.player[i]
				self.UpdataPlayer()
				return
			# if hasattr(self.player[i], 'client'):
			# 	self.player[i].destroy()

		for i in range(len(self.OnMarchingPlayer)):
			if self.OnMarchingPlayer[i].isDestroyed == True:
				DEBUG_MSG("del_self.OnMarchingPlayer::OnMarchingPlayer")
				del self.OnMarchingPlayer[i]
				self.UpdataPlayer()
				return
		DEBUG_MSG("onlineSum:%i" % len(self.player))
		#DEBUG_MSG("OnMarchingSum:%i" % len(self.OnMarchingPlayer))


	def reqAddPlayer(self,player):
		#此函数添加上线玩家入列表
		if player in self.player: 
			return
		DEBUG_MSG("Account[%i].reqAddPlayer:" % player.id)
		self.player.append(player)

	def reqPlayerSum(self,player):
		#此函数是为了获得在线人数
		#此函数是为了获得正在匹配人数
		#DEBUG_MSG("Account[%i].reqPlayerSum:" % player.id)
		player.OnPlayerSum(len(self.player),len(self.OnMarchingPlayer))


	def reqAddMarcher(self,player):
		#此函数添加匹配玩家入列表
		DEBUG_MSG("Account[%i].reqAddMarcher:" % player.id)
		if player in self.OnMarchingPlayer: 
			return
		player.HaveMarchSum =0
		self.OnMarchingPlayer.append(player)

	def reqDelMarcher(self,player):
		#此函数删除匹配玩家从列表
		DEBUG_MSG("Account[%i].reqDelMarcher:" % player.id)
		if player not in self.OnMarchingPlayer: 
			return
		self.OnMarchingPlayer.remove(player)

	'''
	 宠物地图
	'''
	def GetPetMapInfoList(self, cityName):
		#模糊筛选该城市数据
		PetMapInfoList = []
		for PetMapInfo in self.PetMapInfoList:
			if PetMapInfo['cityName'].find(cityName) != -1:
				PetMapInfoList.append(PetMapInfo)
		return PetMapInfoList

	def DelPetNum(self, position, PetType):
		for PetMapInfo in self.PetMapInfoList:
			if PetMapInfo['position'] == position:
				for PetXYZ in PetMapInfo['PetXYZList']:
					if PetXYZ['PetType'] == PetType:
						if PetXYZ['PetNum'] > 0:
							PetXYZ['PetNum'] -= 1
							return True
		return False

	def UpdatePetMapConfig(self):
		sql = "select * from tbl_Hall_PetMapConfigList; "
		KBEngine.executeRawDatabaseCommand(sql, Functor.Functor(self.sqlcallback))
		
	def sqlcallback(self, result, rows, insertid, error):
		if result is None:
			return
		#定时更新地图配置
		self.UpdateMapConfig(result)
		#根据地图配置删除宠物信息
		self.DelPetMapInfo()

	def UpdateMapConfig(self,result):
		self.PetMapConfigList = []
		Element = {}
		for ConfigInfo in result:
			Element['cityName'] = bytes.decode(ConfigInfo[3])
			Element['position'] = bytes.decode(ConfigInfo[4])
			Element['location'] = bytes.decode(ConfigInfo[5])
			Element['radius'] = bytes.decode(ConfigInfo[6])
			Element['Scycle'] = bytes.decode(ConfigInfo[7])
			Element['Ecycle'] = bytes.decode(ConfigInfo[8])
			Element['Stime'] = bytes.decode(ConfigInfo[9])
			Element['Etime'] = bytes.decode(ConfigInfo[10])
			Element['frequence'] = bytes.decode(ConfigInfo[11])
			Element['gen_min'] = bytes.decode(ConfigInfo[12])
			Element['gen_max'] = bytes.decode(ConfigInfo[13])
			Element['gen_id'] = bytes.decode(ConfigInfo[14])
			Element['spe_min'] = bytes.decode(ConfigInfo[15])
			Element['spe_max'] = bytes.decode(ConfigInfo[16])
			Element['spe_id'] = bytes.decode(ConfigInfo[17])
			Element['spe_prob'] = bytes.decode(ConfigInfo[18])
			Element['spe_prob_list'] = bytes.decode(ConfigInfo[19])
			Element['enable'] = bytes.decode(ConfigInfo[20])
			self.PetMapConfigList.append(Element)

	def DelPetMapInfo(self):
		for index,PetMapInfo in enumerate(self.PetMapInfoList):
			IsFind = False
			for PetMapConfig in self.PetMapConfigList:
				if PetMapInfo['position'] == PetMapConfig['position']:
					IsFind = True
					break
			if not IsFind:
				del self.PetMapInfoList[index]
	
	def CreatePetMapInfo(self):
		for PetMapConfig in self.PetMapConfigList:
			self.CreatePetMap(PetMapConfig)
		
	def CreatePetMap(self, PetMapConfig):
		PetMapInfo = self.FindPetMap(PetMapConfig['position'])
		if PetMapInfo is None:
			PetMapInfo = {'cityName':PetMapConfig['cityName'],'position':PetMapConfig['position'],
						'radius':int(PetMapConfig['radius']),'refreshEndTime':0}
			res = self.BuildPetMap(PetMapConfig, PetMapInfo)
			if res == 0:
				self.PetMapInfoList.append(PetMapInfo)
		else:
			self.BuildPetMap(PetMapConfig, PetMapInfo)

	def DelPetMap(self, PetMapConfig):
		res = self.CheckTime(PetMapConfig)
		if res == -3 or res == -4:
			self.DelPetMap2(PetMapConfig['position'])
		return res

	def DelPetMap2(self,position):	
		for index, PetMapInfo in enumerate(self.PetMapInfoList):
			if PetMapInfo['position'] == position:
				del self.PetMapInfoList[index]
				return True
		return False

	def CheckTime(self, PetMapConfig):
		NowTime = time.time()
		date = datetime.datetime.fromtimestamp(NowTime)
		if date.hour < int(PetMapConfig['Stime']):
			return -1
		if date.hour > int(PetMapConfig['Etime']):
			return -2
		Scycle = int(PetMapConfig['Scycle'])
		if Scycle != 0 and int(NowTime) < Scycle:
			return -3
		Ecycle = int(PetMapConfig['Ecycle'])
		if Ecycle != 0 and int(NowTime) > Ecycle:
			return -4
		return 0

	def BuildPetMap(self, PetMapConfig, PetMapInfo):
		if int(PetMapConfig['enable']) == 0:
			self.DelPetMap2(PetMapInfo['position'])
			#INFO_MSG("disenable del PetMapInfoList :%s " % PetMapConfig['location'])
			return -1
		#删除过期的数据
		res = self.DelPetMap(PetMapConfig)
		if res != 0:
			INFO_MSG("DelPetMap, location:%s, res:%d" % (PetMapConfig['location'], res) )
			return -2
		#是否可以刷新数据
		nowTime = int(time.time())
		refreshEndTime = int(PetMapInfo['refreshEndTime'])
		if  refreshEndTime != 0 and nowTime < refreshEndTime:
			#DEBUG_MSG("check refreshEndTime, nowTime:%d, refreshEndTime:%s" % (nowTime, refreshEndTime) )
			return -3
		#清空
		PetMapInfo['PetXYZList'] = []
		#刷新数据
		if PetMapConfig['gen_id'] != "":
			GenIDList = PetMapConfig['gen_id'].split(",")
			PetTotalNum = random.randint(int(PetMapConfig['gen_min']),int(PetMapConfig['gen_max']) )
			RandPetXYZ(PetMapInfo['PetXYZList'],GenIDList,PetTotalNum)
		if PetMapConfig['spe_id'] != "" and IsProbability(int(PetMapConfig['spe_prob']) )[0]:
			SpeIDList = PetMapConfig['spe_id'].split(",")
			SpeProbList = PetMapConfig['spe_prob_list'].split(",")
			PetTotalNum = random.randint(int(PetMapConfig['spe_min']),int(PetMapConfig['spe_max']) )
			RandPetXYZ(PetMapInfo['PetXYZList'],SpeIDList,PetTotalNum,SpeProbList)
		PetMapInfo['refreshEndTime'] = nowTime + int(PetMapConfig['frequence'])*60
		INFO_MSG("BuildPetMap success:%s" % str(PetMapInfo))
		return 0
			
	def FindPetMap(self, position):
		for PetMapInfo in self.PetMapInfoList:
			if PetMapInfo['position'] == position:
				return PetMapInfo
		return None

	

