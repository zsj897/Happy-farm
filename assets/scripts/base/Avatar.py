# -*- coding: utf-8 -*-
import KBEngine
import random
import time
from KBEDebug import *

class Avatar(KBEngine.Proxy):
	"""
	角色实体
	"""
	def __init__(self):
		KBEngine.Proxy.__init__(self)

		self.nameB = self.cellData["nameA"]
		DEBUG_MSG('Avatar.base::__init__: [%i]' % self.id)
		self.cellData['position'] = [0,0,0]
		self.bf = self.cellData['battlefiled']
		self.cellData['playerID'] = self.playerIDB
		

	def onClientInit(self):
		INFO_MSG("Avatar[%i-%s] onClientInit., mailbox:%s" % (self.id, self.nameB, self.client))
		self.createCellEntity(self.cellData['battlefiled'].cell)
 
	def avatarRegiste(self):
		self.bf.AvatarRegiste(self.playerIDB,self.cell)

	def BattleFailed(self):
		self.addTimer(1, 2, 1)

	def BattleEnd(self):
		self.destroySelf()
		self.addTimer(1,1,1)

		
	def createCell(self, space):
		"""
		defined method.
		创建cell实体
		"""
		self.createCellEntity(space)
	
	def destroySelf(self):
		"""
		"""
		# 如果帐号ENTITY存在 移交控制器
		if self.client is not None:
			if self.account != None:
				DEBUG_MSG("Avatar::onDestroyTimer: %i  giveClientToAccount" % (self.id))
				self.giveClientTo(self.account)
				self.account.onGetClient()
				return
			
		if self.cell is not None and not self.isDestroyed:
			# 销毁cell实体
			DEBUG_MSG("Avatar::onDestroyTimer: %i  destroyCellEntity" % (self.id))
			self.destroyCellEntity()
			return
				
		# 销毁base
		self.destroy()

	#--------------------------------------------------------------------------------------------
	#                              Callbacks
	#--------------------------------------------------------------------------------------------
	def onTimer(self, tid, userArg):
		"""
		KBEngine method.
		引擎回调timer触发
		"""
		#DEBUG_MSG("%s::onTimer: %i, tid:%i, arg:%i" % (self.getScriptName(), self.id, tid, userArg))
		if 1 == userArg:
			self.onDestroyTimer()

	def onGetCell(self):
		"""
		KBEngine method.
		entity的cell部分实体被创建成功
		"""
		DEBUG_MSG('Avatar::onGetCell: %s' % self.cell)


		
	def onClientDeath(self):
		"""
		KBEngine method.
		entity丢失了客户端实体
		"""
		DEBUG_MSG("Avatar[%i].onClientDeath:" % self.id)
		# 防止正在请求创建cell的同时客户端断开了， 我们延时一段时间来执行销毁cell直到销毁base
		# 这段时间内客户端短连接登录则会激活entity
		self._destroyTimer = self.addTimer(1, 1, 1)
		self.account.onClientDeath()
			
	def onClientGetCell(self):
		"""
		KBEngine method.
		客户端已经获得了cell部分实体的相关数据
		"""
		DEBUG_MSG("Avatar[%i].onClientGetCell:%s" % (self.id, self.client))
		self.avatarRegiste()

	def onDestroyTimer(self):
		DEBUG_MSG("Avatar(BASE)::onDestroyTimer: %i" % (self.id))
		self.destroySelf()



