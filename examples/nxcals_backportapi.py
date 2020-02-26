import cmmnbuild_dep_manager

import pytimber
db=pytimber.LoggingDB(source="nxcals")
db.search("%LHC%LUMI%")

t1="2018-11-27 01:00:00.000"
t2="2018-11-27 01:10:00.000"
out=db.get('LHC.BLM.LIFETIME:LUMINOSITY_LOSS',t1,t2)
ts,val=db.get('LHC.BLM.LIFETIME:LUMINOSITY_LOSS',t1,t2)

t1="2018-11-27 01:00:00.000"
t2="2018-11-27 01:10:00.000"
ts,val=db.get('LHC.BQBBQ.CONTINUOUS.B2:ACQ_DATA_H',t1,t2)



nxcals=pytimber.NXCals()

import jpype

mgr=nxcals._mgr


ServiceBuilder=nxcals._cern.nxcals.api.backport.client.service.ServiceBuilder

ts=ServiceBuilder.getInstance().createTimeseriesService()
md=ServiceBuilder.getInstance().createMetaService()



