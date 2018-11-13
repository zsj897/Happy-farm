import KBEngine
import Functor
from KBEDebug import *
import d_game
import time
from GlobalDefine import *
from Poller import *

def GetConfigTask(TaskType):
    try:
        Info = d_game.TaskInfo[TaskType]
    except (IndexError, KeyError) as e:
        ERROR_MSG("GetConfigPetSelf error:%s," % (str(e)))
        return None
    return Info

class Task(KBEngine.EntityComponent):
    def __init__(self):
        KBEngine.EntityComponent.__init__(self)

    def onAttached(self, owner):
        #DEBUG_MSG("Task::onAttached(): owner=%i" % (owner.id))
        pass

    def onDetached(self, owner):
        #DEBUG_MSG("Task::onDetached(): owner=%i" % (owner.id))
        pass
        
    def onClientEnabled(self):
        """
        KBEngine method.
        该entity被正式激活为可使用， 此时entity已经建立了client对应实体， 可以在此创建它的
        cell部分。
        """
        DEBUG_MSG("Task[%i]::onClientEnabled:entities enable." % (self.ownerID))
        self._taskObjs = []
        self.BuildTaskObj()
        self.addTimer(1,60,TIMER_CD_TASK_4)
        self.InitClientData()

    def InitClientData(self):
        if hasattr(self,'client'):
            self.reqTaskList()
      
    def onClientDeath(self):
        """
		KBEngine method.
		客户端对应实体已经销毁
        """
        DEBUG_MSG("Task[%i].onClientDeath:" % self.ownerID)	

    def onTimer(self, id, userArg):
        if userArg == TIMER_CD_TASK_4:
            self.CheckTaskTime()

    def Component(self,name):
        return self.owner.getComponent(name)

    def BuildTaskObj(self):
        obj1 = ResetTask(self)
        self._taskObjs.append(obj1)
        obj2 = ComTask(self)
        self._taskObjs.append(obj2)
        self.AddTask()

    def GetTaskObj(self,TaskType):
        for obj in self._taskObjs:
            if obj.GetType() == TaskType:
                return obj
        return None
    
    def AddTask(self):
        taskTypes = []
        for taskInfo in self.Task:
            taskTypes.append(taskInfo['TaskType'])
            obj = self.GetTaskObj(taskInfo['TaskType'])
            if obj is not None:
                obj.SetTaskInfo(taskInfo) 
        for obj in self._taskObjs:
            if obj.GetType() in taskTypes:       
                continue
            taskInfo = {'TaskType':obj.GetType(), 'FinishNum':0, 'CanAward':0,'Endtime':0}
            self.Task.append(taskInfo)
            taskLen = len(self.Task)
            obj.SetTaskInfo(self.Task[taskLen-1]) 
    
    def CheckTaskTime(self):
        for obj in self._taskObjs:
            if obj.CheckResetTime():
                self.client.onTaskInfo(obj.GetTaskInfo())
                DEBUG_MSG("onTaskInfo:%s" % str(obj.GetTaskInfo()))
    """
    任务列表
    """
    def reqTaskList(self):
        self.client.onTaskList(self.Task)

    """
    完成任务
    """
    def reqFinishTask(self, TaskType):
        TaskObj = self.GetTaskObj(TaskType)
        if TaskObj is not None:
            TaskObj.FinishTask()
            self.client.onFinishTask(TaskObj.GetTaskInfo())
    """
    任务奖励
    """
    def reqTaskAward(self,TaskType,FinishNum):
        TaskObj = self.GetTaskObj(TaskType)
        if TaskObj is not None:
            TaskObj.GetTaskAward(FinishNum)



class TaskBase:
    def __init__(self,EntityComponent):
        self._task_info = {}
        self._TaskCom = EntityComponent

    def SetTaskInfo(self, TaskInfo):
        self._task_info = TaskInfo
        
    def GetTaskInfo(self):
        return self._task_info
   
    def FinishTask(self):
        self._task_info['FinishNum'] += 1
    
    def CheckResetTime(self):
        return False

