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

		DEBUG_MSG("battle filed base init ok::Battle March Successed player0:%i player1:%i" % (self.player0.id,self.player1.id))
		
		self.MsgToClient_March("成功匹配到对手 正在检测对手游戏状态是否正常")

		self.avatarList = [None,None]
		self.player = [self.player0,self.player1]

		self.currentProcess = 0 # 0 刚开始 1 base实体存在确认完成 2 Avatar创建完成
		'''
		状态	描述
		0		发送检查语句到account
		1		创建战场CELL
		2		战场Cell创建成功 通知account创建Avatar
		3		开始正式战斗
        4       战斗结算
		'''
		self.AccountReadyList = [0,0]

		self.addTimer(1, 0, 1)


	def Process(self):
		DEBUG_MSG('BattleFiled Process  BFID:{%s]  currentProcess:[%s]'%(self.id,self.currentProcess))
		if self.currentProcess == 0:
			self.player0.OnEnterBattelField(self,0)
			self.player1.OnEnterBattelField(self,1)
			self.nextTimeID = self.addTimer(1,0,1)
		elif self.currentProcess == 1:
			if self.AllReady():
				self.CreatCellBattlefiled()
			else:
				self.BattleFailed()
		elif self.currentProcess == 2:
			self.player0.creatAvatar(self)
			self.player1.creatAvatar(self)
			self.nextTimeID = self.addTimer(10,0,2)#10秒没成功直接进入失败操作
		elif self.currentProcess == 3:
			self.delTimer(self.nextTimeID)
			self.cell.initBattle(self.avatarList)
			
		self.currentProcess += 1		
			


	def AccountReady(self,playerID):
		DEBUG_MSG('AccountReady playerID:[%s]'%playerID)
		if self.AccountReadyList[int(playerID)] == 1:
			WARNING_MSG("AccountReady.accont registe repeatly BFid:[%s] playerID:[%s]"%(self.id,playerID))
		self.AccountReadyList[int(playerID)] = 1
		if self.AccountReadyList == [1,1]:
			if self.currentProcess == 3:
				self.Process()

	def AvatarRegiste(self,playerID,avatarCellMailBox):
		DEBUG_MSG('AvatarRegiste playerID:[%s]  avatar:%s'%(playerID,avatarCellMailBox.id))

		self.avatarList[int(playerID)] = avatarCellMailBox
		self.AccountReady(playerID)

	def AllReady(self):
		if self.AccountReadyList[0] == 1 and self.AccountReadyList[1] == 1:
			self.AccountReadyList = [0,0]
			return True
		else:
			return False
				

	def startBattle(self):	
		if self.AccountReadyList[0] == 0 or self.AccountReadyList[1] == 0 :
			DEBUG_MSG("a player is disconnected And Init Battle Fail  list:[%s]"%str(self.AccountReadyList))
			self.MsgToClient_March("你的对手不知道在那干啥呢，正在为您重新匹配")
			self.BattleFailed()
			return
		
		self.MsgToClient_March("匹配成功 正在初始化战场")

		self.player0.onInitBattleField(self.Hero[0])
		self.player1.onInitBattleField(self.Hero[1])

	
	def CreatCellBattlefiled(self):
		self.MsgToClient_March("正在前往：战场")
		#self.createInNewSpace(None)
		self.createCellEntityInNewSpace(None)

	def onCreateCellFailure(self):
		WARNING_MSG("creat cell fail. BFid:[%s]"%self.id)
		self.MsgToClient_March("战场前往失败，正在重新匹配")
		self.BattleFailed()

	def onGetCell(self):
		DEBUG_MSG('cell has been created')
		self.Process()

	
	def BattleFailed(self):
		DEBUG_MSG("BattleFailed BattleField currentProcessID:[%s] BFid:[%s]"%(self.currentProcess,self.id))
		self.addTimer(1,1,2)

		if self.cell is not None:
			self.destroyCellEntity()
			return
		self.player0.BattleFailed()
		self.player1.BattleFailed()
		self.destroy()
		

	def anotherPlayer(self,_playerID):
		playerID = int(_playerID)
		if playerID == 1:
			return 0
		elif playerID == 0:
			return 1
		else:
			DEBUG_MSG('error playerID wrong ID:[%s] type:[%s]'%(playerID,type(playerID)))
			return -1

	def MsgToClient_March(self,msg):
		self.player0.OnClientMsg_March(msg)
		self.player1.OnClientMsg_March(msg)

	def EndBattle(self,successPlayerID):
		DEBUG_MSG("EndBattle successPlayerID:[%i]  BattleField:[%i]" % (self.player[successPlayerID].id,self.id))
		if successPlayerID == 0:
			self.player0.BattleEndResult(1)
			self.player1.BattleEndResult(0)
		else:
			self.player0.BattleEndResult(0)
			self.player1.BattleEndResult(1)
		self.addTimer(2,1,3)


	def onDestroyTime(self):
		DEBUG_MSG("battlefiled::onDestroyTimer: %i" % (self.id))
		if self.cell is not None:
			# 销毁cell实体
			self.destroyCellEntity()
			return
		self.destroy()

	

	#----------------------------------------------------------
	#					callBack								
	#----------------------------------------------------------


	def onTimer(self, id, userArg):
	
		DEBUG_MSG(id, userArg)

		if userArg == 1:
			self.Process()
		elif userArg == 2:
			self.BattleFailed()
		elif userArg == 3:
			self.onDestroyTime()


