# -*- coding: utf-8 -*-
import KBEngine
from KBEDebug import *
import d_card_dis
import random
import copy
from interfaces.Spell import Spell
from interfaces.Buff import Buff

class cardBase(KBEngine.Entity,Spell):
	def __init__(self):
		KBEngine.Entity.__init__(self)	
		'''
		self.pos
		HAND		手牌
		KZ			卡组中
		0-6			场上1-7号
		HERO		英雄
		WEAPON		武器
		SKILL		技能
		DEAD		死过的卡（随从）
		USED		用过的卡（法术）
		SECRRET		奥秘
		BUFF        BUFF环境buff分发牌
		'''		
		if self.cardID != 0:
			self.initProperty()



		

	def initAvatar(self,cardID,pos,battlefiled):
		DEBUG_MSG("GameObj::initAvatar:id:[%i].BFid:[%s] cardID:[%s]  pos:[%s]" % (self.id,battlefiled,cardID,pos))

		self.cardID = cardID
		self.pos = pos
		self.battlefiled = battlefiled
		self.avatar = self
		self.avatarID = self.id

		self.initProperty()

	def initSpell(self,cardID):
		try:
			Spell.__init__(self,cardID)
		except IOError:
			pass


	def getBattleFiled(self,battlefiled):
		DEBUG_MSG("Avatar::getBattleFiled: %i. BF:%s" % (self.id,battlefiled))
		self.battlefiled = battlefiled

	def initProperty(self):
		cardID = self.cardID

		self.cost = d_card_dis.datas[cardID]["cost"]
		self.att = d_card_dis.datas[cardID]["att"]
		self.HP = d_card_dis.datas[cardID]["HP"]
		self.maxHP = d_card_dis.datas[cardID]["HP"]
		effectBool = d_card_dis.datas[cardID]["effectBool"]
		self.isTaunt = int( effectBool[0:1])
		self.isRush = int(effectBool[1:2])
		self.isWindfury = int( effectBool[2:3])
		self.isDivineShield = int( effectBool[3:4])
		self.isAbledForever = int(effectBool[4:5])
		if self.isAbled == 0:
			self.isAbled = int(effectBool[1:2])
		self.isStealth = int( effectBool[5:6])
		self.frozen = 0
		self.immune = 0
		self.race = d_card_dis.datas[cardID].get('race','')
		self.envBuff = d_card_dis.datas[cardID].get('envBuff',0)

		self.attSum = 0
		self.type = d_card_dis.datas[cardID]["type"]
		self.poison = d_card_dis.datas[cardID]["poison"]
		self.suckBlood = d_card_dis.datas[cardID]["suckBlood"]

		self.buffList = []
		self.sendBuffList = []

		self.chooseDataStore = {
			'targetID': 0,
			'needPos': 0,
			'active': False
		}

		self.initSpell(cardID)

		DEBUG_MSG("GameObj::initProperty:[%i]. BF:[%s]  cardID:[%s]  cost:[%s]  isAbled:[%s]" % (self.id,self.battlefiled,self.cardID,self.cost,self.isAbled))

	def reInitAttAndMaxHP(self):
		'''

		:return:
		'''
		self.att = d_card_dis.datas[self.cardID]["att"]
		self.maxHP = d_card_dis.datas[self.cardID]["HP"]
		self.cost = d_card_dis.datas[self.cardID]["cost"]
		if self == self.avatar:
			self.spellPower = 0

	def addBuff(self, buffEntity):
		"""
		defined method.
		添加buff
		"""
		self.buffList.append(buffEntity)
		self.updateBuffPropertyEffect()

	def removeBuff(self, buffEntity):
		"""
		defined method.
		删除buff
		"""
		self.buffList.remove(buffEntity)
		self.updateBuffPropertyEffect()

	def updateBuffPropertyEffect(self):
		'''
		仅处理属性相关的buff效果
		:return:无
		'''
		self.reInitAttAndMaxHP()
		for buff in self.buffList:
			if buff.envir != 1:
				buff.onAddDefaultProcess()
		for buff in self.buffList:
			if buff.envir == 1:
				buff.onAddDefaultProcess()

		if self.HP > self.maxHP:
			self.HP = self.maxHP

		if self.HP <= 0:
			self.die()



	def recvDamage(self,srcID,damage):

		if damage < 1:
			return

		if self.HP <= 0:
			return

		#buff预处理模块，比如战斗怒吼1血不死
		for buff in self.buffList:
			damage = buff.onBeforeRecvDamage(damage,srcID,self.id)

		oriDamage = damage

		if self.armor > 0:
			if self.armor >= damage:
				self.armor -= damage
				damage = 0
			else:
				damage -= self.armor
				self.armor = 0

		self.HP -= damage

		self.onBeDamaged(srcID,oriDamage)
		self.getEntityByID(srcID).onCauseDamage(self.id,oriDamage)
		if self.HP <= 0:
			self.getEntityByID(srcID).onKillFollower(self.id)
			self.die()

	def randomCauseDamageToOppo(self,damage,hasAvatar = True):
		if self.type == 1:
			damage += self.avatar.spellPower
		for i in range(damage):
			srcID = self.id
			target = random.choice(self.getOppoFollowerAndHeroList(hasAvatar))
			target.recvDamage(srcID, 1)

	def causeDamage(self,targetID,damage):
		DEBUG_MSG("GameObj[%i]::causeDamage:.  targetID:[%s]  damage[%s]" % (self.id, targetID, damage))
		if self.type == 1:
			damage += self.avatar.spellPower
		srcID = self.id
		#if self.pos == 'SKILL' or self.pos == 'WEAPON':
		#	srcID = self.avatarID
		if str(targetID).isdigit():
			target = self.getEntityByID(targetID)
			if target == None:
				return
		else:
			target = targetID
		self.allClients.onEvent(target.id,damage,"")
		target.recvDamage(srcID,damage)


	def causeDamages(self,targetList,damage):
		for target in targetList:
			self.causeDamage(target,damage)

	def recvHeal(self,srcID,HP):
		if HP == 0:
			return
		if HP < 0:
			self.recvDamage(srcID,-HP)
			return
		self.HP += HP
		if self.HP > self.maxHP:
			self.HP = self.maxHP
		self.battlefiled.onEntityRecvHeal(srcID,self.id,HP)

	def changePos(self,pos):
		DEBUG_MSG("GameObj::changePos:[%i].  oldPos:[%s]  newPos[%s]" % (self.id,self.pos,pos))
		loseWeapon = (self.pos == 'WEAPON' and pos != 'WEAPON')
		getWeapon = (self.pos != 'WEAPON' and pos == 'WEAPON')
		if pos == self.pos:
			return

		if pos == 'HAND':
			if len(self.avatar.getPosEntityList('HAND')) > 9:
				if self.type == 3:
					pos = 'DEAD'
				else:
					pos = 'USED'

		self.pos = pos

		if pos == 'SKILL':
			self.isAbled = 1



		for buff in self.buffList:
			buff.onTargetPosChange()
		self.battlefiled.onPosChange(self.id)

		if loseWeapon:
			self.avatar.onLoseWeapon(self.id)
		if getWeapon:
			self.avatar.onGetWeapon(self.id)
			
	def die(self):
		DEBUG_MSG("GameObj::die:[%i]. BF:[%s]" % (self.id,self.battlefiled))
		if self.pos == 'DEAD':
			return
		self.onDead()
		if self.pos.isdigit():
			self.avatar.followerDie(self.id)
		self.changePos('DEAD')
		for buff in self.buffList:
			self.removeBuff(buff)
		self.battlefiled.onFollowerDie(self)

	def reqUse(self,callerID,target):
		pass
	# def reqUse(self,callerID,target,needPos,afterChoose = False):
	# 	if not afterChoose:
	# 		#人出牌处理逻辑
	# 		DEBUG_MSG("GameObj::reqUse:[%i].  target:[%s]  needPos[%s]" % (self.id,target,needPos))
	# 		if callerID!=self.avatarID:
	# 			return

	# 		successInfor = self.useSuccess(target,needPos)

	# 		if successInfor == '':
	# 			pass
	# 		else:
	# 			self.clientMsg(successInfor)
	# 			return

	# 		if self.cost > self.avatar.CrystalAvaliable:
	# 			self.clientMsg("水晶不足 无法施放 当前水晶：%s  所需水晶：%s"%(self.avatar.CrystalAvaliable,self.cost))
	# 			return
	# 		else:
	# 			if len(self.avatar.followerList) > 6 and self.type == 3:
	# 				self.clientMsg("当前随从已经达到上限 无法继续召唤")
	# 				return

	# 		if len(self.chooseStrLs()) != 0:#如果需要抉择 如战争古树 进行处理
	# 			self.chooseDataStore['targetID'] = target
	# 			self.chooseDataStore['needPos'] = needPos
	# 			self.chooseDataStore['active'] = True
	# 			self.reqChoose()
	# 			return
	# 	else:
	# 		DEBUG_MSG("GameObj::reqUse:[%i].  enter to choose use" % (self.id))
	# 		target = self.chooseDataStore['targetID']
	# 		needPos = self.chooseDataStore['needPos']

	# 	self.avatar.uesCrystal(self.id,self.cost)

	# 	if self.pos == 'HAND':
	# 		if self.type == 3:#法术1奥秘2怪兽3武器4
	# 			self.avatar.followerPosAssigned(self.id,needPos)
	# 			self.isAbled = self.isRush
	# 			self.onUse(target,str(needPos))
	# 			self.battlefiled.onSummonFollower(self.id)
	# 		elif self.type == 4:
	# 			self.changePos('WEAPON')
	# 			self.onUse(target,'WEAPON')
	# 		elif self.type == 2:
	# 			self.changePos('SECRET')
	# 			self.onUse(target,'SECRET')
	# 		elif self.type == 1:
	# 			self.changePos('USED')
	# 			self.onUse(target,'SPELL')
	# 	elif self.pos == 'SKILL':
	# 		self.onUse(target,'SKILL')

	# 	self.battlefiled.onUseCard(self.playerID,self.id,self.cardID)
			


	def reqAtt(self,callerID,targetID):
		DEBUG_MSG("GameObj::reqAtt:[%i].  target:[%s]" % (self.id,targetID))
		#-----------检测攻击是否可行逻辑
		#-----------潜行逻辑未添加
		if callerID!=self.avatarID:
			return

		if not self.type == 3:
			return

		if not self.isFollowerOrHero():
			return

		targetEntity = KBEngine.entities.get(targetID,None)

		if targetEntity == None:
			return

		if not targetEntity.type == 3:
			return

		if not self.isFollowerOrHero(targetEntity):
			return

		if not self.canBeAtted(targetEntity):
			return

		if self.attSum > self.isWindfury:
			return
		#--------------攻击前修改
		entity = self.getEntityByID(targetID)
		target = self.battlefiled.onGetAttTarget(self,entity)
		if target == None:
			return
		targetID = target.id
		#--------------攻击逻辑
		self.onAtt(targetID)
		self.allClients.onAtt(targetID)
		targetEntity.recvAtt(self.id)
		self.attSum += 1
		self.updateisAbled()

	def createHandCard(self,cardID):
		self.avatar.creatHandCard(id)

	def updateisAbled(self):
		if self.attSum > self.isWindfury:
			self.isAbled = 0
		else:
			self.isAbled = 1


	def recvAtt(self,srcID):
		srcEntity = KBEngine.entities.get(srcID,None)
		damage = srcEntity.att
		self.recvDamage(srcID,damage)
		self.onBeAtted(srcID)
		srcEntity.recvDamage(self.id,self.att)

	def getDivineShield(self,srcID):
		self.isDivineShield = 1

	def getWindfury(self,srcID):
		self.isWindfury = 1

	def getTaunt(self,srcID):
		self.isTaunt = 1

	def getStealth(self,srcID):
		self.isStealth = 1

	def getRush(self,srcID):
		self.isRush = 1
		if self.attSum < 1+self.isWindfury:
			self.isAbled = 1

	def setImmune(self,srcID,immune = 1):
		self.immune = immune


	def canBeAtted(self,entity):
		if self.TargetIsTaunt(entity):
			return True
		else:
			if self.hasTaunt(entity.avatar):
				return False
			else:
				return True

	def isFollowerOrHero(self,entity = None):
		if entity == None:
			entity = self
		for i in range(7):
			if str(entity.pos) == str(i):
				return True
		if entity.pos == 'HERO':
			return True
		return False

	def hasTaunt(self,avatar):
		for entity in avatar.followerList:
			if entity == None:
				continue
			if entity.isTaunt == 1:
				return True
		if avatar.isTaunt == 1:
			return True
		return False

	def TargetIsTaunt(self,entity):
		if entity == None:
			return False
		return entity.isTaunt == 1

	def getEntityByID(self,ID):
		entity = KBEngine.entities.get(ID,None)	
		return entity

	def clientMsg(self,msg):
		entity = self.avatar
		entity.battleMsg(msg)

	def rush(self):
		self.isRush = 1
		if self.attSum < self.isWindfury +1:
			self.isAbled = 1

	def discard(self):
		DEBUG_MSG('GamObj:[%s] discard'%(self))
		self.changePos('USED')

	def delAllBuff(self):
		for buff in self.buffList:
			buff.delBuffDir()
		for buff in self.sendBuffList:
			buff.delBuffDir()

	def replaceEntity(self,targetID,targetCardID):
		self.avatar.replaceEntity(targetID,targetCardID)

	def changeController(self):
		oppoAvatar = self.getOppoAvatar()
		self.avatar.cardEntityList.remove(self)
		oppoAvatar.cardEntityList.append(self)
		if self in self.avatar.followerList:
			self.avatar.followerList.remove(self)
		oppoAvatar.followerList.append(self)
		oppoAvatar.followerPosReassigned()
		self.playerID = self.another(self.playerID)
	#--------------------------------------------------------------------------------------------
	#                              Callbacks
	#--------------------------------------------------------------------------------------------
	def onTimer(self, tid, userArg):
		"""
		KBEngine method.
		引擎回调timer触发
		"""
		#DEBUG_MSG("%s::onTimer: %i, tid:%i, arg:%i" % (self.getScriptName(), self.id, tid, userArg))

	def onRestore(self):
		"""
		KBEngine method.
		entity的cell部分实体被恢复成功
		"""
		
	def onDestroy(self):
		"""
		KBEngine method.
		当前entity马上将要被引擎销毁
		可以在此做一些销毁前的工作
		"""
		DEBUG_MSG("onDestroy(%i)" % self.id)

	def onBuffTick(self,situation):
		"""
		buff的tick
		此处可以轮询所有的buff，将需要执行的buff执行
		"""
		DEBUG_MSG("onBuffTick")

	def onRemoveBuff(self,buffEntity):
		self.removeBuff(buffEntity)

	def onRemoveSendBuff(self,buffEntity):
		self.sendBuffList.remove(buffEntity)

	def getArmor(self,armor):
		self.armor += armor

	def loseDurable(self,s = 1):
		if self.pos == 'WEAPON':
			self.HP -= s
			if self.HP <= 0:
				self.avatar.loseWeapon()
		else:
			WARNING_MSG("loseDurable but pos is [%s]"%self.pos)

	def onFollowerDie(self,followerEntity):
		pass


	#--------------------------------------------------------------------------------------------
	#                              Effect
	#--------------------------------------------------------------------------------------------
	def onRoundStart(self,isSelf):
		if self.isDestroyed:
			return
		self.attSum = 0
		if isSelf:
			if self.frozen > 0 and isSelf:
				self.frozen -= 1
			if self.isFollowerOrHero:
				self.isAbled = 1
				if self.pos == 'HERO':
					if self.att <= 0:
						self.isAbled = 0
					else:
						self.isAbled = 1
		else:
			self.isAbled = 0

		if self.avatarID == self.id:
			self.updateBuffPropertyEffect()

		for buff in self.buffList:
			buff.onRoundStart(isSelf)

		Spell.onRoundStart(self,isSelf)



	def onRoundEnd(self,isSelf):
		if self.isDestroyed:
			return
		self.isAbled = 0
		for buff in self.buffList:
			buff.onRoundEnd(isSelf)
		if 	self.chooseDataStore['active']:
			self.allClients.onEndChoose()
			self.chooseDataStore['active'] = False
		if self.avatarID == self.id:
			self.att = 0
		Spell.onRoundEnd(self,isSelf)

	def reqEndChoose(callerID,self):
		pass

	def reqChoose(self,callerID = 0,chooseID = -1):
		DEBUG_MSG("GameObj::reqChoose:[%i].  chooseID:[%s]" % (self.id, chooseID))
		if chooseID == -1:
			self.sendChoose(self.chooseStrLs())
		else:
			if chooseID == 0:
				self.choose0(self.chooseDataStore['targetID'],self.chooseDataStore['needPos'])
			elif chooseID == 1:
				self.choose1(self.chooseDataStore['targetID'],self.chooseDataStore['needPos'])
			elif chooseID == 2:
				self.choose2(self.chooseDataStore['targetID'],self.chooseDataStore['needPos'])
			self.reqUse(self.id,self.chooseDataStore['targetID'],self.chooseDataStore['needPos'],True)

	def onUse(self,targetID,selfPos):
		self.allClients.onUse(targetID)
		if self.envBuff == 1:
			self.addEnvirBuff()

		Spell.onUse(self,targetID,selfPos)

	def onDead(self):
		if self.envBuff == 1:
			self.delSendEnvBuff()

		Spell.onDead(self)

	def onAtt(self,targetID):
		if self.pos == 'HERO' and self.getSelfWeapon() != None:
			self.getSelfWeapon().onAtt(targetID)
		elif self.pos == 'WEAPON':
			self.loseDurable()

		Spell.onAtt(self,targetID)

	def onCauseDamage(self,targetID,damage):
		#from recvDamage()
		if self.poison == 1:
			entity = self.getEntityByID(targetID)
			if entity != None and entity.pos.isdigit():
				self.makeTargetDie(targetID)

		if self.suckBlood == 1:
			self.causeHeal(self.avatarID,damage)

		Spell.onCauseDamageA(self,targetID,damage)


	def onPosChange(self,targetID):
		if self.silent == 1:
			return
		entity = self.getEntityByID(targetID)
		if entity == None:
			return
		if self.envBuff == 1:
			self.envBuffJudge(entity)



	# --------------------------------------------------------------------------------------------
	#                              buffEffent
	# --------------------------------------------------------------------------------------------

	#--------------------------------------------------------------------------------------------
	#                              BaseMeathod
	#--------------------------------------------------------------------------------------------
	def sendChoose(self,stringLs):
		DEBUG_MSG("GameObj::sendChoose:[%i].  stringLs:[%s]" % (self.id, str(stringLs)))
		self.allClients.onChoose(stringLs)

	def posIsActive(self,pos):
		return pos != "KZ" and pos != "DEAD" and pos != "USED"

	def posIsInBattleFiled(self,pos):
		return pos == 'HERO' or str(pos).isdigit()

	def getSelfWeapon(self):
		for entity in self.avatar.cardEntityList:
			if entity.pos == 'WEAPON':
				return entity
		return None

	def causeHeal(self,targetID,s):
		if str(targetID).isdigit():
			target = self.getEntityByID(targetID)
		else:
			target = targetID
		if target != None:
			thLS = self.battlefiled.beforeCauseHeal(self,target,s)
			target = thLS[0]
			s = thLS[1]
			target.recvHeal(self.id,s)

	def sendDivineShield(self,targetID):
		target = self.getEntityByID(targetID)
		if target != None:
			target.getDivineShield(self.id)

	def sendWindfury(self,targetID):
		target = self.getEntityByID(targetID)
		if target != None:
			target.getWindfury(self.id)

	def sendTaunt(self,targetID):
		target = self.getEntityByID(targetID)
		if target != None:
			target.getTaunt(self.id)

	def sendRush(self,targetID):
		if str(targetID).isdigit():
			target = self.getEntityByID(targetID)
		else:
			target = targetID
		if target != None:
			target.getRush(self.id)


	def getAllEntity(self):
		ls = copy.deepcopy(self.battlefiled.entityList)
		DEBUG_MSG("GameObj[%i] getAllEntity lenofls:[%s]" % (self.id,len(ls)))
		return ls

	def delSendBuff(self):
		for buff in self.sendBuffList:
			if buff != None and not buff.isDestroyed:
				buff.remove()

	def delSendEnvBuff(self):
		for buff in self.sendBuffList:
			if buff != None and buff.envir == 1:
				buff.remove()

	def creatEnvirBuff(self,params,targetID = 0,buffType = 'buff0'):
		params['envir'] = 1
		self.creatBuff(params,targetID,buffType)

	def creatBuff(self,params,targetID = 0,buffType = 'buff0'):
		DEBUG_MSG("GameObj creatBuff type:[%s] params:[%s]" % (buffType,str(params)))
		if targetID != 0 and str(targetID).isdigit():
			target = self.getEntityByID(targetID)
			if target != None:
				params['targetEntity'] = target
		elif not str(targetID).isdigit():
			target = targetID
			params['targetEntity'] = target

		if params.get('targetEntity',None) == None:
			DEBUG_MSG("GameObj creatBuff type:[%s] params:[%s] targetGetFail" % (buffType, str(params)))
			return

		params['sourceCardID'] = self.cardID
		params['sourceEntityID'] = self.id
		params['sourceEntity'] = self


		#buff = KBEngine.createEntity(buffType, self.spaceID, tuple(self.position), tuple(self.direction), params)
		buff = Buff(params)

		if params.get('envir',0) == 1:
			self.sendBuffList.append(buff)

	def creatBuffs(self,params,targetList):
		for target in targetList:
			self.creatBuff(params,target)
		

	def addEnvirBuff(self,pos = ''):
		entityList = self.getAllEntity()
		sum0 = 0
		for entity in entityList:
			if pos == '' or entity.pos == pos:
				self.envBuffJudge(entity)
				sum0 += 1
		DEBUG_MSG("GameObj:[%s]:pos[%s]:addEnvirBuff addBuffSum:[%s]" % (self.id,self.pos,sum0))

	def getTargetBuff(self,target):
		for buff in self.sendBuffList:
			if buff.targetEntity == target:
				return buff
		return None

	def envBuffJudge(self,entity):
		buff = self.getTargetBuff(entity)
		if self.envBuffConditon(entity):
			if buff == None:
				self.onEnvirBuff(entity)
		else:
			if buff != None:
				buff.delBuff()
		DEBUG_MSG("GameObj:[%s]:[%s]:pos:[%s] envBuffJudge targetHasBuff:[%s]  envBuffConditon:[%s] targetID:[%s] targetCardID:[%s]:[%s]" % (self.id,self.cardID,self.pos,buff!=None,self.envBuffConditon(entity),entity.id,entity.cardID,entity.pos))

	def makeEntitySilent(self,target):
		target.silent = 1
		for buff in target.buffList:
			if buff.envir == 0:
				buff.delBuff()
		target.delSendBuff()
		target.isTaunt = 0
		target.isRush = 0
		target.isWindfury = 0
		target.isDivineShield = 0
		target.isAbledForever = 0
		target.isAbled = 0
		target.isStealth = 0
		target.frozen = 0

	def getOppoAvatar(self):
		playerID = self.playerID
		if playerID == 0:
			return self.battlefiled.avatarList[1]
		elif playerID == 1:
			return self.battlefiled.avatarList[0]
		else:
			ERROR_MSG('getOppoAvatarErr:playerID:'%playerID)

	def getRandomOppoFollowers(self,sum = 1):
		ls = copy.deepcopy(self.getOppoAvatar().followerList)
		if len(ls)<=sum:
			return ls
		else:
			return random.sample(ls,sum)

	def getFollowerAndHeroList(self, hasHero=True):
		ls = []
		heroSum = 0
		for entity in self.getAllEntity():
			if entity.pos == 'HERO' and hasHero:
				heroSum += 1
				ls.append(entity)
			if entity.pos.isdigit():
				ls.append(entity)
		DEBUG_MSG("GameObj[%i] getFollowerAndHeroList lenofls:[%s] heroSum:[%s] hasHero:[%s]" % (self.id,len(ls),heroSum,hasHero))
		return ls

	def getOppoFollowerAndHeroList(self, hasHero=True):
		ls = []
		for entity in self.getAllEntity():
			if entity.playerID != self.playerID:
				if entity.pos == 'HERO' and hasHero:
					ls.append(entity)
				if entity.pos.isdigit():
					ls.append(entity)
		return ls

	def getSelfFollowerAndHeroList(self, hasHero=True):
		ls = []
		for entity in self.getAllEntity():
			if entity.playerID == self.playerID:
				if entity.pos == 'HERO' and hasHero:
					ls.append(entity)
				if entity.pos.isdigit():
					ls.append(entity)
		return ls

	def makeTargetDie(self,targetID):
		target = self.getEntityByID(targetID)
		if target == None:
			return
		target.die()

	def causeDamageToAllOppo(self,damage,hasAvatar = True):
		ls = []
		if hasAvatar:
			ls.append(self.getOppoAvatar())
		for entity in self.getOppoAvatar().followerList:
			ls.append(entity)
		self.causeDamages(ls,damage)

	def frozenTarget(self,targetID):
		target = self.getEntityByID(targetID)
		if target == None:
			return
		target.frozen = 2

	def changeTargetController(self,targetID):
		target = self.getEntityByID(targetID)
		if target == None:
			return
		target.changeController()

	def another(self,ID):
		if ID == 0:
			return  1
		else:
			return  0

	def summorFollower(self,cardIDList,srcEntityID = 0,srcEntityPos = 0):
		DEBUG_MSG('GameObj:[%s]summorFollower::cardIDList:[%s]' % (self.id,str(cardIDList)))
		if self.pos.isdigit():
			self.avatar.summorFollower(cardIDList,self.id,self.pos)
		else:
			self.avatar.summorFollower(cardIDList, self.id, 9)

	def getCard(self,s = 1):
		self.avatar.getCard(s)

	def getWeapon(self,weaponID):
		self.avatar.getWeapon(weaponID)

	def getPosEntityList(self,pos):
		ls = []
		for entity in self.avatar.cardEntityList:
			if entity.pos == pos:
				ls.append(entity)
		if pos != 'KZ':
			DEBUG_MSG('GameObj:[%s]getPosEntityList::needPos:[%s] returnLs:len:[%s] ls:[%s]' % (self.id, pos,len(ls),str(ls)))
		return ls

	def getAllActiveSelfEntity(self):
		ls = []
		for entity in self.avatar.cardEntityList:
			if self.posIsActive(entity.pos):
				ls.append(entity)
		return ls


	def posIsActive(self, pos):
		return pos != "KZ" and pos != "DEAD" and pos != "USED" and pos != 'HAND'

	def getSelfHandCardList(self):
		ls = []
		for entity in self.avatar.cardEntityList:
			if entity.pos == 'HAND':
				ls.append(entity)
		return ls

	def changeController(self):
		if len(self.getOppoAvatar().followerList) >= 7:
			return
		self.avatar.cardEntityList.remove(self)
		if self in self.avatar.followerList:
			self.avatar.followerList.remove(self)
		self.avatar.followerPosReassigned()
		self.avatar = self.getOppoAvatar()
		self.avatarID = self.avatar.id
		self.playerID = self.avatar.playerID
		self.changePos('6')
		self.avatar.cardEntityList.append(self)
		self.avatar.followerList.append(self)
		self.avatar.followerPosReassigned()

	def hasPostion(self):
		return len(self.avatar.followerList) < 7











