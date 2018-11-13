import KBEngine
from KBEDebug import *

class Account(KBEngine.Entity):
    def __init__(self):
        KBEngine.Entity.__init__(self)
        DEBUG_MSG("Account::__init__:%s." % (self.__dict__))
        #self.base.reqChangeData("dfaddfasdf", 1, 2)
    
    def onData(self, Data, DBID):
        print(str(Data), DBID)

    def onAddCardGroup(self,str1):
        print(str1)

    def OnAddCardGroup(self,str1):
        print(str1)

    def onReqAvatarList(self):
        print('dfa')

    def onRemoveAvatar(self):
        print('dfa')
    def onChangeAvatar(self):
        print('dfa')

   
    def onInitBattleField(self):
        print('dfa')
    def OnBattleResult(self):
        print('dfa')
    def onMarchMsg(self):
        print('dfa')
    def OnMarcherSum(self):
        print('dfa')
    def OnDelCarErr(self):
        print('dfa')
    def OnGetKz(self):
        print('dfa')
    def onInf(self):
        print('dfa')
    def onMoney(self,glod):
        print('onMoney:'+ str(glod))
    def onDiamond(self,glod):
        print('onDiamond:'+ str(glod))
    def onKglod(self,glod):
        print('onKglod:'+ str(glod))
    def onEglod(self, glod):
        print('onEglod:'+ str(glod))
    def onAccountCardData(self):
        print('dfa')
    def onbuycard(self):
        print('dfa')
    def onOpeningPackResult(self):
        print('dfa')

    def onChangeData(self, errmsg, name):
        DEBUG_MSG('onChangeData:%s,%s' % (errmsg, name))

    def battleResultClientDisplay(self):
        print('dfa')
    def gotoMain(self):
        print('dfa')
    def onGetPlayerSum(self):
        print('dfa')

    def onBindAccount(self):
        print('dfa')
        