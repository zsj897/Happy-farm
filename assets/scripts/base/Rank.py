import KBEngine
import time
from KBEDebug import *
import redis
import d_game

class BuffRankBase:
    def __init__(self):
        self.TotalRank = []
        self.WeekRank = []
        self.messageID = 0 
        self.weekAwardList = []
    def SetBuff(self,total, week):
        self.TotalRank = total
        self.WeekRank = week
    def GetTotalBuff(self):
        return self.TotalRank
    def GetWeekBuff(self):
        return self.WeekRank
    def Clear(self): #清空奖励列表
        self.weekAwardList = []
    def GetMessageID(self):
        return  self.messageID
    def SetAwardInfo(self,AwardInfo):
        self.weekAwardList.append(AwardInfo)
       
class DiamodBuffRank(BuffRankBase):
    def __init__(self):
        BuffRankBase.__init__(self)
        self.messageID = 6001

class PetBuffRank(BuffRankBase):
    def __init__(self):
        BuffRankBase.__init__(self)
        self.messageID = 6002

class MoneyBuffRank(BuffRankBase):
    def __init__(self):
        BuffRankBase.__init__(self)
        self.messageID = 6003

class EglodBuffRank(BuffRankBase):
    def __init__(self):
        BuffRankBase.__init__(self)
        self.messageID = 6004

