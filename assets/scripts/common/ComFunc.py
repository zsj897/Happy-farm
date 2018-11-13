import KBEngine
from KBEDebug import *
import Functor
import random
import copy

# true：中奖  false: 未中奖
def IsProbability( prob):
	result = random.randint(1, 10000)
	if result > prob:
		return False,result
	return True,result

#根据列表随机，返回列表中的某值
def RandByList(IDList, ProbList):
	sum_prob = 0
	ran = random.randint(1,10000)
	for ID, Prob in zip(IDList, ProbList):
		sum_prob += int(Prob)
		if ran < sum_prob :
			break
	return int(ID)

#随机宠物位置数据
#PetXYZList：生成宠物的列表 IDList：随机的ID列表 PetTotalNum:总数
def RandPetXYZ(PetXYZList,IDList,PetTotalNum,ProbList=None):
    if not IDList:
        return
    while PetTotalNum > 0:
        PetType = 0
        if ProbList is None:
            index = random.randint(0,len(IDList)-1)
            PetType = int(IDList[index])
        else:
            PetType = RandByList(IDList,ProbList)
        PetTotalNum -= 1
        IsFind = False
        for PetXYZ in PetXYZList:
            if PetXYZ['PetType'] == PetType:
                PetXYZ['PetNum'] += 1
                IsFind = True
                break
        if not IsFind:
            PetXYZList.append({'PetType':PetType,'PetNum':1})

# 生产器
class Generator:
    def __init__(self):
        self.UnitList = []
        self.SameCount = 0
        self.LastDBID = 0

    def Set(self, DBID, CallBack, *args):
        arglist = []
        for arg in args:
            arglist.append(arg)
        Unit = {'DBID':DBID, 'CallBack':CallBack, 'arglist':arglist}
        if self.check(Unit):
            self.UnitList.append(Unit)
            INFO_MSG("Generator Set:%s" % str(Unit) )
            INFO_MSG("Generator Check:%i,%i" % (self.LastDBID,self.SameCount) )
    
    def check(self,Unit):
        if self.LastDBID == Unit['DBID']:
            self.SameCount += 1
        else:
            self.SameCount = 0
        if self.SameCount >= 5:
            return False
        self.LastDBID = Unit['DBID']
        return True

    def Get(self):
        if self.UnitList:
            DBID = self.UnitList[0]['DBID'] 
            CallBack = self.UnitList[0]['CallBack'] 
            arglist = self.UnitList[0]['arglist']
            if len(arglist) == 0:
                KBEngine.createEntityFromDBID("Account", DBID, Functor.Functor(CallBack) )
            elif len(arglist) == 1:
                KBEngine.createEntityFromDBID("Account", DBID, Functor.Functor(CallBack, arglist[0]) )
            elif len(arglist) == 2:
                KBEngine.createEntityFromDBID("Account", DBID, Functor.Functor(CallBack, arglist[0],arglist[1]) )
            elif len(arglist) == 3:
                KBEngine.createEntityFromDBID("Account", DBID, Functor.Functor(CallBack, arglist[0],arglist[1],arglist[2]) )
            elif len(arglist) == 4:
                KBEngine.createEntityFromDBID("Account", DBID, Functor.Functor(CallBack, arglist[0],arglist[1],arglist[2],arglist[3]) )
            else:
                ERROR_MSG("超出范围，arglist 大于4 ")
            INFO_MSG("Generator Get:%s" % str(self.UnitList[0]) )
            del self.UnitList[0]
            
g_Generator = Generator()