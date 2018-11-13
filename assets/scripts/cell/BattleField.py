# -*- coding: utf-8 -*-
import KBEngine
import d_card_dis
import random
import re
from KBEDebug import *
from array import *


class BattleField(KBEngine.Entity):
	def __init__(self):
		KBEngine.Entity.__init__(self)

		KBEngine.globalData["space_%i" % self.spaceID] = self.base

		self.entityList = []
		self.onPlaying = True

		DEBUG_MSG("BattleField.cell::init")

		self.startSituation = 0
		self.situation = 0

		self.CurrentPlayer = 0	
		self.Round = 0	
		self.FollowerID = 0
	
		self.EnvironmentProperty = {}
		self.EnvironmentProperty['SpellPlus'] = []
		self.EnvironmentProperty['FindPlus'] = []

		self.chooseCardStore = {}
		self.onDoingEvent = ''
		self.FindStore = {}

		self.afterTime = 0
		self.roundTime = 60

		self.TimerID = 0
		self.onlineCheckTimeID = 0
		self.outlineTimes = [0,0]
		self.readyList = [0,0]

		DEBUG_MSG("battle cell init OK TimerID:%i" % (self.TimerID))

		self.onGetAttTargetOpreateList = []
		self.beforeCauseHealOpreateList = []



	def initBattle(self,avatarList):#游戏开始入口
		self.avatarList = avatarList
		self.onlineCheckTimeID = self.addTimer(10, 3, 5)#ONLINE CHECK
		self.addTimer(5,0,6)#卡组获取

	def reqCardList(self):
		DEBUG_MSG('battleFiled:%s reqCardList'%self.id)
		for i in range(2):
			self.avatarList[i].reqCardList(self)

	def onReqCardList(self,cardEntityList,playerID):
		DEBUG_MSG('battleFiled:%s onReqCardList playerID:%s'%(self.id,playerID))
		self.cardEntityList[playerID] = cardEntityList

	def onBeginCardChoose(self,playerID):
		self.readyList[playerID] = 1
		if self.readyList == [1,1]:
			self.startFirstRound()
			self.readyList = [0,0]
		

	def onlineCheck(self):
		for i in range(2):
			if self.avatarList[i] != None and not self.avatarList[i].isDestroyed:
				self.outlineTimes[i] = 0
			else:
				self.outlineTimes[i] += 1
				if self.outlineTimes[i] > 5:
					self.MsgToClient_Battle('您的对手已经被你吓的掉线了，您已经获胜',self.another(i))
					self.EndBattle(self.another(i))

	def nextRound(self):
		self.Round += 1
		self.CurrentPlayer = (self.Round + 1)%2
		self.afterTime = 0
		self.avatarList[self.CurrentPlayer].setSituation(1)
		self.avatarList[self.another(self.CurrentPlayer)].setSituation(0)

	def startFirstRound(self):
		self.giveCard(0,20000002)
		self.addTimer(0,1,10)
		self.nextRound()

	def TimeTick(self):
		self.afterTime += 1
		if self.afterTime > self.roundTime:
			self.afterTime = 0
			self.endRound()

		for avatar in self.avatarList:
			if avatar is not None and not avatar.isDestroyed:
				avatar.afterTime = self.afterTime

	def endRound(self):
		DEBUG_MSG("battlefiled endRound")
		for avatar in self.avatarList:
			avatar.endRound()
		self.nextRound()

	def reqEndRound(self):
		self.afterTime = 0
		self.endRound()
		
	def giveCard(self,playerID,_cardID):#新版本
		cardID = int(_cardID)
		DEBUG_MSG("giveCard  playerID:[%s]  cardID:[%s]" % (playerID,_cardID))
		self.avatarList[playerID].creatHandCard(cardID)	

	def giveCardFromKZ(self,playerID,_cardID):
		cardID = int(_cardID)
		DEBUG_MSG("giveCardFromKZ  playerID:[%s]  cardID:[%s]" % (playerID,_cardID))
		self.avatarList[playerID].getCardFromKZ(cardID)

	def getCard(self,_playerID,sum=1):
		playerID = int(_playerID)
		self.avatarList[playerID].getCard(sum)

	def MsgToClient_Battle(self,msg,playerID):
		self.avatarList[playerID].msg(msg)


	def reqGiveUp(self,playerID):
		if not self.onPlaying:
			return
		self.onPlaying = False

		DEBUG_MSG("GiveUp playerID:[%i] BattleField:[%i]" % (playerID,self.id))
		if playerID == 1:
			successPlayerID = 0
		else:
			successPlayerID = 1
		self.EndBattle(successPlayerID)		

	def EndBattle(self,successPlayerID):
		DEBUG_MSG("EndBattle   BattleField:[%i]" % (self.id))
		self.delTimer(self.onlineCheckTimeID)
		for i in range(2):
			if self.avatarList[i] != None and not self.avatarList[i].isDestroyed:
				self.avatarList[i].battleEnd(i==successPlayerID)
		self.base.EndBattle(successPlayerID)


	def another(self,playerID):
		if str(playerID) == '0':
			return 1
		if str(playerID) == '1':
			return 0

	def posIsActive(self,pos):
		return pos != "KZ" and pos != "DEAD" and pos != "USED" and pos != 'HAND'

	#--------------------------------------------------------------------------------------------
	#                              EventProcess
	#--------------------------------------------------------------------------------------------

	def onPosChange(self,srcID):
		for entity in self.entityList:
			pos = entity.pos
			if self.posIsActive(pos):
				entity.onPosChange(srcID)

	def onEntityRecvHeal(self,srcID,targetID,healSum):
		for entity in self.entityList:
			pos = entity.pos
			if self.posIsActive(pos):
				entity.onEntityRecvHeal(srcID,targetID,healSum)

	def onSummonFollower(self,followerID):
		for entity in self.entityList:
			pos = entity.pos
			if self.posIsActive(pos):
				entity.onSummonFollower(followerID)

	def onUseCard(self,playerID,cardEntityID,cardID):
		for entity in self.entityList:
			pos = entity.pos
			if self.posIsActive(pos):
				entity.onUseCard(playerID,cardEntityID,cardID)

	def onFollowerDie(self,followerEntity):
		for entity in self.entityList:
			pos = entity.pos
			if self.posIsActive(pos):
				entity.onFollowerDie(followerEntity)


	#--------------------------------------------------------------------------------------------
	#                              Callbacks
	#--------------------------------------------------------------------------------------------
	def onDestroy(self):
		"""
		KBEngine method.
		"""
		del KBEngine.globalData["space_%i" % self.spaceID]
		self.destroySpace()
		
	def onEnter(self, entityMailbox):
		"""
		defined method.
		进入场景
		"""
		DEBUG_MSG('Space::onEnter space[%d] entityID = %i.' % (self.spaceUType, entityMailbox.id))
		
	def onLeave(self, entityID):
		"""
		defined method.
		离开场景
		"""
		DEBUG_MSG('Space::onLeave space[%d] entityID = %i.' % (self.spaceUType, entityID))

	def onTimer(self, id, userArg):
		#2	回合计时用的
		#5	检查双方是否仍在线

		if userArg == 2:
			self.EndRound()

		elif userArg == 3:#第一回合 留给客户端反应
			self.startFirstRound()

		elif userArg == 4:
			self.endCardChooseAndStartNewRound()

		elif userArg == 5:
			self.onlineCheck()

		elif userArg == 6:
			self.reqCardList()

		elif userArg == 10:
			self.TimeTick()


	#--------------------------------------------------------------------------------------------
	#                              Callbacks With Return
	#--------------------------------------------------------------------------------------------

	def onGetAttTarget(self,source,target):
		targetStore = target
		for i in range(len((self.onGetAttTargetOpreateList))):
			target = self.onGetAttTargetOpreateList[i].onGetAttTarget(source,target)
		if targetStore != target:
			DEBUG_MSG('BF::onGetAttTarget OldTarget[%s] newTarget[%s] source:[%s].' % (targetStore,target,source))
		return target

	def beforeCauseHeal(self,source,target,healSum):
		for i in range(len(self.beforeCauseHealOpreateList)):
			thLS  = self.beforeCauseHealOpreateList[i].beforeCauseHeal(source,target,healSum)
			target = thLS[0]
			healSum = thLS[1]
		return [target,healSum]
			

			
			

			

		