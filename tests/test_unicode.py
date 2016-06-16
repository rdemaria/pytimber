import os,sys,time,pickle
import pytimber,pagestore

db=pytimber.LoggingDB()

name='LHC.BOFSU:BPM_CAL_MAPPING_ERRORS'


data=db.get(name,'2016-03-01 18:32:46','2016-05-01 18:32:46')

mydb=pagestore.PageStore('unicode.db','unicode',maxpagesize=100)

mydb.store(data)

t,v=mydb.get(name)[name]


from numpy import *
a=[[u'1',u'2'],[u'22'],[u'1',u'2',u'44']]
data=map(array,a)


fh=open('out','wb')

lengths=map(len,a)









