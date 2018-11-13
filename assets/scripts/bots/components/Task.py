import KBEngine
from KBEDebug import *

class Task(KBEngine.EntityComponent):
    def __init__(self):
        KBEngine.EntityComponent.__init__(self)
        #self.base.reqTaskList()
        #self.base.reqFinishTask(1)
        
 
    def onAttached(self, owner):
        pass
        
    def onTaskList(self, TaskList):
        DEBUG_MSG('onTaskList:%s' % str(TaskList))
        
    def onTaskInfo(self, TaskInfo):
        DEBUG_MSG('onTaskInfo:%s' % str(TaskInfo))

    def onFinishTask(self, TaskInfo):
        DEBUG_MSG('onFinishTask:%s' % str(TaskInfo))

    def onTaskAward(self, errmsg, Type, Value):
        DEBUG_MSG('onTaskAward:%s, %i,%i' % (errmsg,Type, Value))
  