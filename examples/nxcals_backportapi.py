import pytimber

cals = pytimber.LoggingDB(source="ldb")
nxca = pytimber.LoggingDB(source="nxcals")

t1 = "2018-11-27 01:00:00.000"
t2 = "2018-11-27 01:10:00.000"
name = "LHC.BLM.LIFETIME:LUMINOSITY_LOSS"
ts1, ds1 = cals.get(name, t1, t2)[name]
ts2, ds2 = nxca.get(name, t1, t2)[name]


t1 = "2016-08-07 17:27:00"
t2 = "2016-08-07 17:37:00"
name = "LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H"

ts1, ds1 = cals.get(name, t1, t2)[name]
ts2, ds2 = nxca.get(name, t1, t2)[name]


cals.search("%LHC%LUMI%")
nxca.search("%LHC%LUMI%")
