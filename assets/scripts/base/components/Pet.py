import KBEngine
import Functor
from KBEDebug import *
from ComFunc import *
import d_game
import time
import random
from GameRecord import *
from ComFunc import *
import copy

class Pet(KBEngine.EntityComponent):
    def __init__(self):
        KBEngine.EntityComponent.__init__(self)
    
    def onAttached(self, owner):
        #DEBUG_MSG("Pet::onAttached(): owner=%i" % (owner.id))
        pass

    def onDetached(self, owner):
        #DEBUG_MSG("Pet::onDetached(): owner=%i" % (owner.id))
        pass
        
    def onClientEnabled(self):
        """
        KBEngine method.
        该entity被正式激活为可使用， 此时entity已经建立了client对应实体， 可以在此创建它的
        cell部分。
        """
        DEBUG_MSG("Pet[%i]::onClientEnabled:entities enable." % (self.ownerID))
        #self.InitClientData()
    
    def InitClientData(self):
        if hasattr(self,'client'):
            self.reqAllPetInfo(0)

      
    def onClientDeath(self):
        """
		KBEngine method.
		客户端对应实体已经销毁
        """
        DEBUG_MSG("Pet[%i].onClientDeath:" % self.ownerID)	

    def onTimer(self, id, userArg):
        """
		KBEngine method.
		使用addTimer后， 当时间到达则该接口被调用
		@param id		: addTimer 的返回值ID
		@param userArg	: addTimer 最后一个参数所给入的数据
        """
        #DEBUG_MSG(id, userArg)

    def Component(self,name):
        return self.owner.getComponent(name)
    '''
	  获取宠物定点投放信息
	'''
    def reqPetMapInfo(self, cityName):
        MapInfoList = KBEngine.globalData["Halls"].GetPetMapInfoList(cityName)
        self.client.onPetMapInfo(MapInfoList)
        DEBUG_MSG("reqPetMapInfo: %s" % str(MapInfoList) )

    def GetConfigPetSelf(self):
        try:
            Info = d_game.PetSelf[1]
        except (IndexError, KeyError) as e:
            ERROR_MSG("GetConfigPetSelf error:%s," % (str(e)))
            return None
        return Info

    def CreatePetSelf(self, d_petself):
        nowTime = int(time.time())
        refreshEndTime = self.PetSelfInfo['refreshEndTime']
        if refreshEndTime != 0 and nowTime < refreshEndTime:
            return 
        #刷新数据
        PetSelfInfo = {}
        PetSelfInfo['radius'] = d_petself['radius']
        PetSelfInfo['PetXYZList'] = []
        if d_petself['GenIDList']:
            PetTotalNum = random.randint(d_petself['GenMinMax'][0],d_petself['GenMinMax'][1] )
            RandPetXYZ(PetSelfInfo['PetXYZList'],d_petself['GenIDList'],PetTotalNum)
        if IsProbability(d_petself['SpeProb'])[0] and d_petself['SpeIDList']:
            PetTotalNum = random.randint(d_petself['SpeMinMax'][0],d_petself['SpeMinMax'][1] )
            RandPetXYZ(PetSelfInfo['PetXYZList'],d_petself['SpeIDList'],PetTotalNum,d_petself['SpeProbList'])
        PetSelfInfo['refreshEndTime'] = nowTime + d_petself['frequence']*60
        self.PetSelfInfo = PetSelfInfo
     
    '''
	  获取定位投放宠物信息
	'''
    def reqPetSelfInfo(self):
        d_petself = self.GetConfigPetSelf()
        if d_petself is None:
            return
        self.CreatePetSelf(d_petself)
        self.client.onPetSelfInfo(self.PetSelfInfo)
        DEBUG_MSG("reqPetSelfInfo: %s" % str(self.PetSelfInfo) )

    def DelPetMapNum1(self,PetType):
        for PetXYZ in self.PetSelfInfo['PetXYZList']:
            if PetXYZ['PetType'] == PetType:
                if PetXYZ['PetNum'] > 0:
                    PetXYZ['PetNum'] -= 1
                    return True
        return False

    def DelPetMapNum2(self,position,PetType):
        return KBEngine.globalData["Halls"].DelPetNum(position, PetType)

    def DelPetMapNum(self, position, PetType):
        if position == '':
            #抓定位宠物
            return self.DelPetMapNum1(PetType)
        else:
            #抓定点宠物信息
            return self.DelPetMapNum2(position,PetType)

    def GetConfigGenPet(self,PetType):
        try:
            Info = d_game.GenPet[PetType]
        except (IndexError, KeyError) as e:
            return None
        return Info

    def GetConfigSpePet(self,PetType):
        try:
            Info = d_game.SpePet[PetType]
        except (IndexError, KeyError) as e:
            return None
        return Info 

    def AddPet(self, PetType,Des):
        d_GenPet = self.GetConfigGenPet(PetType)
        PetInfo = {}
        UUID = KBEngine.genUUID64()
        if d_GenPet is not None:                          
            nowtime = int(time.time() )
            PetInfo = {'UUID':UUID, 'PetType':PetType, 'Endtime':nowtime+d_GenPet['time']*60 }
        else:
            PetInfo = {'UUID':UUID, 'PetType':PetType, 'Endtime':0 }
        self.PetData.append(PetInfo)
        self.client.onAddPet(PetInfo)
        GamePetRecord(self.owner.AccountName(),self.owner.databaseID,PetType,1,Des)

    def DelPet(self, UUID, Des):
        for index,PetInfo in enumerate(self.PetData):
            if PetInfo['UUID'] == UUID:
                GamePetRecord(self.owner.AccountName(),self.owner.databaseID,PetInfo['PetType'],-1,Des)
                del self.PetData[index]
                self.client.onDelPet(UUID)
                
    def DelPetByType(self, PetType, Des):
        for index,PetInfo in enumerate(self.PetData):
            if PetInfo['PetType'] == PetType:
                GamePetRecord(self.owner.AccountName(),self.owner.databaseID,PetInfo['PetType'],-1,Des)
                self.client.onDelPet(PetInfo['UUID'])
                del self.PetData[index]
                return True
        return False
                

    def CheckAllCDTime(self):
        nowtime = int(time.time() )
        for PetInfo in self.PetData:
            self.CheckCDTime(PetInfo,nowtime)

    def CheckCDTime(self, PetInfo, nowtime):
        if PetInfo['Endtime'] != 0 and nowtime >= PetInfo['Endtime']:
            self.DelPet(PetInfo['UUID'],'宠物收获')
            self.PetAward(PetInfo['PetType'])

    def PetAward(self, PetType):
        d_GenPet = self.GetConfigGenPet(PetType)
        if d_GenPet is None:
            return
        if not d_GenPet['awardType'] or not d_GenPet['awardValue']:
            return
        #获得宠物名称
        d_Item = self.Component("bags").GetConfigItem(PetType)
        for index,awardType in enumerate(d_GenPet['awardType']) :
            self.owner.ChangeBaseData(awardType, d_GenPet['awardValue'][index],'增加，普通宠物奖励')
            self.Component("Friends").SYSMessage(0, 3013, int(time.time()) ,d_Item['ItemName'],d_GenPet['awardValue'][index],'游戏币')

    '''
	  请求宠物信息
	'''  
    def reqAllPetInfo(self, DBID):
        if DBID == 0:
            self.client.onAllPetInfo(self.owner.databaseID,self.PetData)
        else: 
            KBEngine.createEntityFromDBID("Account",DBID,Functor.Functor(self.CallBackAllPetInfo))
		
    def CallBackAllPetInfo(self,baseRef,databaseID,wasActive):
        if baseRef is None:
            g_Generator.Set(databaseID,self.CallBackAllPetInfo)
        else:
            Pet = baseRef.getComponent("Pet")
            self.client.onAllPetInfo(databaseID,Pet.PetData)
            if not wasActive:
                baseRef.destroy()
       
    def reqPetHarvest(self, UUID):
        for PetInfo in self.PetData:
            if PetInfo['UUID'] == UUID:
                pet_info = copy.deepcopy(PetInfo)
                self.CheckCDTime(PetInfo,int(time.time()))
                self.client.onPetHarvest(pet_info)
        

    def CheckPetCount(self):
        # d_petself = self.GetConfigPetSelf()
        # if d_petself['PetMaxNum'] <= len(self.PetData):
        #     return False
        return True

    '''
	  捕捉宠物 (position:空 定位投放)(ItemType:没有凤凰链等道具就填0)
	'''
    def reqCatchPet(self, position, PetType, ItemType):
        Item = self.Component("bags").GetConfigItem(PetType)
        if Item is None:
            return 
        #判断是否超过数量上限
        if not self.CheckPetCount():
            self.client.onCatchPet('超出抓捕上限',PetType,0,0)
            return
        res = 0
        if Item['ItemType'] == '宠物':
            res = self.CatchGenPet(position, PetType)
        elif Item['ItemType'] == '宝宝':
            res = self.CatchSpePet(position, PetType, ItemType)
        #E币掉落, 除了使用道具失败
        if res != -4:
            self.CatchAward()
        DEBUG_MSG("reqCatchPet: %i,%i" % (res,PetType) )

    def CatchGenPet(self, position, PetType):
        d_GenPet = self.GetConfigGenPet(PetType)
        if d_GenPet is None:
            self.client.onCatchPet('PetType类型错误',PetType,0,0)
            return -1
        #删除地图宠物信息
        if not self.DelPetMapNum(position,PetType):
            self.client.onCatchPet('地铁上没有该宠物',PetType,0,0)
            return -2
        #概率抓到
        probability = d_GenPet['probability']
        sucss, prob = IsProbability(probability)
        if not sucss:
            self.client.onCatchPet('抓捕失败,当前概率:%i' % prob,PetType,0,0)
            return -3
        #添加宠物
        self.AddPet(PetType,'捕捉普通宠物')
        #消息
        Item = self.Component("bags").GetConfigItem(PetType)
        self.Component("Friends").SYSMessage(0, 3012, int(time.time()) , Item['ItemName'])
        self.client.onCatchPet('成功',PetType,0,0)
        return 0


    def CatchSpePet(self, position, PetType, ItemType):
        d_SpePet = self.GetConfigSpePet(PetType)
        if d_SpePet is None:
            self.client.onCatchPet('PetType类型错误',PetType,0,0)
            return -4
        if ItemType != 0:
            argDict = {'position':position, 'PetType':PetType}
            err = self.Component("bags").UseItem(ItemType, argDict,Des='使用凤凰链:%d' % PetType) 
            if err != 0:
                self.client.onCatchPet('道具不足',PetType,0,0)
                return -5
            return 0
        else:
            return self.CatchSpePet2(position,PetType,ItemType,0)

    def CatchSpePet2(self,position,PetType,ItemType,Addprob):
        d_SpePet = self.GetConfigSpePet(PetType)
        #删除地图宠物信息
        if not self.DelPetMapNum(position,PetType):
            if Addprob != 0:
                self.Component("bags").AddItem(ItemType,1,'添加凤凰链道具')
            self.client.onCatchPet('地图上没有该宠物',PetType,0,0)
            return -6
        #概率抓到
        probability = d_SpePet['probability'] + Addprob
        sucss, prob = IsProbability(probability)
        if not sucss:
            Type,Value = self.SpeFaileAward(d_SpePet)
            self.client.onCatchPet('宝宝抓取失败,概率值:%i' % prob,PetType,Type,Value)
            return -7
        #添加宝宝
        self.AddPet(PetType,'捕捉宝宝')
        #消息
        Item = self.Component("bags").GetConfigItem(PetType)
        self.Component("Friends").SYSMessage(0, 3012, int(time.time()) , Item['ItemName'])
        self.client.onCatchPet('成功',PetType,0,0)
        return 0

    #宝宝抓捕失败补偿
    def SpeFaileAward(self,d_SpePet):
        if d_SpePet['GetValue']:
            value = random.randint(d_SpePet['GetValue'][0],d_SpePet['GetValue'][1])
            self.owner.ChangeBaseData(d_SpePet['GetType'], value,'宝宝抓捕失败奖励')
            return d_SpePet['GetType'], value
        return 0,0

    #E币掉落，有一定概率掉落一个E币
    def CatchAward(self):
        d_PetSelf = self.GetConfigPetSelf()
        sucss, prob = IsProbability(d_PetSelf['probability'])
        if not sucss:
            DEBUG_MSG("E币掉落失败，概率值%i" % prob )
            return
        self.owner.ChangeBaseData(4, 100,'E币掉落')
        self.client.onAward(4,100)

    #获得宝宝的PetType列表
    def GetSpePetList(self):
        SpePetList = []
        for key, value in d_game.ItemInfo.items():
            if value['ItemType'] == '宝宝':
                SpePetList.append(value['ID'])
        return SpePetList
    '''
	  宠物合成
	'''  
    def reqPetCompound(self):
        SpePetList = self.GetSpePetList()
        if not SpePetList:
            self.client.onPetCompound('配置表找不到特殊宠物',0)
            return
        for PetType in SpePetList:
            if not self.DelPetByType(PetType,'宝宝合成'):
                self.client.onPetCompound('没有该宝宝',PetType)
                return
        #获得1玫开元通宝
        self.owner.ChangeBaseData(3, 100,'宠物合成获得开元通宝')
        self.client.onPetCompound('成功',0)
        
