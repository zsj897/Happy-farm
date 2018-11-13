# -*- coding: utf-8 -*-		self.
import KBEngine
from KBEDebug import *
import d_card_dis
import random
import copy

class skillBase():
	def __init__(self):
		pass

	#--------------------------------------------------------------------------------------------
	#                              Callbacks
	#--------------------------------------------------------------------------------------------
	def onFollowerDie(self,followerEntity):
		pass

	def onRoundStart(self,isSelf):
		pass

	def onRoundEnd(self,isSelf):
		pass

	def choose0(self,targetID,needPos):
		pass

	def choose1(self,targetID,needPos):
		pass

	def choose2(self,targetID,needPos):
		pass

	def chooseStrLs(self):
		return []

	def battleCry(self,targetID,selfPos):
		pass

	def onUse(self,targetID,selfPos):
		self.battleCry(targetID,selfPos)

	def onDead(self):
		pass

	def onHeroUseSkill(self,isSelf):
		pass

	def onEntityRecvHeal(self,srcID,targetID,healSum):
		pass

	def onBeDamaged(self,srcID,sum):
		pass

	def onUseSkillCard(self,isSelf,cardID):
		pass

	def onUseCard(self,playerID,cardEntityID,cardID):
		pass

	def onUseFollowerCard(self,isSelf,cardID):
		pass

	def onBeAtted(self,srcID):
		pass

	def onAtt(self,targetID):
		pass

	def onCauseDamage(self,targetID,damage):
		pass

	def onCauseDamageA(self,targetID,damage):
		pass

	def onAddFollower(self,targetID):
		pass

	def onEnvirBuff(self,target):
		pass

	def envBuffConditon(self,target):
		return False

	def onKillFollower(self,targetID):
		pass

	def onAddBuff(self):
		pass

	def onSummonFollower(self,followerEntityID):
		pass

	def onGetWeapon(self,weaponEntityID):
		pass

	def onLoseWeapon(self,weaponEntityID):
		pass

	def onGetAttTarget(self,source,target):
		return target

	def beforeCauseHeal(self,source,target,healSum):
		return [target,healSum]

	# --------------------------------------------------------------------------------------------
	#                              buffEffent
	# --------------------------------------------------------------------------------------------
	def onRoundStartB(v,self,isSelf):
		pass

	def onBeforeRecvDamageB(v,self,damage,srcID,targetID):
		return damage

	def useSuccess(self,targetID = 0,needPos = 0):
		return ''
	#--------------------------------------------------------------------------------------------
	#                              BaseMeathod
	#--------------------------------------------------------------------------------------------
















