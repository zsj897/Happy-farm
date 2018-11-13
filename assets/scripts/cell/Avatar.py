# -*- coding: utf-8 -*-
import KBEngine
import random
from KBEDebug import *
from interfaces.cardBase import cardBase
import d_card_dis

class Avatar(cardBase):
	def __init__(self):
		DEBUG_MSG('Avatar.cell::__init__: [%i]  roleType:[%i]' % (self.id,self.roleType))
		cardBase.__init__(self)
		self.cardID = (20003000+self.roleType)
		
		self.addTimer(2,0,2)#初始化

		self.addTimer(1,2,5)#获取信息

		self.cardEntityList = []
		self.beChoosedEntityList = []
		self.tiredSum = 0

		self.startEntityCreat = False
		self.startHaveChooseCard = False
		self.onCreatCardEntityList = []
		self.followerList = []

		self.onPlaying = True

		self.uesCardSumInRound = 0
		self.uesCardSum = 0

		self.chooseCardData = {
			'TimeID':0,
			'EntityIDList':[],
			'recvEntity':None,
			'mode':0
		}
		'''
		self.situation
		0	对方操作状态
		1	己方操作状态
		'''


	def init(self):
		cardBase.initAvatar(self,self.cardID,'HERO',self.battlefiled)
		self.avatar = self


	def reqCardList(self,battlefiled):
		DEBUG_MSG("Avatar::reqCardList: %i. BF:%s" % (self.id,battlefiled.id))
		self.battlefiled = battlefiled

		self.battlefiled.entityList.append(self)
		DEBUG_MSG("Avatar[%i]::register to entityList: pos:[%s] [%s]" % (self.id,self.pos,(self in self.battlefiled.entityList)))

		self.battleMsg('开始创建游戏所需卡牌实体 请稍后')
		for id in self.cardList:
			self.creatCardEntity(id)
		#self.battlefiled.onReqCardList(self.playerID)
		skillID = (20001000 + self.roleType)
		self.creatCardEntity(skillID,'SKILL')

	def creatCardEntity(self,cardID,pos = 'KZ'):
		DEBUG_MSG('Avatar:[%s] add to will creat entityList cardID:[%s]'%(self.id,cardID))

		data = {}
		data['cardID'] = cardID
		data['pos'] = pos
		self.onCreatCardEntityList.append(data)

		if not self.startEntityCreat:
			self.addTimer(0.1,0.1,4)#实体创建计时器
			self.startEntityCreat = True

	def eventTrigger(self,event):
		pass

	def getCardWithCardID(self,cardID):
		if len(self.getPosEntityList('HAND')) < 10:
			self.creatHandCard(cardID)

	def creatHandCard(self,cardID):
		self.creatCardEntity(cardID,'HAND')

	def setSituation(self,situation):
		DEBUG_MSG('Avatar:[%s]setSituation::situation:[%s]'%(self.id,situation))
		self.situation = situation
		self.newRound(1==situation)

	def newRound(self,isSelf):
		if isSelf:
			if self.CrystalSum < 10:
				self.CrystalSum += 1
			self.CrystalAvaliable = self.CrystalSum
			self.uesCardSumInRound = 0
			self.getCard()
		for entity in self.cardEntityList:
			if self.posIsActive(entity.pos):
				entity.onRoundStart(isSelf)
		cardBase.onRoundStart(self,isSelf)


	def endRound(self):
		isSelf = (self.situation == 1)
		if self.chooseCardData['EntityIDList'] != []:
			self.NoCardBeChoosedProcess()
		for entity in self.cardEntityList:
			if self.posIsActive(entity.pos):
				entity.onRoundEnd(isSelf)
		cardBase.onRoundEnd(self,isSelf)

	def chooseCardWithCardID(self,cardIDList,recvEntity = None,mode = 1):
		entityIDList = []
		for cardID in cardIDList:
			if int(cardID) in d_card_dis.datas:
				params = {
					"cardID": cardID,
					"playerID": self.playerID,
					"battlefiled": self.battlefiled,
					'pos': 'N',
					'avatar': self,
					'avatarID': self.id
				}
				e = KBEngine.createEntity('card', self.spaceID, tuple(self.position), tuple(self.direction),params)
				entityIDList.append(e.id)
		self.chooseCardWithEntityID(entityIDList,recvEntity,mode)


	def chooseCardWithEntityID(self,EntityList,recvEntity = None,mode = 1):
		self.chooseCardData['TimeID'] = self.addTimer(30,0,1)
		self.chooseCardData['recvEntity'] = recvEntity
		self.chooseCardData['mode'] = mode
		DEBUG_MSG("Avatar::chooseCardWithEntityID: %i.  len of cardEntityList: %i" % (self.id, len(EntityList)))
		self.chooseCardData['EntityIDList'] = EntityList
		self.client.beginCardChoose(self.beChoosedEntityList,mode)



	def beginCardChoose(self):#初始时选择卡牌具体处理函数
		self.chooseCardData['TimeID'] = self.addTimer(30, 0, 1)#时间过长直接取消选择卡牌
		self.battleMsg('开始初始卡牌选择')
		self.ChooseCardCardSum = 3 + self.playerID
		kzls = self.getPosEntityList('KZ')
		DEBUG_MSG("Avatar::beginCardChoose: %i.  len of kzls: %i" %( self.id,len(kzls)))

		beChoosedEntityIndex = random.sample(range(len(kzls)),self.ChooseCardCardSum)

		self.beChoosedEntityList.clear()
		for index in beChoosedEntityIndex:
			self.chooseCardData['EntityIDList'].append(kzls[index].id)
		DEBUG_MSG("Avatar::beginCardChoose: %i.  be choosed entityIDs: %s" %( self.id,str(self.beChoosedEntityList)))
		self.client.beginCardChoose(self.chooseCardData['EntityIDList'],0)
		self.chooseCardData['mode'] = 0


	def onBeginChooseCard(self,callerID,cardEntityIDList):#用户自选处理
		DEBUG_MSG("Avatar::onBeginChooseCard: %i.  be choosed entityIDs: %s" %( self.id,str(cardEntityIDList)))
		if callerID!= self.id:
			return

		AllbeChoosedList = self.chooseCardData['EntityIDList']


		if AllbeChoosedList == []:
			return
		if self.chooseCardData['mode'] == 0:#多选多 目前仅用于开始卡牌替换
			beChoosedList = []

			for EntityID in cardEntityIDList:
				if EntityID == 0:
					continue
				beChoosedList.append(int(EntityID))

			self.ChooseCardCardSum = len(AllbeChoosedList)
			beChoosedCardSum = len(beChoosedList)

			for EntityID in beChoosedList:
				self.getCardFromKZ(EntityID)
			DEBUG_MSG("Avatar::onBeginChooseCard: %i.  completingCardSum: %s" %(self.id,self.ChooseCardCardSum - beChoosedCardSum))
			self.getCard(self.ChooseCardCardSum - beChoosedCardSum)
			self.battlefiled.onBeginCardChoose(self.playerID)

		elif self.chooseCardData['mode'] == 1:#多选1，目前用于发现、追踪术，选中卡牌进入手牌，非选中卡牌销毁
			beChoosedCard = 0
			if len(cardEntityIDList) > 1:
				ERROR_MSG("Avatar::onBeginChooseCard: %i.  More than need" % (self.id))
				beChoosedCard = cardEntityIDList[0]
			elif len(cardEntityIDList) == 1:
				beChoosedCard = cardEntityIDList[0]
			elif len(cardEntityIDList) == 0:
				beChoosedCard = random.choice(AllbeChoosedList)

			for entityID in AllbeChoosedList:
				entity = self.getEntityByID(entityID)
				if entity == None:
					continue
				if entityID == beChoosedCard:
					entity.changePos('HAND')
				else:
					if entity in self.cardEntityList:
						self.cardEntityList.remove(entity)
						self.battlefiled.entityList.remove(entity)
					entity.destroy()
		if 	self.chooseCardData['TimeID'] != 0:
			self.delTimer(self.chooseCardData['TimeID'])

		self.chooseCardData = {
			'TimeID': 0,
			'EntityIDList': [],
			'recvEntity': None,
			'mode': 0
		}



	def NoCardBeChoosedProcess(self):#用于回合结束还没OK的处理
		DEBUG_MSG("Avatar::beginCardChoose: %i.  NoCardBeChoosedProcess" %(self.id))
		AllbeChoosedList = self.chooseCardData['EntityIDList']
		
		if AllbeChoosedList == []:
			return

		if self.chooseCardData['mode'] == 0:#多选多 目前仅用于开始卡牌替换
			for EntityID in AllbeChoosedList:
				self.getCardFromKZ(EntityID)
		elif self.chooseCardData['mode'] == 1:  # 多选1，目前用于发现、追踪术，选中卡牌进入手牌，非选中卡牌销毁
			beChoosedCard = random.choice(AllbeChoosedList)

			for entityID in AllbeChoosedList:
				entity = self.getEntityByID(entityID)
				if entity == None:
					continue
				if entityID == beChoosedCard:
					entity.changePos('HAND')
				else:
					if entity in self.cardEntityList:
						self.cardEntityList.remove(entity)
						self.battlefiled.entityList.remove(entity)
					entity.destroy()

		self.chooseCardData = {
			'TimeID': 0,
			'EntityIDList': [],
			'recvEntity': None,
			'mode': 0
		}

		self.client.endChooseCard()
		if self.chooseCardData['mode'] == 0:
			self.battlefiled.onBeginCardChoose(self.playerID)
	

	def getCard(self,sum = 1):
		DEBUG_MSG("Avatar::getCard: %i.  SUM: %i" %(self.id,sum))
		if sum > 30:
			sum = 30
			DEBUG_MSG("Avatar::getCard: %i.  sum is more than 30" %(self.id))
		for i in range(sum):
			handCardList = self.getPosEntityList('KZ')
			if len(handCardList) == 0:
				self.tired()
			else:
				entity = random.choice(handCardList)
				entity.pos = 'HAND'


	def tired(self):
		self.tiredSum += 1
		DEBUG_MSG("Avatar::tired: %i.  tiredSum: %i" %( self.id,self.tiredSum))
		self.recvDamage(self.id,self.tiredSum)

	def msg(self,msg):
		pass

	def getCardFromKZ(self,entityID):
		DEBUG_MSG('Avatar:[%s]getCardFromKZ::entityID:[%s]'%(self.id,entityID))
		entity = KBEngine.entities.get(entityID,None)
		if entity == None:
			return
		entity.pos = 'HAND'

	def getPosEntityList(self,pos):
		#获取所选POS的卡牌
		ls = []
		for entity in self.cardEntityList:
			if entity.pos == pos:
				ls.append(entity)
		#self.KZsum = len(ls)
		if pos != 'KZ':
			DEBUG_MSG('Avatar:[%s]getPosEntityList::needPos:[%s] returnLs:len:[%s] ls:[%s]' % (self.id, pos,len(ls),str(ls)))
		return ls

	def UpdateInfor(self):
		if self.KZsum != len(self.getPosEntityList('KZ')):
			self.KZsum = len(self.getPosEntityList('KZ'))

	def die(self):
		self.reqGiveUp(self.id)

	def reqGiveUp(self,callerID):
		if callerID != self.id:
			return

		if not self.onPlaying:
			return

		self.onPlaying = False
		DEBUG_MSG('Avatar:[%s]reqGiveUp'%(self.id))
		self.battlefiled.reqGiveUp(self.playerID)


	def reqEndRound(self):
		self.battlefiled.reqEndRound(self.playerID)


	def ifcardEntityCanBeUsed(self,cardEntityID):
		entity = KBEngine.entities.get(cardEntityID,None)
		if entity == None:
			return False
		if entity in self.cardEntityList:
			if entity.pos == 'HAND':
				return True
			elif entity.pos == 'SKILL':
				return True


	def battleMsg(self,msg):
		self.client.battleMsg(msg)

	def followerPosAssigned(self,entityID,needPosID):
		entity = KBEngine.entities.get(entityID,None)

		self.followerList.insert(needPosID,entity)

		for i in range(len(self.followerList)):
			self.followerList[i].changePos(str(i))

	def followerDie(self,entityID):
		entity = KBEngine.entities.get(entityID,None)
		self.followerList.remove(entity)
		
		for i in range(len(self.followerList)):
			self.followerList[i].changePos(str(i))

	def followerPosReassigned(self):
		for follower in self.followerList:
			if follower.pos.isdigit():
				continue
			else:
				self.followerList.remove(follower)

		for i in range(len(self.followerList)):
			self.followerList[i].changePos(str(i))

	def followerRemove(self,entityID):
		entity = KBEngine.entities.get(entityID,None)
		self.followerList.remove(entity)

		for i in range(len(self.followerList)):
			self.followerList[i].pos = str(i)

	def uesCrystal(self,sourceID,crystalSum):
		DEBUG_MSG('Avatar:[%s]uesCrystal::entityID:[%s] useSum:[%s]  currentSum:[%s]'%(self.id,sourceID,crystalSum,self.CrystalAvaliable))
		self.CrystalAvaliable -= crystalSum
		if self.CrystalAvaliable < 0:
			self.CrystalAvaliable = 0
			ERROR_MSG('crystal is less than use')

	def reqEndRound(self,callerID):
		DEBUG_MSG('Avatar:[%s]reqEndRound::callerID:[%s]'%(self.id,callerID))
		if callerID != self.id:
			return
		if self.situation == 0:
			return
		if self.afterTime > self.battlefiled.roundTime - 2:
			return
		self.battlefiled.reqEndRound()

	def testMaxCrystal(self,callerID):
		if callerID!=self.id:
			return
		self.CrystalAvaliable = 200

	def testGetCard(self,callerID,cardID):
		DEBUG_MSG('Avatar:[%s]testGetCard::cardID:[%s]'%(self.id,cardID))
		if callerID!=self.id:
			return
		id = int(cardID)
		if id in d_card_dis.datas:
			self.creatHandCard(id)

	def testAddTime(self,callerID):
		if callerID!=self.id:
			return
		self.battlefiled.roundTime = 9999999

	def testChangeSkill(self,callerID,skillID):
		if callerID!=self.id:
			return
		DEBUG_MSG('Avatar:[%s]testChangeSkill::skillID:[%s]'%(self.id,skillID))
		if skillID > 9:
			return
		ls = self.getPosEntityList('SKILL')
		for entity in ls:
			entity.changePos("USED")
		self.creatCardEntity(20001000+skillID,'SKILL')

	def reqSendDialog(self,callerID,msg,name):
		DEBUG_MSG('Avatar:[%s] reqSendDialog'%(self.id))
		if callerID!= self.id:
			return
		self.allClients.onSendDialog(msg,name)

	def randomDiscard(self,s = 1):
		DEBUG_MSG('Avatar:[%s] randomDiscard:[%s]'%(self.id,s))
		ls = self.getPosEntityList('HAND')
		if len(ls) <= s:
			pass
		else:
			ls = random.sample(ls,s)
		for entity in ls:
			entity.discard()

	def replaceEntity(self,entityID,targetCardID):

		entity = self.getEntityByID(entityID)
		if entity == None:
			return
		entity.delAllBuff()
		if not targetCardID in d_card_dis.datas:
			return
		params = {
			"cardID": targetCardID,
			"playerID": self.playerID,
			"battlefiled": self.battlefiled,
			'pos': entity.pos,
			'avatar': self,
			'avatarID': self.id
		}
		e = KBEngine.createEntity('card', self.spaceID, tuple(self.position), tuple(self.direction),params)

		lss = [self.cardEntityList,self.followerList,self.battlefiled.entityList]
		for ls in lss:
			for i in range(len(ls)):
				if ls[i] == entity:
					ls[i] = e
		self.battlefiled.onPosChange(e.id)

	def summorFollower(self,cardIDList,srcEntityID,srcEntityPos):
		for cardID in cardIDList:
			DEBUG_MSG('Avatar:[%s] summorFollower:[%s]' % (self.id, cardID))
			if len(self.followerList) > 6:
				return
			if not cardID in d_card_dis.datas:
				continue
			params = {
				"cardID": cardID,
				"playerID": self.playerID,
				"battlefiled": self.battlefiled,
				'pos': 'N',
				'avatar': self,
				'avatarID': self.id
			}
			e = KBEngine.createEntity('card', self.spaceID, tuple(self.position),tuple(self.direction), params)
			self.cardEntityList.append(e)
			self.followerPosAssigned(e.id,int(srcEntityPos)+1)

	def getWeapon(self,weaponID = 0):
		if weaponID == 0:
			return self.getSelfWeapon()

		DEBUG_MSG('Avatar:[%s] getWeapon:[%s]' % (self.id, weaponID))
		if weaponID not in d_card_dis.datas:
			ERROR_MSG('ID is wrong')
		self.loseWeapon()
		params = {
			"cardID": weaponID,
			"playerID": self.playerID,
			"battlefiled": self.battlefiled,
			'avatar': self,
			'avatarID': self.id
		}
		e = KBEngine.createEntity('card', self.spaceID, tuple(self.position), tuple(self.direction),params)
		self.cardEntityList.append(e)
		e.changePos("WEAPON")

	def loseWeapon(self):
		weaponLs = self.getPosEntityList('WEAPON')
		DEBUG_MSG('Avatar:[%s] len(weaponLs):[%s]' % (self.id, len(weaponLs)))
		if len(weaponLs) == 1:
			weapon = weaponLs[0]
			weapon.onDead()
			weapon.changePos('DEAD')
		elif len(weaponLs) == 0:
			pass
		else:
			ERROR_MSG('weapon is more than one')
			for e in weaponLs:
				e.changePos('DEAD')

	def battleEnd(self,success):
		if self.client != None:
			self.client.battleResultClientDisplay(success)
		self.base.BattleEnd()
		self.addTimer(0.1,0.1,6)

	def destroyProcess(self):
		if len(self.cardEntityList) > 0:
			self.addTimer(0.1, 0.1, 6)
		elif self.onPlaying:
			self.die()
			self.onPlaying = False
		else:
			self.destroy()

	def updateBuffPropertyEffect(self):
		super().updateBuffPropertyEffect()
		if self.situation == 1:
			weapon = self.getSelfWeapon()
			if weapon != None:
				self.att += weapon.att
		self.updateisAbled()

	def updateisAbled(self):
		if (self.attSum > self.isWindfury and (self.getSelfWeapon() == None or self.attSum > self.getSelfWeapon().isWindfury)) or self.situation == 0:
			self.isAbled = 0
		else:
			self.isAbled = 1

	#--------------------------------------------------------------------------------------------
	#                              Callbacks
	#--------------------------------------------------------------------------------------------
	def onTimer(self, tid, userArg):
		"""
		KBEngine method.
		引擎回调timer触发
		"""
		#DEBUG_MSG("%s::onTimer: %i, tid:%i, arg:%i" % (self.getScriptName(), self.id, tid, userArg))
		if userArg == 1:
			self.NoCardBeChoosedProcess()
		elif userArg == 2:
			self.init()
		elif 4 == userArg:
			self.onCreatCardEntity()
		elif 5 == userArg:
			self.UpdateInfor()
		elif 6 == userArg:
			self.destroyAllEntity()

	def onGetWeapon(self,weaponEntityID):
		super(Avatar, self).onGetWeapon(weaponEntityID)
		self.updateBuffPropertyEffect()
		for entity in self.followerList:
			entity.onGetWeapon(weaponEntityID)

	def onLoseWeapon(self,weaponEntityID):
		super(Avatar, self).onLoseWeapon(weaponEntityID)
		self.updateBuffPropertyEffect()
		for entity in self.followerList:
			entity.onLoseWeapon(weaponEntityID)

	def destroyAllEntity(self):
		for i in range(10):
			if len(self.cardEntityList) > 0:
				self.cardEntityList[0].destroy()
				del self.cardEntityList[0]
			else:
				self.destroyProcess()
				break
	
	def onDestroy(self):
		"""
		KBEngine method.
		entity销毁
		"""
		DEBUG_MSG("Avatar(CELL)::onDestroy: %i." % self.id)


	def onCreatCardEntity(self):
		if len(self.onCreatCardEntityList) == 0:
			self.onCreatOk()
			return

		data = self.onCreatCardEntityList[0]
		self.onCreatCardEntityList.remove(data)

		pos = data['pos']
		cardID = data['cardID']

		DEBUG_MSG('Avatar:[%s] creatCardEntity cardID:[%s]'%(self.id,cardID))
		params = {
			"cardID"	: cardID,
			"playerID" : self.playerID,
			"battlefiled" : self.battlefiled,
			'pos':pos,
			'avatar':self,
			'avatarID':self.id
		}
		if pos == 'SKILL':
			params['isAbled'] = 1
			DEBUG_MSG('Avatar:[%s] pos is skill' % (self.id))
		e = KBEngine.createEntity('card', self.spaceID, tuple(self.position), tuple(self.direction), params)

		self.cardEntityList.append(e)
		self.battlefiled.entityList.append(e)

	def onCreatOk(self):		
		if not self.startHaveChooseCard:
			DEBUG_MSG('Avatar:[%s] onCreatOk to beginCardChoose '%(self.id))
			self.battleMsg('卡牌实体创建完成 即将开始初始卡牌选择')
			self.startHaveChooseCard = True
			self.beginCardChoose()
			return

	def onUseCard(self,playerID,cardEntityID,cardID):
		if playerID == self.playerID:
			self.uesCardSumInRound += 1
			self.uesCardSum += 1




		