class Rank():
    def __init__(self, Entity):
        self.r=redis.Redis(port=63797,password='rA12d_E25m!Di78*-Izl58s6$s!!S_zlwy')
        #self.r=redis.Redis()
        self.Hall = Entity
        #开启周排行榜
        self.IsStart = True
        INFO_MSG('Rank init is success!')
        self._DiamodBuffRank = DiamodBuffRank()
        self._PetBuffRank = PetBuffRank()
        self._MoneyBuffRank = MoneyBuffRank()
        self._EglodBuffRank = EglodBuffRank()
        self._NextRefreshTime = 0

    def CheckRankTime(self):
        week = time.strftime("%a", time.localtime())
        if week == 'Sun':
            Hour = time.strftime("%H", time.localtime())
            #结算9点发放奖励
            if Hour == '21' and self.IsStart:
                self.EndOldWeekRank()
                self.IsStart = False
            #10点开始新的周排行
            if Hour == '22' and not self.IsStart:               
                self.StartNewWeekRank()
                self.IsStart = True
            #DEBUG_MSG("Rank CheckRankTime:Hour:%s,IsStart:%i" % (Hour,self.IsStart) )
  
    #更新排行榜数据
    def UpdateRankDate(self):
        topNum = 10
        total_d  = self.GetTotalRankName('Diamond', topNum)
        week_d = self.GetWeekRankName('Diamond', topNum)
        self._DiamodBuffRank.SetBuff(total_d, week_d)

        total_p = self.GetTotalRankName('Pet', topNum)
        week_p = self.GetWeekRankName('Pet', topNum)
        self._PetBuffRank.SetBuff(total_p, week_p)

        total_m = self.GetTotalRankName('Money', topNum)
        week_m = self.GetWeekRankName('Money', topNum)
        self._MoneyBuffRank.SetBuff(total_m, week_m )
        
        total_E = self.GetTotalRankName('Eglod', topNum)
        week_E = self.GetWeekRankName('Eglod', topNum)
        self._EglodBuffRank.SetBuff(total_E, week_E )

    def CheckRefreshTime(self, timeInterval):
        nowtime = int(time.time())
        if nowtime > self._NextRefreshTime - 2:  #提前60秒刷新 
            self._NextRefreshTime = nowtime + timeInterval + 2
            self.UpdateRankDate()
        
    def SetRefreshTime(self,timeInterval):
        nowtime = int(time.time())
        self._NextRefreshTime = nowtime + timeInterval

    def GetBuffTotalRank(self, Type):
        if Type == 'Diamond':
            return self._DiamodBuffRank.GetTotalBuff()
        elif Type == 'Pet':
            return self._PetBuffRank.GetTotalBuff()
        elif Type == 'Money':
            return self._MoneyBuffRank.GetTotalBuff()
        elif Type == 'Eglod':
            return self._EglodBuffRank.GetTotalBuff()
        ERROR_MSG('GetBuffTotalRank type is error')

    def GetBuffWeekRank(self, Type):
        if Type == 'Diamond':
            return self._DiamodBuffRank.GetWeekBuff()
        elif Type == 'Pet':
            return self._PetBuffRank.GetWeekBuff()
        elif Type == 'Money':
            return self._MoneyBuffRank.GetWeekBuff()
        elif Type == 'Eglod':
            return self._EglodBuffRank.GetWeekBuff()
        ERROR_MSG('GetBuffWeekRank type is error')

    def GetBuffObj(self,Type):
        if Type == 'Diamond':
            return self._DiamodBuffRank
        elif Type == 'Pet':
            return self._PetBuffRank
        elif Type == 'Money':
            return self._MoneyBuffRank
        elif Type == 'Eglod':
            return self._EglodBuffRank
        ERROR_MSG('GetBuffObj type is error')


    #记录账户内容
    def SetAcountRecord(self,Type,rankInfo):
        Lastkey = self.Getkey(rankInfo[0],Type,'Last')
        self.r.hset(Lastkey, 'Last_score', rankInfo[1])
        self.r.hset(Lastkey, 'Last_rank', rankInfo[2])
        Bestkey = self.Getkey(rankInfo[0],Type,'Best')
        if self.r.exists(Bestkey):
            score = self.r.hget(Bestkey, 'Best_score')
            if rankInfo[1] > int(score):
                self.r.hset(Bestkey,'Best_score',rankInfo[1])
                self.r.hset(Bestkey,'Best_rank',rankInfo[2])
        else:
            self.r.hset(Bestkey,'Best_score', rankInfo[1])
            self.r.hset(Bestkey,'Best_rank', rankInfo[2]) 
            
    #记录排行榜奖励
    # def SetTypeAward(self,Type,rankInfo,BuffObj):
    #     MessageID = BuffObj.GetMessageID()
    #     score = rankInfo[1]
    #     rank = rankInfo[2]
    #     TitleInfo = self.GetTitle(Type,rank,score)
    #     DBID = rankInfo[4]
    #     if TitleInfo and DBID:
    #         AwardInfo = {'DBID':DBID,'MessageID':MessageID,'awardTypeList':TitleInfo['awardType'],'awardValueList':TitleInfo['awardValue'],'title':TitleInfo['title']}
    #         BuffObj.SetAwardInfo(AwardInfo)
    
    #处理排行榜
    def HandleRank(self,Type):
        ranklist = self.GetWeekRankName(Type, 0)
        if not ranklist:
            return
        BuffObj = self.GetBuffObj(Type)
        for rankInfo in ranklist:
            #账户记录
            self.SetAcountRecord(Type,rankInfo)
            #记录每个榜单的奖励
            self.SetTypeAward(Type,rankInfo)

    def SetTypeAward(self,Type,rankInfo):
        score = rankInfo[1]
        rank = rankInfo[2]
        TitleInfo = self.GetTitle(Type,rank,score)
        if TitleInfo:
            awardTypelist = TitleInfo['awardType'] 
            awardValuelist = TitleInfo['awardValue'] 
            title = TitleInfo['title']
            awardValue = ''
            for index,awardType in enumerate(awardTypelist):
                if index == 0:
                    awardValue = str(awardType)
                else:
                    awardValue += '$'+ str(awardType)
                awardValue += '$'+ str(awardValuelist[index])
            awardValue += '$'+ title
            DEBUG_MSG('SetTypeAward:%s' % awardValue)
            self.SetPlayerAward(Type,rankInfo[0],awardValue)          
            

    #结算这周排行内容
    def EndOldWeekRank(self):
        INFO_MSG('开始结算奖励!')
        #更新到最新缓存数据
        self.SetRefreshTime(60*60)
        self.UpdateRankDate()
        #处理排行榜
        self.HandleRank('Diamond')
        self.HandleRank('Pet')
        self.HandleRank('Money')
        self.HandleRank('Eglod')
        #每隔0.1秒发放一个奖励
        #self.Hall.addTimer(1,0.1,6)
        #删除周排行榜
        self.r.delete('zset_WeekDiamond')
        self.r.delete('zset_WeekPet')
        self.r.delete('zset_WeekMoney')
        self.r.delete('zset_WeekEglod')
        #清空缓存数据
        self.UpdateRankDate()
      
    def StartNewWeekRank(self):
        INFO_MSG('开启新的周排行榜!')
        self.Clear()

    def Clear(self):
        self._DiamodBuffRank.Clear()
        self._PetBuffRank.Clear()
        self._MoneyBuffRank.Clear()
        self._EglodBuffRank.Clear()

    #是否游客 true 是游客
    def IsYK(self, AccountName):
        if AccountName[0:2] == 'yk' and AccountName[2:].isdigit():
            return True
        return False

    #根据账号名插入相关信息
    def SetPlayerName(self, AccountName, PlayerName):
        key = AccountName +'_name'
        if not self.r.exists(key):
            self.r.set(key, PlayerName)

    def GetPlayerName(self, AccountName):
        if type(AccountName) is bytes:
            AccountName = AccountName.decode()
        key = AccountName +'_name'
        playerName = self.r.get(key)
        return playerName.decode()
    
    def SetDBID(self, AccountName, DBID):
        key = AccountName +'_DBID'
        if not self.r.exists(key):
            self.r.set(key, DBID)

    def GetDBID(self, AccountName):
        if type(AccountName) is bytes:
            AccountName = AccountName.decode()
        key = AccountName +'_DBID'
        DBID = self.r.get(key)
        return DBID.decode()

    def SetPlayerAward(self,Type,AccountName,awardValue):
        key = AccountName +'_' +Type +'_award'
        if not self.r.exists(key):
            self.r.set(key, awardValue)      
    
    def GetPlayerAward(self,Type,AccountName):
        if type(AccountName) is bytes:
            AccountName = AccountName.decode()
        key = AccountName +'_' +Type +'_award'
        awardValue = self.r.get(key)
        if awardValue:
            return awardValue.decode()
        else:
            return None

    def ClearAwardKey(self,AccountName):
        Diamondkey = AccountName +'_Diamond' +'_award'
        Petkey = AccountName +'_Pet' +'_award'
        Moneykey = AccountName +'_Money' +'_award'
        Eglodkey = AccountName +'_Eglod' +'_award'
        self.r.delete(Diamondkey)
        self.r.delete(Petkey)
        self.r.delete(Moneykey)
        self.r.delete(Eglodkey)

    def ChangeRank(self, Type, amount, PlayerName, AccountName, DBID):
        if self.IsYK(AccountName):
            DEBUG_MSG('yk is not rank!:%s' % AccountName)
            return
        #设置名字
        self.SetPlayerName(AccountName,PlayerName)
        self.SetDBID(AccountName,DBID)
        #改变总排行榜
        name = self.GetTotalNameByType(Type)
        if name is not None:
            self.r.zincrby(name, amount, AccountName)
        else:
            ERROR_MSG('Rank Total name is none')
        #周日晚上9点--10点禁止修改周排行榜的分数
        if not self.IsStart:
            return
        name = self.GetWeekNameByType(Type)
        if name is not None:
            self.r.zincrby(name, amount, AccountName) 
        else:
            ERROR_MSG('Rank Week name is none')


    def GetTotalNameByType(self, Type):
        name = None
        if Type == 'Diamond':
            name = 'zset_TotalDiamond'
        elif Type == 'Pet':
            name = 'zset_TotalPet'
        elif Type == 'Money':
            name = 'zset_TotalMoney'
        elif Type == 'Eglod':
            name = 'zset_TotalEglod'
        return name

    def Getkey(self, AccountName, Type , status):
        if type(AccountName) is bytes:
            AccountName = AccountName.decode()
        return AccountName+'_'+Type+'_'+status

    def GetTotalRank(self, Type, topNum, start = 0):
        name = self.GetTotalNameByType(Type)
        if name is not None:
            return self.r.zrevrange(name, start, topNum-1, withscores=True, score_cast_func=int )
        else:
            return []
    
    #转换到list
    def TupleToList(self, Tuple):
        if not Tuple:
            return None
        List = []
        for T in Tuple:
            List.append(list(T) ) 
        return List

    def GetTotalRankName(self, Type, topNum, start = 0):
        ranklist = self.TupleToList( self.GetTotalRank(Type, topNum, start) )
        if ranklist is None:
            return None
        #DEBUG_MSG("GetTotalRank type:%s,ranklist: %s" % (Type,str(ranklist)) )
        lastScore = 0
        lastRank = 0
        index = start
        for rankinfo in ranklist:
            #0
            rankinfo[0] = rankinfo[0].decode()
            #2
            Rank = self.ShowRank(index,rankinfo[1],lastRank,lastScore)
            lastScore = rankinfo[1]
            lastRank = Rank
            rankinfo.append(Rank)
            #3
            playName = self.GetPlayerName(rankinfo[0])
            rankinfo.append(playName)
            index += 1
        DEBUG_MSG("GetTotalRankName type:%s,ranklist: %s" % (Type,str(ranklist)) )
        return ranklist

    def GetTotalOwenrRank(self, Type, AccountName):
        name = self.GetTotalNameByType(Type)
        if name is not None:
            rank = self.r.zrevrank(name,AccountName)
            rank = self.GetSameScoreRank('total',Type,rank)
            return rank, self.r.zscore(name,AccountName) , self._NextRefreshTime
        else:
            ERROR_MSG('Rank name is none')
           
    def GetWeekNameByType(self, Type):
        name = None
        if Type == 'Diamond':
            name = 'zset_WeekDiamond'
        elif Type == 'Pet':
            name = 'zset_WeekPet'
        elif Type == 'Money':
            name = 'zset_WeekMoney'
        elif Type == 'Eglod':
            name = 'zset_WeekEglod'
        return name

    def GetWeekRank(self, Type, topNum, start = 0):
        name = self.GetWeekNameByType(Type)
        if name is not None:
            return self.r.zrevrange(name, start, topNum-1, withscores=True, score_cast_func=int )
        else:
            return []

    def ShowRank(self,index,score,lastRank,lastScore):
        if index >= 1 and score == lastScore:
            return lastRank
        return index+1

    def GetWeekRankName(self, Type, topNum, start = 0):
        ranklist = self.TupleToList( self.GetWeekRank(Type, topNum, start) )
        if ranklist is None:
            return None
        lastScore = 0
        lastRank = 0
        index = start
        for rankinfo in ranklist:
            #0
            rankinfo[0] = rankinfo[0].decode()
            #2
            Rank = self.ShowRank(index,rankinfo[1],lastRank,lastScore)
            lastScore = rankinfo[1]
            lastRank = Rank
            rankinfo.append(Rank)
            #3
            playName = self.GetPlayerName(rankinfo[0])
            rankinfo.append(playName)
            #4
            DBID = self.GetDBID(rankinfo[0])
            rankinfo.append(DBID)
            index += 1
        DEBUG_MSG("GetWeekRankName type:%s,ranklist: %s" % (Type,str(ranklist)) )
        return ranklist

    def GetSameScoreRank(self,week ,Type, cur_rank):
        cur_rank = int(cur_rank) if cur_rank is not None else 0
        start = cur_rank-10
        if start < 0:
            start = 0
        if week == 'week':
            ranklist = self.GetWeekRankName(Type, cur_rank+1, start)
        else:
            ranklist = self.GetTotalRankName(Type, cur_rank+1, start)
        rank = 0
        if ranklist:
            DEBUG_MSG("GetSameScoreRank start:%i,cur_rank:%i,ranklist num:%i, ranklist[-1]:%s" % (start,cur_rank,len(ranklist),str(ranklist[-1])) )
            rank = ranklist[-1][2]
        DEBUG_MSG("GetSameScoreRank week:%s,Type:%s,rank:%i" % (week,Type,rank) )
        return rank

    def GetWeekOwenrRank(self, Type, AccountName):
        zsetName = self.GetWeekNameByType(Type)
        if zsetName is not None:
            cur_rank = self.r.zrevrank(zsetName,AccountName)
            cur_rank = self.GetSameScoreRank('week',Type,cur_rank)
            cur_score = self.r.zscore(zsetName,AccountName) 
            Lastkey = self.Getkey(AccountName,Type,'Last')
            Bestkey = self.Getkey(AccountName,Type,'Best')
            Last_rank = self.r.hget(Lastkey, 'Last_rank')
            Last_score = self.r.hget(Lastkey, 'Last_score') 
            Best_score = self.r.hget(Bestkey, 'Best_score') 
            Best_rank = self.r.hget(Bestkey, 'Best_rank')
            DEBUG_MSG("GetWeekOwenrRank type:%s, AccountName: %s" % (Type, AccountName) )
            DEBUG_MSG("GetWeekOwenrRank %i,%s,%s,%s,%s,%s" % (cur_rank, cur_score, Last_rank , Last_score, Best_rank, Best_score) )
            return cur_rank, cur_score, Last_rank , Last_score, Best_rank, Best_score
        else:
            ERROR_MSG('Rank zsetName is none')
    
    #根据分数和排名算称号
    def GetTitle(self, Type, rank, score):
        if score is None:
            return None
        if Type == 'Diamond':
            return self.GetTitleByObj(d_game.DiamondRank, rank, score)
        elif Type == 'Pet':
            return self.GetTitleByObj(d_game.PetRank, rank, score)
        elif Type == 'Money':
            return self.GetTitleByObj(d_game.MoneyRank, rank, score)
        elif Type == 'Eglod':
            return self.GetTitleByObj(d_game.EglodRank, rank, score)
        return None

    def GetTitleByObj(self, d_gameObj, rank, score):
        if score == 0:
            return None
        #钻石消费优先条件
        lastID = len(d_gameObj)
        #DEBUG_MSG("score:%i,rank:%i,lastID:%i " % (score,rank,lastID) )
        for value in d_gameObj.values():
            if score >= value['Get']:
                DEBUG_MSG("value:%s" % str(value) )
                #最后的品级不受排名限制
                if value['ID'] == lastID:
                    return value
                if rank <= value['rank']:  
                    return value
                else:
                    ID = value['ID'] + 1 
                    return d_gameObj[ID]       
        return None

                    
            
 
