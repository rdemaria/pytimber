import pytimber

nxcals = pytimber.NXCals()


### High level API

lst = nxcals.searchVariable("LHC%BCT%INT%")
print(lst)

t1 = "2018-05-23 00:05:54.500"
t2 = "2018-05-23 00:06:54.500"

ts, val = nxcals.getVariable("LHC.BCTFR.A6R4.B1:BEAM_INTENSITY", t1, t2)


### Spark rows lowlevel access

t1 = "2018-05-23 00:05:54.500"
t2 = "2018-05-23 00:06:54.500"

ds = nxcals.getVariable("LHC.BCTFR.A6R4.B1:BEAM_INTENSITY", t1, t2, output="spark")
rows = (
    ds.select("nxcals_timestamp", "nxcals_value")
    .na()
    .drop()
    .sort("nxcals_timestamp")
    .collect()
)
ts, val1 = list(zip(*[(row.get(0) / 1000.0, row.get(1)) for row in rows]))

arr = nxcals.rows2array(rows)
pd = nxcals.rows2pandas(rows)

### Spark rows lowlevel access

df = (
    nxcals.DataQuery.byEntities()
    .system("WINCCOA")
    .startTime("2018-06-15 00:00:00.000")
    .endTime("2018-06-15 12:00:00.000")
    .entity()
    .keyValue("variable_name", "MB.C16L2:U_HDS_3")
    .buildDataset()
)

rows = df.collect()
arr = nxcals.rows2array(rows)
pd = nxcals.rows2pandas(rows)

df = (
    nxcals.DataQuery.byEntities()
    .system("CMW")
    .startTime("2018-04-29 00:00:00.000")
    .endTime("2018-04-30 00:00:00.000")
    .entity()
    .keyValue("device", "LHC.LUMISCAN.DATA")
    .keyValue("property", "CrossingAngleIP1")
    .buildDataset()
)

rows = df.collect()
arr = nxcals.rows2array(rows)
pd = nxcals.rows2pandas(rows)

df = (
    nxcals.DataQuery.byEntities()
    .system("CMW")
    .startTime("2018-04-29 00:00:00.000")
    .endTime("2018-04-30 00:00:00.000")
    .entity()
    .keyValue("device", "LHC.LUMISCAN.DATA")
    .keyValueLike("property", "CrossingAngleIP%")
    .buildDataset()
)

rows = df.collect()
arr = nxcals.rows2array(rows)
pd = nxcals.rows2pandas(rows)


# basic query
dataset = (
    nxcals.DataQuery.byEntities()
    .system("CMW")
    .startTime("2018-05-23 00:05:54.500")
    .endTime("2018-05-23 00:06:54.500")
    .entity()
    .keyValue("device", "ZT10.QFO03")
    .keyValue("property", "Acquisition")
    .buildDataset()
)

dataset.printSchema()

rows = (
    dataset.select("cyclestamp", "current")
    .orderBy("cyclestamp", ascending=False)
    .collect()
)
rows = dataset.orderBy("cyclestamp", ascending=False).collect()
pd = nxcals.rows2pandas(rows)


for row in data:
    print(list(row.values()))

# from manual
import numpy

ref_time = numpy.datetime64("2018-05-23T00:05:54.500")
interval_start = ref_time - numpy.timedelta64(1, "D")

ref_time = str(ref_time).replace("T", " ")
interval_start = str(ref_time).replace("T", " ")


df = (
    nxcals.DevicePropertyQuery.system("CMW")
    .startTime(interval_start)
    .endTime(ref_time)
    .entity()
    .device("ZT10.QFO03")
    .property("Acquisition")
    .buildDataset()
    .select("cyclestamp", "current")
    .orderBy("cyclestamp", ascending=False)
    .limit(1)
)

df.show()


# basic query
df = (
    nxcals.VariableQuery.system("CMW")
    .variable("CPS.TGM:CYCLE")
    .startTime("2018-06-15 23:00:00.000")
    .endTime("2018-06-16 00:00:00.000")
    .buildDataset()
)


# basic query
df = (
    nxcals.VariableQuery.system("CMW")
    .startTime("2018-04-29 00:00:00.000")
    .endTime("2018-04-30 00:00:00.000")
    .variableLike("%I_MEAS%")
    .buildDataset()
)

data = df.collect()
list(data[0].values())

nxcals._cern.nxcals.service.client.api.VariableService.findBySystemNameAndVariableNameLike(
    "CMW", "%I_MEAS%"
)

# create certificate

pytimber.NXCals.create_certs()


# device
nxcals.searchDevice("%RSF2%")
t1 = "2018-06-15 23:00:00.000"
t2 = "2018-06-15 23:01:00.000"

ds = (
    nxcals.DevicePropertyQuery.system("CMW")
    .startTime(t1)
    .endTime(t2)
    .entity()
    .device("RPMBB.UA87.RSF2.A81B1")
    .property("SUB_51")
    .buildDataset()
)

ds.printSchema()
rows = ds.select("acqStamp", "I_MEAS").orderBy("acqStamp", ascending=False).na().drop()
[(r.get(0), r.get(1)) for r in rows.collect()]

ts, val = nxcals.getVariable("RPMBB.UA87.RSF2.A81B1:I_MEAS", t1, t2)


# simple comparison
import pytimber

t1 = "2018-06-15 23:00:00.000"
t2 = "2018-06-15 23:01:00.000"
vname = "RPMBB.UA87.RSF2.A81B1:I_MEAS"
cals = pytimber.LoggingDB()
print(cals.getVariable(vname, t1, t2))
nxcals = pytimber.NXCals()
print(nxcals.getVariable(vname, t1, t2))


# from doc
import time
import numpy as np

nxcals = pytimber.NXCals()
start = time.time()
ds = (
    nxcals.DevicePropertyQuery.system("CMW")
    .startTime("2018-11-27 01:00:00.000")
    .endTime("2018-11-27 01:10:00.000")
    .entity()
    .parameter("LHC.BQ.GATED.B1/Measurement")
    .buildDataset()
    .sort("acqStamp")
    .select("acqStamp", "lastRawDataH")
    .na()
    .drop()
)
print(f"Time elapsed {time.time()-start} seconds")
rows = ds.limit(10).collect()
print(f"Time elapsed {time.time()-start} seconds")
ts0 = np.array([row.getAs("acqStamp") for row in rows]) / 1e9
print(f"Time elapsed {time.time()-start} seconds")
data0 = np.array([np.array(row.getAs("lastRawDataH").getList(0)) for row in rows])
print(f"Time elapsed {time.time()-start} seconds")
print(f"ts0: {ts0.shape}; data0: {data0.shape}")

t1 = "2018-11-27 01:00:00.000"
t2 = "2018-11-27 01:10:00.000"
ts, val = nxcals.getVariable("LHC.BQBBQ.CONTINUOUS.B2:ACQ_DATA_H", t1, t2)

list(val.getAs("nxcals_value").getList(0))


import cmmnbuild_dep_manager

import pytimber

db = pytimber.LoggingDB(source="nxcals")
db.search("%LHC%LUMI")


t1 = "2018-11-27 01:00:00.000"
t2 = "2018-11-27 01:10:00.000"
ts, val = db.get("LHC.BQBBQ.CONTINUOUS.B2:ACQ_DATA_H", t1, t2)


nxcals = pytimber.NXCals()

import jpype

mgr = nxcals._mgr


ServiceBuilder = nxcals._cern.nxcals.api.backport.client.service.ServiceBuilder

ts = ServiceBuilder.getInstance().createTimeseriesService()
md = ServiceBuilder.getInstance().createMetaService()