"""
重置任务,分享任务
"""
class ResetTask(TaskBase):
    def __init__(self,EntityComponent):
        TaskBase.__init__(self,EntityComponent)  
        
    #必须实现
    def GetType(self):
        return 1

    def GetAwardConfig(self, index):
        Type = 0
        value = 0
        d_TaskInfo = GetConfigTask(1)
        if d_TaskInfo is not None:
            Type = d_TaskInfo['awardType'][index]
            value = d_TaskInfo['awardValue'][index]
        return [{'Type':Type,'value':value}]

    #必须实现
    def GetTaskAward(self, FinishNum):
        if FinishNum == 1:
            if self._task_info['CanAward'] & 0b100:
                self._task_info['CanAward'] &= 0b011
                self.TaskAward('成功',self.GetAwardConfig(0) ,FinishNum)
                return
        if FinishNum == 3:
            if self._task_info['CanAward'] & 0b010:
                self._task_info['CanAward'] &= 0b101
                self.TaskAward('成功',self.GetAwardConfig(1),FinishNum)
                return
        if FinishNum == 5:
            if self._task_info['CanAward'] & 0b001:
                self._task_info['CanAward'] &= 0b110
                self.TaskAward('成功',self.GetAwardConfig(2),FinishNum)
                return

    def TaskAward(self, errMsg, AwardList, FinishNum):
        for AwardInfo in AwardList:
            self._TaskCom.Component("bags").AddItem(AwardInfo['Type'], AwardInfo['value'], '任务奖励,任务类型:%d' % self.GetType())
        self._TaskCom.client.onTaskAward(errMsg,self.GetType(),FinishNum) 
        self._TaskCom.client.onTaskInfo(self._task_info)

    def SetTaskInfo(self, TaskInfo):
        super().SetTaskInfo(TaskInfo)
        if self._task_info['Endtime'] == 0:
            self._task_info['Endtime'] = self.GetNextDay()

    def FinishTask(self):
        super().FinishTask()
        self.CheckAward()

    def CheckAward(self):
        FinishNum = self._task_info['FinishNum']
        if FinishNum == 1:
            self._task_info['CanAward'] |= 0b100
        if FinishNum == 3:
            self._task_info['CanAward'] |= 0b010
        if FinishNum == 5:
            self._task_info['CanAward'] |= 0b001
        DEBUG_MSG("CheckAward:%d" % self._task_info['CanAward'])

    def CheckResetTime(self):
        nowTime = int(time.time() )
        if nowTime > self._task_info['Endtime']:
            self.Reset()
            return True
        return False
        
    def Reset(self):
        self._task_info['FinishNum'] = 0
        self._task_info['CanAward'] = 0
        self._task_info['Endtime'] = self.GetNextDay()
        DEBUG_MSG("Reset:%s" % str(self._task_info) )
        
    #获得下一天的零点零分时间戳
    def GetNextDay(self):
        now_time = int(time.time()) 
        return now_time - now_time % 86400 + time.timezone + 86400
	

"""
公众号任务
"""
class ComTask(TaskBase):
    def __init__(self,EntityComponent):
        TaskBase.__init__(self,EntityComponent) 

    #必须实现
    def GetType(self):
        return 2

    def GetAwardConfig(self):
        AwardList = []
        d_TaskInfo = GetConfigTask(self.GetType())
        if d_TaskInfo is not None:
            for index,Type in enumerate(d_TaskInfo['awardType']):
                AwardList.append({'Type':Type, 'value':d_TaskInfo['awardValue'][index] })
        return AwardList

     #必须实现
    def GetTaskAward(self, FinishNum):
        #发送公众号验证
        g_Poller.CheckBindWeChat(self._TaskCom.owner.AccountName(), Functor.Functor(self.OnGetTaskAward,FinishNum ) )

    def OnGetTaskAward(self,FinishNum, Result):
        if Result['code'] == 1:
            if self._task_info['CanAward'] == 0:
                self.TaskAward('成功', self.GetAwardConfig(),FinishNum)
                self._task_info['CanAward'] = 1
        else:
            self.TaskAward('当前账号尚未参加活动', [],FinishNum)
            DEBUG_MSG("OnGetTaskAward:%s" % Result['info'] )

    def TaskAward(self, errMsg, AwardList, FinishNum):
        for AwardInfo in AwardList:
            self._TaskCom.Component("bags").AddItem(AwardInfo['Type'], AwardInfo['value'], '任务奖励,任务类型:%d' % self.GetType())
        self._TaskCom.client.onTaskAward(errMsg,self.GetType(),FinishNum)
        self._TaskCom.client.onTaskInfo(self._task_info)



    