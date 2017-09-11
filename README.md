# pytimber

Python wrapping of the [CERN Accelerator Logging Service][cals] (CALS) API.

[cals]: https://wikis.cern.ch/display/CALS/CERN+Accelerator+Logging+Service

## Installation

Install a Python distribution (e.g. [Anaconda][]) and a recent Java version
(1.8), then install pytimber using pip:

[anaconda]: https://www.continuum.io/downloads

```sh
pip install pytimber
```

or for the most updated version

```sh
pip install git+https://github.com/rdemaria/pytimber.git
```

This will also install [cmmnbuild-dep-manager][] to provide automatic
resolution of Java dependencies for CERN packages. It is required to use
pytimber with other CERN libraries, such as [PyJapc][].

[cmmnbuild-dep-manager]: https://gitlab.cern.ch/scripting-tools/cmmnbuild-dep-manager
[pyjapc]: https://gitlab.cern.ch/scripting-tools/pyjapc

### Installation notes

  * For Windows, [this][jpype-win] pre-compiled version of JPype seems to work
    best.
  * For CERN machines without internet access, you need to manually install the
    dependencies and use the mirrors on the Scripting Tools GitLab group:

    ```sh
    pip install git+https://gitlab.cern.ch/scripting-tools/jpype.git
    pip install git+https://gitlab.cern.ch/scripting-tools/cmmnbuild-dep-manager.git
    pip install git+https://gitlab.cern.ch/scripting-tools/pytimber.git

    ```

[jpype-win]: http://www.lfd.uci.edu/~gohlke/pythonlibs/#jpype

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
fills = ldb.getLHCFillsByTime(t1, t2, beam_modes='RAMP')
print([f['fillNumber'] for f in fills])
```

By default all times are returned as Unix timestamps. If you pass
`unixtime=False` to `get()`, `getAligned()`, `getLHCFillData()` or
`getLHCFillsByTime()` then `datetime` objects are returned instead.

## Usage with PageStore

pytimber can be combined with PageStore for local data storage. Usage example:

```python
import pytimber
from pytimber import pagestore

ldb = pytimber.LoggingDB()
mydb = pagestore.PageStore('mydata.db', './datadb')

t1 = time.mktime(time.strptime('Fri Apr 25 00:00:00 2016'))
mydb.store(ldb.get('%RQTD%I_MEAS', t1, t1+60))
mydb.store(ldb.get('%RQTD%I_MEAS', t1+60, t1+120))

mydata = mydb.get('RPMBB.UA47.RQTD.A45B2:I_MEAS', t1+90, t1+110)
data = ldb.get('RPMBB.UA47.RQTD.A45B2:I_MEAS', t1+90, t1+110)
for k in data:
  print(mydata[k][0] - data[k][0])
  print(mydata[k][1] - data[k][1])
```
