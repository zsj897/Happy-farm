# -*- coding: utf-8 -*-
import KBEngine
import skills
from KBEDebug import * 


class Spell:
	def __init__(self,cardID):
		self.skill = skills.getSkill(cardID)

	def onFollowerDie(self,followerEntity):
		self.skill.onFollowerDie(self,followerEntity)

	def onRoundStart(self,isSelf):
		self.skill.onRoundStart(self,isSelf)

	def onRoundEnd(self,isSelf):
		self.skill.onRoundEnd(self,isSelf)

	def choose0(self,targetID,needPos):
		self.skill.choose0(self,targetID,needPos)

	def choose1(self,targetID,needPos):
		self.skill.choose1(self,targetID,needPos)

	def choose2(self,targetID,needPos):
		self.skill.choose2(self,targetID,needPos)

	def chooseStrLs(self):
		return self.skill.chooseStrLs(self)

	def battleCry(self,targetID,selfPos):
		self.skill.battleCry(self,targetID,selfPos)

	def onUse(self,targetID,selfPos):
		self.skill.onUse(self,targetID,selfPos)
		self.battleCry(targetID,selfPos)

	def onDead(self):
		self.skill.onDead(self)

	def onHeroUseSkill(self,isSelf):
		self.skill.onHeroUseSkill(self,isSelf)

	def onEntityRecvHeal(self,srcID,targetID,healSum):
		self.skill.onEntityRecvHeal(self,srcID,targetID,healSum)

	def onBeDamaged(self,srcID,sum):
		self.skill.onBeDamaged(self,srcID,sum)

	def onUseSkillCard(self,isSelf,cardID):
		self.skill.onUseSkillCard(self,isSelf,cardID)

	def onUseCard(self,playerID,cardEntityID,cardID):
		self.skill.onUseCard(self,playerID,cardEntityID,cardID)

	def onUseFollowerCard(self,isSelf,cardID):
		self.skill.onUseFollowerCard(self,isSelf,cardID)

	def onBeAtted(self,srcID):
		self.skill.onBeAtted(self,srcID)

	def onAtt(self,targetID):
		self.skill.onAtt(self,targetID)

	def onCauseDamage(self,targetID,damage):
		self.skill.onCauseDamage(self,targetID,damage)

	def onCauseDamageA(self,targetID,damage):
		self.skill.onCauseDamageA(self,targetID,damage)

	def onAddFollower(self,targetID):
		self.skill.onAddFollower(self,targetID)

	def onEnvirBuff(self,target):
		self.skill.onEnvirBuff(self,target)

	def envBuffConditon(self,target):
		return self.skill.envBuffConditon(self,target)

	def onKillFollower(self,targetID):
		self.skill.onKillFollower(self,targetID)

	def onAddBuff(self):
		self.skill.onAddBuff(self)

	def onSummonFollower(self,followerEntityID):
		self.skill.onSummonFollower(self,followerEntityID)

	def onGetWeapon(self,weaponEntityID):
		self.skill.onGetWeapon(self,weaponEntityID)

	def onLoseWeapon(self,weaponEntityID):
		self.skill.onLoseWeapon(self,weaponEntityID)

	def onGetAttTarget(self,source,target):
		return self.skill.onGetAttTarget(self,source,target)

	def beforeCauseHeal(self,source,target,healSum):
		return self.beforeCauseHeal(self,source,target,healSum)

	# --------------------------------------------------------------------------------------------
	#                              buffEffent
	# --------------------------------------------------------------------------------------------
	def onRoundStartB(v,self,isSelf):
		v.skill.onRoundStartB(v,self,isSelf)

	def onBeforeRecvDamageB(v,self,damage,srcID,targetID):
		return v.skill.onBeforeRecvDamageB(v,self,damage,srcID,targetID)

	def useSuccess(self,targetID = 0,needPos = 0):
		return self.skill.useSuccess(self,targetID = 0,needPos = 0)
