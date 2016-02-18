# -*- coding: utf-8 -*-

import os
import glob
import time
import datetime
import six
import logging

import jpype
import numpy as np

"""Latest version of the standalone jar is availale here:
http://abwww.cern.ch/ap/dist/accsoft/cals/accsoft-cals-extr-client/PRO/build/dist/accsoft-cals-extr-client-nodep.jar
"""

logging.basicConfig()
log = logging.getLogger(__name__)

try:
    # Try to get a lit of .jars from cmmnbuild_dep_manager.
    import cmmnbuild_dep_manager
    mgr = cmmnbuild_dep_manager.Manager()

    # During first installation with cmmnbuild_dep_manager some necessary jars
    # do not exist, so fall back to locally bundled .jar file in this case.
    if not mgr.is_registered("pytimber"):
        log.warn("pytimber is not registered with cmmnbuild_dep_manager "
                 "so falling back to bundled jar. Things may not work as "
                 "expected...")
        raise ImportError

    _jar = mgr.class_path()
except ImportError:
    # Could not import cmmnbuild_dep_manager -- it is probably not
    # installed. Fall back to using the locally bundled .jar file.
    _moddir = os.path.dirname(__file__)
    _jar = os.path.join(_moddir, 'jars', 'accsoft-cals-extr-client-nodep.jar')

if not jpype.isJVMStarted():
    libjvm = jpype.getDefaultJVMPath()
    jpype.startJVM(libjvm, '-Djava.class.path={0}'.format(_jar))
else:
    log.warn('JVM is already started')

# Definitions of Java packages
cern = jpype.JPackage('cern')
org = jpype.JPackage('org')
java = jpype.JPackage('java')
ServiceBuilder = cern.accsoft.cals.extr.client.service.ServiceBuilder
DataLocationPreferences = \
        cern.accsoft.cals.extr.domain.core.datasource.DataLocationPreferences
VariableDataType = \
        cern.accsoft.cals.extr.domain.core.constants.VariableDataType
Timestamp = java.sql.Timestamp
null = org.apache.log4j.varia.NullAppender()
org.apache.log4j.BasicConfigurator.configure(null)

source_dict = {
    'mdb': DataLocationPreferences.MDB_PRO,
    'ldb': DataLocationPreferences.LDB_PRO,
    'all': DataLocationPreferences.MDB_AND_LDB_PRO
}


def test():
    print("OK")


