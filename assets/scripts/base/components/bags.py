import KBEngine
import Functor
from KBEDebug import *
import d_game
import time
from GameRecord import *
from Poller import *
import math

ERR_ITEM_INFO = {'ItemType':0, 'ItemNum':0}

class bags(KBEngine.EntityComponent):
    def __init__(self):
        KBEngine.EntityComponent.__init__(self)
    
    def onAttached(self, owner):
        #DEBUG_MSG("bags::onAttached(): owner=%i" % (owner.id))
        pass

    def onDetached(self, owner):
        #DEBUG_MSG("bags::onDetached(): owner=%i" % (owner.id))
        pass

    def onClientEnabled(self):
        """
        KBEngine method.
        该entity被正式激活为可使用， 此时entity已经建立了client对应实体， 可以在此创建它的
        cell部分。
        """
        DEBUG_MSG("bags[%i]::onClientEnabled:entities enable." % (self.ownerID))
        self.InitClientData()
        
    def InitClientData(self):
        if hasattr(self,'client'):
            self.reqBags()

    def onClientDeath(self):
        """
		KBEngine method.
		客户端对应实体已经销毁
        """
        DEBUG_MSG("bags[%i].onClientDeath:" % self.ownerID)	

    def onTimer(self, id, userArg):
        """
		KBEngine method.
		使用addTimer后， 当时间到达则该接口被调用
		@param id		: addTimer 的返回值ID
		@param userArg	: addTimer 最后一个参数所给入的数据
        """

    def Component(self,name):
        return self.owner.getComponent(name)

    def GetConfigShop(self, shopID):
        try:
            Info = d_game.shop[shopID]
        except (IndexError, KeyError) as e:
            ERROR_MSG("GetConfigShop error:%s, shopID:%i" % (str(e), shopID))
            return None
        return Info
    
    def GetItemInfo(self, ItemType):
        for ItemInfo in self.Bags:
            if ItemInfo['ItemType'] == ItemType:
                return ItemInfo
        return {'ItemType':ItemType,'ItemNum':0}
    
    def	reqBuyItem(self,shopID,num = 1):
        DEBUG_MSG("reqBuyItem:%i" % shopID)
        if num < 1:
            self.client.onBuyItem("购买数量错误", ERR_ITEM_INFO)
            return -1
        #判断金钱
        shopInfo = self.GetConfigShop(shopID)
        if shopInfo is None:
            self.client.onBuyItem('错误的shopID',ERR_ITEM_INFO)
            return -2
        priceType = shopInfo['priceType']
        Value = shopInfo['Value']
        errcode=self.owner.ChangeBaseData(priceType, -(Value*num),'减少,购买商品:%d' % shopID)
        if errcode < 0:
            self.client.onBuyItem("金币不够",ERR_ITEM_INFO)
            return -3 
        ItemNum = shopInfo['Num']*num
        ItemType = shopInfo['ItemID']
        errcode=self.AddItem(ItemType, ItemNum,'商店购买:%d' % shopID)
        if errcode < 0:
            self.client.onBuyItem("错误的物品ID",ERR_ITEM_INFO)
            return -4
        ItemInfo = self.GetItemInfo(ItemType)
        self.client.onBuyItem("成功", ItemInfo)
        #购买记录
        d_ItemInfo = self.GetConfigItem(ItemType)
        MoneyName = self.GetMoneyNameByType(priceType)
        ItemNumName = self.GetNumName(ItemType,ItemNum)
        self.Component("Friends").SYSMessage(0, 4002, int(time.time()) , Value*num, MoneyName, ItemNumName, d_ItemInfo['ItemName'])
        return 0

    #请求充值订单
    def reqRechargeOrder(self, shopID, device_type):
        shopInfo = self.GetConfigShop(shopID)
        if shopInfo is None:
            return
        diamond = shopInfo['Num']
        if self.owner.Data['FirstRecharge'] == 0:
            rate = math.ceil(diamond * 0.1)
            diamond += rate
            DEBUG_MSG("first Recharge:%d,%d" % (rate, diamond)	)
        g_Poller.GetRechargeOrder(device_type,diamond,shopInfo['Value'],self.owner.AccountName(),self.RechargeCall)
        

    def RechargeCall(self,strResult):
        self.client.onRechargeOrder(strResult)

    def GetMoneyNameByType(self, priceType):
        if priceType == 1:
            return '游戏币'
        elif priceType == 2:
            return '钻石'
        elif priceType == 3:
            return '开元通宝'
        elif priceType == 4:
            return 'E币'
        return ''
    def GetNumName(self, ItemType, ItemNum):
        strNum = str(ItemNum)
        if ItemType == 1001 or ItemType == 1002:
            return strNum + "颗"
        if ItemType == 2001 or ItemType == 2002:
            return strNum + "包"
        if ItemType == 5001 or ItemType == 5002:
            return ""
        return strNum + ""

    def reqBags(self):
        DEBUG_MSG("reqBags:%s" % str(self.Bags))	
        self.client.onBags(self.Bags)

    #添加物品 IsUse：aaaa是否立即使用  
    def AddItem(self, ItemType, num , Des):
        try:
            Item = d_game.ItemInfo[ItemType]
        except (IndexError, KeyError) as e:
            ERROR_MSG("AddItem error:%s" % str(e))
            return -1 #错误的物品ID
        IsOverlay = Item['IsOverlay']
        IsUse = Item['IsUse']
        if IsOverlay == 1:
            self.AddItem2(ItemType,num,IsUse)
        else:
            self.AddItem3(ItemType,num,IsUse)
        #游戏物品日志记录
        GameItemRecord(self.owner.AccountName(),self.owner.databaseID,ItemType,num,Des)
        return 0

    def AddItem2(self, ItemType, num = 1, IsUse = 0):
        for Item in self.Bags:
            if Item['ItemType'] == ItemType:
                Item['ItemNum'] += num
                if hasattr(self,'client'):
                    self.client.onAddItem(Item)
                if IsUse == 1:
                    self.UseItem(Item['ItemType'],num=num,Des='添加道具时使用') 
                return
        self.AddItem3(ItemType,num,IsUse)
 
    def AddItem3(self, ItemType, num = 1, IsUse = 0): 
        Item = {'ItemType':ItemType,"ItemNum":num }
        self.Bags.append(Item)        
        if IsUse == 1:
            err = self.UseItem(Item['ItemType'],num=num,Des='添加道具时使用')
            INFO_MSG("add UseItem: "+str(err))
        if hasattr(self,'client'):
            self.client.onAddItem(Item)

    def IsOverlay(self, ItemType):
        d_Item = self.GetConfigItem(ItemType)
        if d_Item is not None and d_Item['IsOverlay'] == 1:
            return True
        return False
    #删除物品
    def DelItem(self, ItemType, num = 1):
        for index, item in enumerate(self.Bags):
            if item['ItemType'] == ItemType:
                if self.IsOverlay(ItemType): #如果可以叠加
                    return self.DelItem2(item,num)
                else:
                    return self.DelItem3(index)
        return -1

    def DelItem2(self, item, num = 1):
        if item['ItemNum'] >= num:
            item['ItemNum'] -= num
            if hasattr(self,'client'):
                self.client.onDelItem(item)
            INFO_MSG("DelItem2:%i,%i" % (self.ownerID, item['ItemNum'] ) )
            return 0
        return -1

    def DelItem3(self, index):
        self.Bags.pop(index)
        INFO_MSG("DelItem3:%i,%s" % (self.ownerID, str(self.Bags) ) )
        return 0
        
    #使用物品 (ArgDict参数字典)
    def UseItem(self, ItemType, ArgDict = None, num = 1,Des=''):
        for Item in self.Bags:
            if Item['ItemType'] == ItemType:
                #该物品是否可以使用
                err = self.CanUse(ItemType, ArgDict, num)
                if err != 0:
                    INFO_MSG("CanUse error:%i" % (err))
                    return -1
                #删除背包
                if self.DelItem(ItemType, num) != 0:
                    return -2
                #使用效果
                self.ItemEffect(ItemType, ArgDict, num)  
                #游戏物品日志记录
                Des = '使用道具,'+ Des
                GameItemRecord(self.owner.AccountName(),self.owner.databaseID,ItemType,num,Des)
                return 0
        return -3

  
    def GetConfigItem(self, ItemID):
        try:
            Info = d_game.ItemInfo[ItemID]
        except (IndexError, KeyError) as e:
            ERROR_MSG("GetConfigItem error:%s, ItemID:%i" % (str(e), ItemID))
            return None
        return Info
    def GetConfigItemUse(self, UseID):
        try:
            Info = d_game.ItemUse[UseID]
        except (IndexError, KeyError) as e:
            ERROR_MSG("GetConfigItemUse error:%s, UseID:%i" % (str(e), UseID))
            return None
        return Info
    def GetConfigItemEffect(self, EffectID):
        try:
            Info = d_game.ItemEffect[EffectID]
        except (IndexError, KeyError) as e:
            ERROR_MSG("GetConfigItemEffect error:%s, EffectID:%i" % (str(e), EffectID))
            return None
        return Info
    """
    物品是否可以使用
    """
    def CanUse(self, ItemType, ArgDict,num):
        d_ItemInfo = self.GetConfigItem(ItemType)
        if d_ItemInfo is None:
            return -1
        UseIDList = d_ItemInfo['CanUseID']
        if d_ItemInfo['ItemType'] == '种子':
            return self.CheckZhongZhi(UseIDList, ArgDict )
        elif d_ItemInfo['ItemType'] == '化肥':
            return self.CheckHuaFei(UseIDList, ArgDict ,num)
        return 0

    #种子
    def CheckZhongZhi(self, UseIDList, ArgDict):
        #INFO_MSG("_CheckHuaFei enable." % (self.ownerID))
        for UseID in UseIDList:
            d_ItemUse = self.GetConfigItemUse(UseID)
            if d_ItemUse is None:
                return -2
            if d_ItemUse['UseType'] == '可以使用的土地编号':
                LandType = ArgDict['LandType']
                if LandType not in d_ItemUse['Value']:
                    return -3
            else:
                return -4
        return 0
    #化肥
    def CheckHuaFei(self, UseIDList, ArgDict,num):
        #INFO_MSG("_CheckHuaFei enable." % (self.ownerID))
        for UseID in UseIDList:
            d_ItemUse = self.GetConfigItemUse(UseID)
            if d_ItemUse is None:
                return -2
            if d_ItemUse['UseType'] == '化肥可以使用的阶段':
                stageName = ArgDict['stageName']
                if stageName not in d_ItemUse['StrValue']:
                    print(stageName,d_ItemUse)
                    return -3
            elif d_ItemUse['UseType'] == '使用数量':
                if d_ItemUse['Value'][0] != num:
                    print('化肥使用限制%d,%d' % (d_ItemUse['Value'][0],num) )
                    return -4
            else:
                return -5
        return 0
    """
    物品效果
    """
    def ItemEffect(self, ItemType, ArgDict = None, num = 1):
        d_ItemInfo = self.GetConfigItem(ItemType)
        if d_ItemInfo is None:
            return -1
        EffectIDList = d_ItemInfo['EffectID']

        if d_ItemInfo['ItemType'] == '种子':
            pass
        elif d_ItemInfo['ItemType'] == '化肥':
            self.HuaFeiEffect(EffectIDList, ItemType, ArgDict)
        elif d_ItemInfo['ItemType'] == '管家':
            self.StewardEffect(EffectIDList, ItemType, ArgDict)
        elif d_ItemInfo['ItemType'] == '货币':
            self.MoneyEffect(ItemType, num)
        elif d_ItemInfo['ItemType'] == '宠物道具':
            self.PetItem(ItemType,ArgDict)
    #种子
    def SeedEffect(self, ItemType, ArgDict):
        pass
    #化肥
    def HuaFeiEffect(self, EffectIDList, ItemType, ArgDict):
        for EffectID in EffectIDList:
            d_ItemEffect = self.GetConfigItemEffect(EffectID)
            if d_ItemEffect is None:
                return 
            if d_ItemEffect['EffectType'] == '缩短种子成长时间':
                self.Component("Land").fertilization(ArgDict['LandId'],d_ItemEffect['Value']*60)
            if d_ItemEffect['EffectType'] == '直接到下一个阶段':
                self.Component("Land").fertilization2(ArgDict['LandId'])
                
    #管家
    def StewardEffect(self, EffectIDList, ItemType, ArgDict):
        for EffectID in EffectIDList:
            d_ItemEffect = self.GetConfigItemEffect(EffectID)
            if d_ItemEffect is None:
                return 
            if d_ItemEffect['EffectType'] == '管家持续时间':
                nowtime = int(time.time())	
                self.Component("Land").SetGJ(ItemType, nowtime+d_ItemEffect['Value']*60)
                self.Component('Friends').ClearMessage('管家日志')
      
    #货币
    def MoneyEffect(self, ItemType, num):
        self.owner.ChangeBaseData(ItemType, num, '增加，商店购买货币')

    #宠物道具
    def PetItem(self, ItemType,ArgDict):
        for EffectID in EffectIDList:
            s = self.GetConfigItemEffect(EffectID)
            if d_ItemEffect is None:
                return 
            if d_ItemEffect['EffectType'] == '提高抓捕概率':
                Addprob = d_ItemEffect['Value']
                self.Component("Pet").CatchSpePet2(ArgDict['position'],ArgDict['PetType'],ItemType,Addprob)
    