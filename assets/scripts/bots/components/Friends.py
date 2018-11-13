import KBEngine

class Friends(KBEngine.EntityComponent):
    def __init__(self):
        KBEngine.EntityComponent.__init__(self)

    def onAttached(self, owner):
        pass

    def onFriendList(self, InfoList):
        print(str(InfoList) )

    def onYaoShuStatus(self, ApplyInfo, AcceptInfo, time):
        print(str(ApplyInfo),str(AcceptInfo),time)


    def onApplyYaoShu(self, ERR_MSG):
        print(ERR_MSG)

    def onAcceptYaoShu(self, ERR_MSG):
        print(ERR_MSG)

    def onAllSysMessage(self, ERR_MSG, messageLIst):
        print(ERR_MSG, str(messageLIst) )

    def onSysMessage(self,  message):
        print(str(message) )

    def onSteal(self, ERR_MSG, stealLIst):
        print(ERR_MSG, str(stealLIst) )

    def onCheckCanSteal(self, DBID, IsSteal):
        print(DBID, IsSteal)

    def onCheckMessageCanSteal(self, ERR_MSG):
        print(ERR_MSG)

    def onOpenFriendList(self, ERR_MSG):
        print(ERR_MSG)

    def onReadMessage(self, ERR_MSG):
        print(ERR_MSG)
        
    def onYaoShu(self, ERR_MSG):
        print(ERR_MSG)
 