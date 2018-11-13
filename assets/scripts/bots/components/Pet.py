import KBEngine
from KBEDebug import *

class Pet(KBEngine.EntityComponent):
    def __init__(self):
        KBEngine.EntityComponent.__init__(self)
        self.base.reqPetSelfInfo()
        self.base.reqAllPetInfo(0)
        #self.base.reqPetMapInfo(1)
        #self.base.reqCatchPet('',4004,0)
        #self.base.reqPetCompound()

    def onAttached(self, owner):
        pass
    def onPetMapInfo(self, PetMapList):
        DEBUG_MSG('onPetMapInfo:%s' % str(PetMapList))
        
    def onPetSelfInfo(self, PetselfList):
        DEBUG_MSG('onPetSelfInfo:%s' % str(PetselfList))

    def onAllPetInfo(self, DBID,PetInfoList):
        DEBUG_MSG('onAllPetInfo:%s' % str(PetInfoList))

    def onPetHarvest(self, PetInfo):
        DEBUG_MSG('onPetHarvest:%s' % str(PetInfo))
      

    def onAddPet(self, PetInfo):
        DEBUG_MSG('onAddPet:%s' % str(PetInfo))
       
    def onDelPet(self, PetType):
        DEBUG_MSG('onDelPet:%i' % PetType)
       
    def onCatchPet(self,  ERR_MSG, arg1,arg2,arg3):
        DEBUG_MSG('onCatchPet:%s,%i,%i,%i' % (ERR_MSG, arg1,arg2,arg3))

    def onAward(self, Type,value):
        DEBUG_MSG('onAward:%i,%i' % (Type,value))

    def onPetCompound(self, ERR_MSG, arg1):
        DEBUG_MSG('onPetCompound:%s，%i' % (ERR_MSG, arg1))
        

  