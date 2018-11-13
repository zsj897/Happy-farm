import KBEngine
import time

#游戏金钱日志信息
def GameMoneyRecord(uid,DBID,MoneyType,ChangeValue,Des):
    createTime = int(time.time())
    sql = "insert into kbe_money_record(uid,DBID,MoneyType,ChangeValue,Des,createTime)  \
           value('"+uid+"',"+str(DBID)+','+str(MoneyType)+','+str(ChangeValue)+",'"+Des+"',"+str(createTime)+');'
    KBEngine.executeRawDatabaseCommand(sql,sqlcallback,10,"mysql2")

#游戏道具日志信息
def GameItemRecord(uid,DBID,ItemType,ChangeValue,Des):
    createTime = int(time.time())
    sql = "insert into kbe_Item_record(uid,DBID,ItemType,ChangeValue,Des,createTime)  \
           value('"+uid+"',"+str(DBID)+','+str(ItemType)+','+str(ChangeValue)+",'"+Des+"',"+str(createTime)+');'
    KBEngine.executeRawDatabaseCommand(sql,sqlcallback,11,"mysql2")

#游戏宠物记录
def GamePetRecord(uid,DBID,PetType,ChangeValue,Des):
    createTime = int(time.time())
    sql = "insert into kbe_Pet_record(uid,DBID,PetType,ChangeValue,Des,createTime)  \
           value('"+uid+"',"+str(DBID)+','+str(PetType)+','+str(ChangeValue)+",'"+Des+"',"+str(createTime)+');'
    KBEngine.executeRawDatabaseCommand(sql,sqlcallback,12,"mysql2")

def sqlcallback(result, rows, insertid, error):
    pass 
