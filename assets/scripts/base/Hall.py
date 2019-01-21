# -*- coding: utf-8 -*-
import KBEngine
import random
import time
from KBEDebug import *
import Functor
import datetime
from Poller import *
from ComFunc import *
import Rank

Time_CD_AR = 60*3
#每隔一个小时刷新排行榜
Time_CD_RANK = 60*2

g_WebPoller = WebPoller()

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
        #从数据库读取AR配置数据
        self.addTimer(1,Time_CD_AR,1)
        #每隔10秒检查地图宠物是否过期，是否需要刷新
        self.addTimer(1,10,2)
        #http服务器
        self.addTimer(1,0.5,3)
        g_WebPoller.StartServer()
        #生成器
        self.generator = Generator()        
        #初始化排行榜
        self.rank = Rank.Rank(self)
        #定时器检查周日的9点和10点
        self.addTimer(1,1,4)
        
    def onTimer(self, id, userArg):
        if userArg == 1:
            self.UpdatePetMapConfig()
        elif userArg == 2:
            self.CreatePetMapInfo()
        elif userArg == 3:
            g_WebPoller.tickTornadoIOLoop()
            self.generator.Get()
        elif userArg == 4:
            self.rank.CheckRankTime()
            self.rank.CheckRefreshTime(Time_CD_RANK)          
        elif userArg == 6:
            self.SendAward(id)

    #充值
    def ReChange(self, DBID, errMsg, moneyType, moneyValue):
        KBEngine.createEntityFromDBID("Account",DBID,Functor.Functor(self.onReChange,errMsg,moneyType,moneyValue))
            
    def onReChange(self,errMsg,moneyType,moneyValue,baseRef,databaseID,wasActive):
        if baseRef is None:
            ERROR_MSG("onReChange baseRef error:%i" % databaseID)
            self.generator.Set(databaseID,self.onReChange,errMsg,moneyType,moneyValue)
        else:
            if errMsg == 'success':
                baseRef.ChangeBaseData(moneyType,moneyValue,'充值')
                baseRef.Data['FirstRecharge'] = 1
            bags = baseRef.getComponent("bags")
            bags.client.onRecharge(errMsg,moneyType,moneyValue)
            INFO_MSG("onReChange:%s,%i,%i" % (errMsg,databaseID, moneyValue ) )
            if not wasActive:
                baseRef.destroy()

    def SendAward(self, time_id):
        DiamondAward = self.rank.GetBuffObj('Diamond').weekAwardList
        PetAward = self.rank.GetBuffObj('Pet').weekAwardList
        MoneyAward = self.rank.GetBuffObj('Money').weekAwardList
        EglodAward = self.rank.GetBuffObj('Eglod').weekAwardList
        if len(DiamondAward) != 0:
            AwardInfo = DiamondAward.pop()
            self.SendMailMessage(AwardInfo['DBID'],AwardInfo['MessageID'],AwardInfo['awardTypeList'],AwardInfo['awardValueList'],AwardInfo['title'])
            INFO_MSG("DiamondAward:%s,%d" % (str(AwardInfo), len(DiamondAward)) )
            return
        if len(PetAward) != 0:
            AwardInfo = PetAward.pop()
            self.SendMailMessage(AwardInfo['DBID'],AwardInfo['MessageID'],AwardInfo['awardTypeList'],AwardInfo['awardValueList'],AwardInfo['title'])
            INFO_MSG("PetAward:%s,%d" % (str(AwardInfo), len(PetAward)) )
            return
        if len(MoneyAward) != 0:
            AwardInfo = MoneyAward.pop()
            self.SendMailMessage(AwardInfo['DBID'],AwardInfo['MessageID'],AwardInfo['awardTypeList'],AwardInfo['awardValueList'],AwardInfo['title'])
            INFO_MSG("MoneyAward:%s,%d" % (str(AwardInfo), len(MoneyAward)) )
            return
        if len(EglodAward) != 0:
            AwardInfo = EglodAward.pop()
            self.SendMailMessage(AwardInfo['DBID'],AwardInfo['MessageID'],AwardInfo['awardTypeList'],AwardInfo['awardValueList'],AwardInfo['title'])
            INFO_MSG("EglodAward:%s,%d" % (str(AwardInfo), len(EglodAward)) )
            return
        self.delTimer(time_id)

    #发送邮件
    def SendMailMessage(self, DBID, MessageID, awardTypelist, awardValuelist, MessageTEXT = '', timeinterval = 7*24*60*60):
        MessageType = '邮箱奖励'
        MesaageUUID = KBEngine.genUUID64()
        nowtime = int(time.time() )
        Endtime = nowtime + timeinterval
        MessageInfo = {'MesaageUUID':MesaageUUID, 'time':nowtime ,'MessageID':MessageID, 'Endtime':Endtime}
        MessageInfo['ArgList'] = ''
        if len(awardTypelist) != len(awardValuelist):
            ERROR_MSG('奖励表配置错误！:%s,%s' % (str(awardTypelist),str(awardValuelist)))
            return
        for index,awardType in enumerate(awardTypelist):
            AddSplitStr(MessageInfo,'ArgList',awardType)
            AddSplitStr(MessageInfo,'ArgList',awardValuelist[index])
        AddSplitStr(MessageInfo,'ArgList',MessageTEXT)
        KBEngine.createEntityFromDBID("Account",int(DBID),Functor.Functor(self.onMailMessage,MessageInfo,MessageType))
        DEBUG_MSG('SendMailMessage, MessageInfo:%s' % str(MessageInfo))

    def SendMailMessage2(self, DBID, MessageID, ArgList, timeinterval = 7*24*60*60):
        MessageType = '邮箱奖励'
        MesaageUUID = KBEngine.genUUID64()
        nowtime = int(time.time() )
        Endtime = nowtime + timeinterval
        MessageInfo = {'MesaageUUID':MesaageUUID, 'time':nowtime ,'MessageID':MessageID, 'Endtime':Endtime, 'ArgList':ArgList}  
        KBEngine.createEntityFromDBID("Account",DBID,Functor.Functor(self.onMailMessage,MessageInfo,MessageType))
        DEBUG_MSG('SendMailMessage2, MessageInfo:%s' % str(MessageInfo))    
                
    def onMailMessage(self,MessageInfo,MessageType,baseRef,databaseID,wasActive):
        if baseRef is None:
            ERROR_MSG("onMailMessage baseRef error:%i" % databaseID)
        else:
            Friends = baseRef.getComponent("Friends")
            Friends.WriteSysMessage(MessageInfo,MessageType)
            if not wasActive:
                baseRef.destroy()


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
        #DEBUG_MSG("PetMapConfigList:%s" % str(self.PetMapConfigList) )

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
        if res != 0:
            #DEBUG_MSG("CheckTime is timeout res:%i, %s" % (res,str(PetMapConfig)) )
            self.DelPetMap2(PetMapConfig['position'])
        return res

    def DelPetMap2(self,position):	
        for index, PetMapInfo in enumerate(self.PetMapInfoList):
            if PetMapInfo['position'] == position:
                del self.PetMapInfoList[index]
                DEBUG_MSG("del PetMapInfo: %s" % position)
                return True
        return False

    def CheckTime(self, PetMapConfig):
        NowTime = time.time()
        date = datetime.datetime.fromtimestamp(NowTime)
        if date.hour < int(PetMapConfig['Stime']):
            return -1
        if date.hour >= int(PetMapConfig['Etime']):
            return -2
        Scycle = int(PetMapConfig['Scycle'])
        Ecycle = int(PetMapConfig['Ecycle'])
        if Scycle == Ecycle:
            Ecycle = Scycle + 24*3600
        if Scycle != 0 and int(NowTime) < Scycle:
            return -3
        if Ecycle != 0 and int(NowTime) > Ecycle:
            return -4
        return 0

    def BuildPetMap(self, PetMapConfig, PetMapInfo):
        if int(PetMapConfig['enable']) == 0:
            self.DelPetMap2(PetMapInfo['position'])
            return -1
        #删除过期的数据
        if self.DelPetMap(PetMapConfig) != 0:
            return -2
        PetMapInfo['radius'] = int(PetMapConfig['radius'])
        #是否可以刷新数据
        nowTime = int(time.time())
        refreshEndTime = int(PetMapInfo['refreshEndTime'])
        if  refreshEndTime != 0 and nowTime < refreshEndTime:
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

    

