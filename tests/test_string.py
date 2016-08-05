import datetime, time
import pytimber


db=pytimber.LoggingDB()

data1=db.get('LHC.BOFSU:BPM_CAL_MAPPING_ERRORS',time.time()-3600*24*30,time.time())

print([v.dtype for v in data1.values()[0][1]])

data2=db.get(['CPS.TGM:USER'], datetime.datetime(2016,8,3,8), datetime.datetime(2016,8,3,8,20))

print(data2.values()[0][1].dtype)