class LoggingDB(object):
    def __init__(self, appid='LHC_MD_ABP_ANALYSIS', clientid='BEAM PHYSICS',
                 source='all', silent=False):
        loc = source_dict[source]
        self._builder = ServiceBuilder.getInstance(appid, clientid, loc)
        self._md = self._builder.createMetaService()
        self._ts = self._builder.createTimeseriesService()
        self.tree = Hierarchy('root', None, None, self._md)

    def toTimestamp(self, t):
        if isinstance(t, six.string_types):
            return Timestamp.valueOf(t)
        elif type(t) is datetime.datetime:
            return Timestamp.valueOf(t.strftime("%Y-%m-%d %H:%M:%S.%f"))
        elif t is None:
            return None
        else:
            tt = datetime.datetime.fromtimestamp(t)
            ts = Timestamp.valueOf(tt.strftime("%Y-%m-%d %H:%M:%S.%f"))
            sec = int(t)
            nanos = int((t-sec)*1e9)
            ts.setNanos(nanos)
            return ts

    def toStringList(self, myArray):
        myList = java.util.ArrayList()
        for s in myArray:
            myList.add(s)
        return myList

    def search(self, pattern):
        """Search for parameter names. Wildcard is '%'."""
        types = VariableDataType.ALL
        v = self._md.getVariablesOfDataTypeWithNameLikePattern(pattern, types)
        return v.toString()[1:-1].split(', ')

    def getFundamentals(self, t1, t2, fundamental):
        log.info('Querying fundamentals (pattern: {0}):'.format(fundamental))
        fundamentals = self._md.getFundamentalsInTimeWindowWithNameLikePattern(
                        t1, t2, fundamental)
        if fundamentals is None:
            log.info('No fundamental found in time window')
        else:
            logfuns = []
            for f in fundamentals:
                logfuns.append(f)
            log.info('List of fundamentals found: {0}'.format(
                ', '.join(logfuns)))
        return fundamentals

    def getVariablesList(self, pattern_or_list, t1, t2):
        """Get a list of variables based on a list of strings or a pattern.
        Wildcard for the pattern is '%'.
        Assumes t1 and t2 to be Java TimeStamp objects
        """
        if isinstance(pattern_or_list, six.string_types):
            types = VariableDataType.ALL
            variables = self._md.getVariablesOfDataTypeWithNameLikePattern(
                    pattern_or_list, types)
        elif isinstance(pattern_or_list, list):
            variables = self._md.getVariablesWithNameInListofStrings(
                    java.util.Arrays.asList(pattern_or_list))
        else:
            variables = None
        return variables

    def processDataset(self, dataset, datatype, unixtime):
        datas = []
        tss = []
        for tt in dataset:
            ts = tt.getStamp()
            ts = ts.fastTime/1000.+ts.getNanos()/1e9
            if datatype == 'MATRIXNUMERIC':
                val = np.array(tt.getMatrixDoubleValues())
            elif datatype == 'VECTORNUMERIC':
                val = np.array(tt.getDoubleValues())
            elif datatype == 'NUMERIC':
                val = tt.getDoubleValue()
            elif datatype == 'FUNDAMENTAL':
                val = 1
            elif datatype == 'TEXTUAL':
                val = tt.getVarcharValue()
            else:
                self.warn('Unsupported datatype, returning the java object')
                val = tt
            datas.append(val)
            tss.append(ts)
        if not unixtime:
            tss = list(map(datetime.datetime.fromtimestamp, tss))
        tss = np.array(tss)
        datas = np.array(datas)
        return (tss, datas)

    def getAligned(self, pattern_or_list, t1, t2,
                   fundamental=None, unixtime=True):
        ts1 = self.toTimestamp(t1)
        ts2 = self.toTimestamp(t2)
        out = {}
        master_variable = None

        # Fundamentals
        if fundamental is not None:
            fundamentals = self.getFundamentals(ts1, ts2, fundamental)
            if fundamentals is None:
                return {}

        # Build variable list
        variables = self.getVariablesList(pattern_or_list, ts1, ts2)
        if len(variables) == 0:
            log.warning('No variables found.')
            return {}
        else:
            logvars = []
            for i, v in enumerate(variables):
                if i == 0:
                    master_variable = variables.getVariable(0)
                    master_name = master_variable.toString()
                    logvars.append('{0} (using as master)'.format(v))
                else:
                    logvars.append(v)
                log.info('List of variables to be queried: {0}'.format(
                    ', '.join(logvars)))

        # Acquire master dataset
        if fundamental is not None:
            master_ds = self._ts.getDataInTimeWindowFilteredByFundamentals(
                    master_variable, ts1, ts2, fundamentals)
        else:
            master_ds = self._ts.getDataInTimeWindow(master_variable, ts1, ts2)
        log.info('Retrieved {0} values for {1} (master)'.format(
            master_ds.size(), master_name))

        # Prepare master dataset for output
        out['timestamps'], out[master_name] = self.processDataset(
            master_ds,
            master_ds.getVariableDataType().toString(),
            unixtime
        )

        # Acquire aligned data based on master dataset timestamps
        for v in variables:
            if v == master_name:
                continue
            jvar = variables.getVariable(v)
            start_time = time.time()
            res = self._ts.getDataAlignedToTimestamps(jvar, master_ds)
            log.info('Retrieved {0} values for {1}'.format(
                res.size(), jvar.getVariableName()))
            log.info(time.time()-start_time, "seconds for aqn")
            out[v] = self.processDataset(
                       res, res.getVariableDataType().toString(), unixtime)[1]
        return out

    def get(self, pattern_or_list, t1, t2=None,
            fundamental=None, unixtime=True):
        """Query the database for a list of variables or for variables whose
        name matches a pattern (string).

        If no pattern if given for the fundamental all the data are returned.

        If a fundamental pattern is provided, the end of the time window as to
        be explicitely provided.
        """
        ts1 = self.toTimestamp(t1)
        ts2 = self.toTimestamp(t2)
        out = {}

        # Build variable list
        variables = self.getVariablesList(pattern_or_list, ts1, ts2)
        if len(variables) == 0:
            log.warning('No variables found.')
            return {}
        else:
            logvars = []
            for v in variables:
                logvars.append(v)
            log.info('List of variables to be queried: {0}'.format(
                ', '.join(logvars)))

        # Fundamentals
        if fundamental is not None and ts2 is None:
            self.warn('Unsupported: if filtering by fundamentals'
                      'you must provide a correct time window')
            return {}
        if fundamental is not None:
            fundamentals = self.getFundamentals(ts1, ts2, fundamental)
            if fundamentals is None:
                return {}

        # Acquire
        for v in variables:
            jvar = variables.getVariable(v)
            if t2 is None:
                res = \
                  [self._ts.getLastDataPriorToTimestampWithinDefaultInterval(
                    jvar, ts1)]
                datatype = res[0].getVariableDataType().toString()
                log.info('Retrieved {0} values for {1}'.format(
                           1, jvar.getVariableName()))
            else:
                if fundamental is not None:
                    res = self._ts.getDataInTimeWindowFilteredByFundamentals(
                            jvar, ts1, ts2, fundamentals)
                else:
                    res = self._ts.getDataInTimeWindow(jvar, ts1, ts2)
                datatype = res.getVariableDataType().toString()
                log.info('Retrieved {0} values for {1}'.format(
                    res.size(), jvar.getVariableName()))
            out[v] = self.processDataset(res, datatype, unixtime)
        return out


class Hierarchy(object):
    def __init__(self, name, obj, src, varsrc):
        self.name = name
        self.obj = obj
        self.varsrc = varsrc
        if src is not None:
            self.src = src

    def _get_childs(self):
        if self.obj is None:
            objs = self.src.getHierachies(1)
        else:
            objs = self.src.getChildHierarchies(self.obj)
        return dict([(self.cleanName(hh.hierarchyName), hh) for hh in objs])

    def cleanName(self, s):
        if s[0].isdigit():
            s = '_'+s
        out = []
        for ss in s:
            if ss in ' _;></':
                out.append('_')
            else:
                out.append(ss)
        return ''.join(out)

    def __getattr__(self, k):
        if k == 'src':
            self.src = self.varsrc.getAllHierarchies()
            return self.src
        elif k == '_dict':
            self._dict = self._get_childs()
            return self._dict
        else:
            return Hierarchy(k, self._dict[k], self.src, self.varsrc)

    def __dir__(self):
        return sorted(self._dict.keys())

    def __repr__(self):
        if self.obj is None:
            return "<Top Hierarchy>"
        else:
            name = self.obj.getHierarchyName()
            desc = self.obj.getDescription()
            return "<{0}: {1}>".format(name, desc)

    def get_vars(self):
        if self.obj is not None:
            vvv = self.varsrc.getVariablesOfDataTypeAttachedToHierarchy(
                    self.obj, VariableDataType.ALL)
            return vvv.toString()[1:-1].split(', ')
        else:
            return []
