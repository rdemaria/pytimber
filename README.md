# pytimber

Python wrapping of CALS API.

## Installation

Install a Python distribution (e.g. Anaconda) and a recent Java version (1.8) then:

```sh
pip install git+https://github.com/rdemaria/pytimber.git
```

## Usage

Import:

```python
import pytimber
ldb = pytimber.LoggingDB()
```

Search for variables:

```python
print(ldb.search('HX:BETA%'))
```

Get data:

```python
t1 = '2015-05-13 00:00:00.000'
t2 = '2015-05-15 00:00:00.000'
d = ldb.get('HX:FILLN', t1, t2)
print(d)
```

```python
t1 = '2015-05-13 12:00:00.000'
t2 = '2015-05-13 12:00:01.000'
d = ldb.get('LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H', t1, t2)
print(d)
```

Explore variable hierarchies:

```python
ldb.tree
print(dir(ldb.tree))
print(ldb.tree.LHC.Collimators.BPM.bpmColl.get_vars())
```

Get data for a particular LHC fill:

```python
fill = ldb.getLHCFillData(4760)
t1 = fill['startTime']
t2 = fill['endTime']
d = ldb.get('LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H', t1, t2)
print(d)
```

Find all fill number in the last 48 hours that contained a ramp:

```python
t2 = datetime.datetime.now()
t1 = t2 - datetime.timedelta(hours=48)
fills = ldb.getLHCFillsByTime(t1, t2, beam_modes="RAMP")
print([f['fillNumber'] for f in fills])
```

By default all times are returned as Unix timestamps. If you pass
`unixtime=False` to `get()`, `getAligned()`, `getLHCFillData()` or
`getLHCFillsByTime()` then `datetime` objects are returned instead.

## Usage with PageStore

Installation (assuming pytimber is already installed):

```sh
pip install git+https://github.com/rdemaria/pagestore.git
```

Usage example:

```python
import pagestore

mydb=pagestore.PageStore("mydata.db","./datadb")

t1=time.mktime(time.strptime('Fri Apr 25 00:00:00 2016'))
mydb.store(ldb.get('%RQTD%I_MEAS', t1, t1+60))
mydb.store(ldb.get('%RQTD%I_MEAS', t1+60, t1+120))

mydata=mydb.get('RPMBB.UA47.RQTD.A45B2:I_MEAS',t1+90,t1+110)
data=ldb.get('RPMBB.UA47.RQTD.A45B2:I_MEAS',t1+90,t1+110)
for k in data:
  print(mydata[k][0]-data[k][0])
  print(mydata[k][1]-data[k][1])

```

## Installation with cmmnbuild-dep-manager

cmmnbuild-dep-manager provides automatic resolution of Java dependencies for
CERN packages. It is required to use pytimber with other CERN libraries, such
as PyJapc.

The installation must be done from a machine connected to the CERN network:

```sh
pip install git+https://gitlab.cern.ch/scripting-tools/cmmnbuild-dep-manager.git
pip install git+https://github.com/rdemaria/pytimber.git
```

pytimber is automatically registered with cmmnbuild-dep-manager during
installation and the necessary jars are downloaded.

Note: if cmmnbuild-dep-manager is installed _after_ pytimber, it is necessary
to manually register it and download the jars:

```python
import cmmnbuild_dep_manager
mgr = cmmnbuild_dep_manager.Manager()
mgr.install('pytimber')
```
