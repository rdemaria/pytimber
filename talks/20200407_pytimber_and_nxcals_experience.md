---
title: pytimber and nxcals experience
tags: presentation
slideOptions:
  theme: cern2
  transition: 'fade'
slideNumber: true
---



# pytimber with NXCALS

R. De Maria, P. Sowinski, P. Elson

Thanks to L. Coyle, T. Ytterdal, NXCALS team


---

## pytimber

* pytimber is simple wrapper to Logging Service APIs (CALS and now NXCALS)
* pytimber development is community driven and officially supported by CO
* contacts: [mattermost acc-py channel](https://mattermost.web.cern.ch/acc-py/channels/town-square), acc-logging-support@cern.ch
* Version 3.0.0 is being released and brings:
    * First NXCALS support using the backport API and experimental native API
    * Drop support for Python <3.6 and jpype <0.7.1
    * Various fixes and improvements
* pytimber 3.0.x will be proposed for installtion in the next LCG release (LCG98 probably)


---

## pytimber installation

* In a recent own-managed python stack:

```
pip install pytimber
```

---

## pytimber installation (Swan)


* In Swan (stack "96 Python3"):
 
```python
#Always on the top of your notebooks#
import sys, site; sys.path.insert(0, site.USER_SITE)
import os
os.environ['PYTHONPATH'] = f"{site.USER_SITE}:{os.environ['PYTHONPATH']}"
#Install modules: only once#
!pip install --upgrade pip --user
!~/.local/bin/pip install pytimber --user
```

---

## pytimber installation (lxplus)


* In lxplus terminal:

```
source /cvmfs/sft.cern.ch/lcg/views/LCG_97python3/x86_64-centos7-gcc9-opt/setup.sh
VENV_PATH=~/pytimber3-env
python -m venv $VENV_PATH
source $VENV_PATH/bin/activate
export PYTHONPATH=$VENV_PATH/lib/python3.7/site-packages:$PYTHONPATH
python -m pip install -U pytimber
```

---

## pytimber installation (technical network)


* In technical network terminal:

```
source /acc/local/share/python/acc-py/pro/setup.sh
VENV_PATH=~/pytimber3-env
acc-py venv $VENV_PATH 
source $VENV_PATH/bin/activate
python -m pip install -U pytimber
export LD_LIBRARY_PATH=$ACC_PY_PREFIX/lib:$ACC_PY_COMPILER_PREFIX/lib64
```

---

## pytimber installation (dev version)

For the development version of pytimber use instead:

```
pip install -U git+https://gitlab.cern.ch/scripting-tools/pytimber/
```

---

## pytimber with NXCALS

1. Request acc-logging-support@cern.ch for permission to use NXCALS as explained at:
http://nxcals-docs.web.cern.ch/current/user-guide/data-access/nxcals-access-request/

2. Using backport API:
`import pytimber`
`pytimber.check_kerberos() #For Swan only and once per session (create kerberos token)`
`ldb=pytimber.LoggingDB(source='nxcals')`
Your existing scripts should work without modifications (if not, contact support).

3. Using native API (very experimental) for spark queries:
`import pytimber`
`nxcals=pytimber.NXCALS()`
See https://github.com/rdemaria/pytimber/blob/master/examples/nxcals_example.py


---

## Using Backport API in pytimber

* Backport API mimics CALS API but it is not a full drop-in replacement
* pytimber porting triggered Backport API improvements (thanks to NXCALS team)

* Status
    * needs a kerberos token
    * requires similarly named packages
    * returns similarly named objects
    * still missing methods (e.g. hierarchy)
    * ~~nxcals returns extra nulls~~ (fixed in the last NXCALS >0.4.20)


---

## Using Backport API in pytimber


* In pytimber we needed to duplicate and modify a fraction of the code:
    * Java: 84 LOC for CALS -> extra 132 LOC
    * Python: 5 LOC for CALS -> extra 60 LOC
    * About 20 person x days required

---

## Code differences: Java (1)
NXCALS
```Java
    public static double[] doubleData(TimeseriesDataSet dataSet) {
        return dataSet.stream().filter(BackPortDataSets::isNotNullValue)
                .mapToDouble(timeseriesData -> {
                            try {
                                return timeseriesData.getDoubleValue();
                            } catch (NoSuchMethodException ex) {
                                throw new RuntimeException(ex);
                            }
                        }
                ).toArray();
    }

```

CALS
```Java
    public static double[] doubleData(TimeseriesDataSet dataSet) {
        return dataSet.stream().map(NumericDoubleData.class::cast).mapToDouble(NumericDoubleData::getDoubleValue)
                .toArray();
    }
```
same for other types


---

## Code differences: Python (1)
Initialization of the service
```python
        if source == "nxcals":
            check_kerberos()
            self._System = jpype.java.lang.System
            self._System.setProperty(
                "service.url",
                "https://cs-ccr-nxcals6.cern.ch:19093,"
                "https://cs-ccr-nxcals7.cern.ch:19093,"
                "https://cs-ccr-nxcals8.cern.ch:19093",
            )
            ServiceBuilder = jpype.JPackage(
                "cern"
            ).nxcals.api.backport.client.service.ServiceBuilder
            builder = ServiceBuilder.getInstance()
            self._md = builder.createMetaService()
            self._ts = builder.createTimeseriesService()
            self._VariableDataType = jpype.JPackage(
                "cern"
            ).nxcals.api.backport.domain.core.constants.VariableDataType
        else: #CALS
            DataLocPrefs = jpype.JPackage(
                "cern"
            ).accsoft.cals.extr.domain.core.datasource.DataLocationPreferences
            loc = {
                "mdb": DataLocPrefs.MDB_PRO,
                "ldb": DataLocPrefs.LDB_PRO,
                "all": DataLocPrefs.MDB_AND_LDB_PRO,
            }[source]
````

---

## Code differences Python (2)
Differentiating classes
```python
    def toTimescale(self, timescale_list):
        if self._source == "nxcals":
            Timescale = jpype.JPackage(
                "cern"
            ).nxcals.api.backport.domain.core.constants.TimescalingProperties
        else:
            Timescale = jpype.JPackage(
                "cern"
            ).accsoft.cals.extr.domain.core.constants.TimescalingProperties
```

---

## Code differences (3)
Differentiating classes
```python
        if self._source == "nxcals":
            PrimitiveDataSets = jpype.JPackage(
                "org"
            ).pytimber.utils.BackPortDataSets
        else:
            PrimitiveDataSets = jpype.JPackage(
                "org"
            ).pytimber.utils.PrimitiveDataSets
```

---

## Code differences (4)
Different approach for data unpacking
```python
        if self._source == "nxcals":
            ds = dataset
            if datatype == "NUMERIC":
                try:
                    ds = np.array([d.getDoubleValue() for d in ds])
                except jpype.java.lang.NoSuchMethodException:
                    try:
                        ds = np.array([d.getLongValue() for d in ds])
                    except jpype.java.lang.NoSuchMethodException:
                        self._log.warning("unsupported datatype, returning the java object")
            elif datatype == "VECTORNUMERIC":
                try:
                    ds = np.array([d.getDoubleValues() for d in ds])
                except jpype.java.lang.NoSuchMethodException:
                    try:
                        ds = np.array([d.getLongValues() for d in ds])
                    except jpype.java.lang.NoSuchMethodException:
                        self._log.warning("unsupported datatype, returning the java object")
            elif datatype == "TEXTUAL":
                try:
                    ds = np.array([d.getVarcharValue() for d in ds])
                except jpype.java.lang.NoSuchMethodException:
                    self._log.warning("unsupported datatype, returning the java object")
            elif datatype == "VECTORSTRING":
                try:
                    ds = np.array([d.getStringValues() for d in ds])
                except jpype.java.lang.NoSuchMethodException:
                    self._log.warning("unsupported datatype, returning the java object")
            else:
                self._log.warning("unsupported datatype, returning the java object")
            return (timestamps, ds)
```