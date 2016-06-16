import pytimber
db=pytimber.LoggingDB()

t1="2016-03-01 00:00:00.000"
t2="2016-04-03 00:00:00.000"

vn='LHC.BOFSU:EIGEN_FREQ_2_B1'
data=db.getStats(vn,t1,t2)
#data=db.getSize(vn,t1,t2)


