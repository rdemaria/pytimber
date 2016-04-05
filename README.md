# pytimber

Python wrapping of CALS API.

## Installation

Install a Python distribution (e.g. Anaconda) then:

```sh
pip install git+https://gitlab.cern.ch/scripting-tools/cmmnbuild-dep-manager.git
pip install git+https://github.com/rdemaria/pytimber.git
pip install git+https://github.com/rdemaria/pagestore.git
```

_Note: cmmnbuild-dep-manager is optional but is required for compatibility with
other CERN packages using JPype (such as PyJapc)_

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
