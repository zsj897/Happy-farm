import KBEngine
from KBEDebug import *

class Land(KBEngine.EntityComponent):
    def __init__(self):
        KBEngine.EntityComponent.__init__(self)
        KBEngine.callback( 1, self.update )

    def onAttached(self, owner):
        pass

    def update(self):
        self.base.reqAllLandInfo(0)

        KBEngine.callback(1, self.update)

    def onAllLandInfo(self, ERR_MSG,DBID,LandInfoList):
        DEBUG_MSG('onAllLandInfo:%s,%I', ERR_MSG,DBID )
    
    def onLandInfo(self, ERR_MSG, LAND_INFO):
        print(ERR_MSG,str(LAND_INFO))


    def onGJInfo(self,DBID, GJ_INFO, ISOK):
        print(DBID,GJ_INFO,ISOK)

    def onBuyLand(self, ERR_MSG):
        print(ERR_MSG)

    def onFriendBuyLand(self, ERR_MSG, messageLIst):
        print(ERR_MSG, str(messageLIst) )

    def onGiveLand(self,  message):
        print(str(message) )

    def onPlant(self, ERR_MSG, stealLIst):
        print(ERR_MSG, str(stealLIst) )

    def onfertilization(self, DBID, IsSteal):
        print(DBID, IsSteal)

    def onServerTime(self, ERR_MSG):
        print(ERR_MSG)

        