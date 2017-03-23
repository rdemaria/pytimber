import datetime, time
import pytimber
from numpy import *
from pytimber.pagestore import *

db=pytimber.LoggingDB()

data1=db.get('LHC.BOFSU:BPM_CAL_MAPPING_ERRORS',time.time()-3600*24*30,time.time())

print([v.dtype for v in data1.values()[0][1]])

data2=db.get(['CPS.TGM:USER'], datetime.datetime(2016,8,3,8), datetime.datetime(2016,8,3,8,20))

print(data2.values()[0][1].dtype)

db=PageStore('test.db','testdata')

name='var'
idx=range(3)
rec=['123','232','123']
db.store_variable(name,idx,rec)
print(db.get_variable('var'))

rec=['123','232','333123441']
db.store_variable(name,idx,rec)
print(db.get_variable('var'))

rec=array(['123','232','333'],dtype='U')
db.store_variable(name,idx,rec)
print(db.get_variable('var'))

rec=[['123','123412'],['232','4241','fdasfa'],['333','434123']]

db.store_variable(name,idx,rec)
print(db.get_variable('var'))

db.delete()
