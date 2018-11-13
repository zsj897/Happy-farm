import KBEngine

class card(KBEngine.Entity):
    def __init__(self):
        KBEngine.Proxy.__init__(self)

    def onUse(self):
        print('dfa')
    def onEvent(self):
        print('dfa')
    def onAtt(self):
        print('dfa')
    def onChoose(self):
        print('dfa')