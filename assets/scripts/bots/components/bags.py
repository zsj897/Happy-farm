import KBEngine

class bags(KBEngine.EntityComponent):
    def __init__(self):
        KBEngine.EntityComponent.__init__(self)
        #self.base.reqRechargeOrder(13,2)

    def onAttached(self, owner):
        pass

    def onBags(self, InfoList):
        print(str(InfoList) )

    def onBuyItem(self, ERR_MSG, ItemInfo):
        print(ERR_MSG,str(ItemInfo))


    def onAddItem(self, ItemInfo):
        print(str(ItemInfo) )

    def onDelItem(self, ItemInfo):
        print(str(ItemInfo) )

    def onRechargeOrder(self, stroder):
        print('onRechargeOrder:'+stroder)

    def onRecharge(self, Type, Value):
        print('onRecharge:%d,%d' % (Type,Value) )