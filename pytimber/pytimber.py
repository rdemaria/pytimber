# -*- coding: utf-8 -*-

# Authors:
#   R. De Maria
#   T. Levens
#   C. Hernalsteens
#   M. Betz

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
    logging.getLogger(
        'cmmnbuild_dep_manager.cmmnbuild_dep_manager'
    ).setLevel(logging.WARNING)

    # During first installation with cmmnbuild_dep_manager some necessary jars
    # do not exist, so fall back to locally bundled .jar file in this case.
    if not mgr.is_registered('pytimber'):
        log.warning('pytimber is not registered with cmmnbuild_dep_manager '
                    'so falling back to bundled jar. Things may not work as '
                    'expected...')
        raise ImportError

    _jar = mgr.class_path()
except ImportError:
    # Could not import cmmnbuild_dep_manager -- it is probably not
    # installed. Fall back to using the locally bundled .jar file.
    _moddir = os.path.dirname(__file__)
    _jar = os.path.join(_moddir, 'jars', 'accsoft-cals-extr-client-nodep.jar')

if not jpype.isJVMStarted():
    libjvm = os.environ.get('JAVA_JVM_LIB')
    if libjvm is None:
      libjvm = jpype.getDefaultJVMPath()
    jpype.startJVM(libjvm, '-Djava.class.path={0}'.format(_jar))
else:
    log.warning('JVM is already started')

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
BeamModeValue = \
    cern.accsoft.cals.extr.domain.core.constants.BeamModeValue

source_dict = {
    'mdb': DataLocationPreferences.MDB_PRO,
    'ldb': DataLocationPreferences.LDB_PRO,
    'all': DataLocationPreferences.MDB_AND_LDB_PRO
}


def test():
    print('OK')


class LoggingDB(object):
    def __init__(self, appid='LHC_MD_ABP_ANALYSIS', clientid='BEAM PHYSICS',
                 source='all', silent=False, loglevel=None):
        loc = source_dict[source]
        self._builder = ServiceBuilder.getInstance(appid, clientid, loc)
        self._md = self._builder.createMetaService()
        self._ts = self._builder.createTimeseriesService()
        self._FillService = FillService = self._builder.createLHCFillService()
        self.tree = Hierarchy('root', None, None, self._md)
        if loglevel is not None:
            log.setLevel(loglevel)

    def toTimestamp(self, t):
        if isinstance(t, six.string_types):
            return Timestamp.valueOf(t)
        elif isinstance(t, datetime.datetime):
            return Timestamp.valueOf(t.strftime('%Y-%m-%d %H:%M:%S.%f'))
        elif t is None:
            return None
        else:
            tt = datetime.datetime.fromtimestamp(t)
            ts = Timestamp.valueOf(tt.strftime('%Y-%m-%d %H:%M:%S.%f'))
            sec = int(t)
            nanos = int((t-sec)*1e9)
            ts.setNanos(nanos)
            return ts

    def fromTimestamp(self, ts, unixtime):
        if ts is None:
            return None
        else:
            t = ts.fastTime / 1000.0 + ts.getNanos() / 1.0e9
            if unixtime:
                return t
            else:
                return datetime.datetime.fromtimestamp(t)

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

    def getVariablesList(self, pattern_or_list):
        """Get a list of variables based on a list of strings or a pattern.
        Wildcard for the pattern is '%'.
        """
        if isinstance(pattern_or_list, six.string_types):
            types = VariableDataType.ALL
            variables = self._md.getVariablesOfDataTypeWithNameLikePattern(
                    pattern_or_list, types)
        elif isinstance(pattern_or_list, (list, tuple)):
            variables = self._md.getVariablesWithNameInListofStrings(
                    java.util.Arrays.asList(pattern_or_list))
        else:
            variables = None
        return variables

    def processDataset(self, dataset, datatype, unixtime):
        datas = []
        tss = []
        for tt in dataset:
            ts = self.fromTimestamp(tt.getStamp(), unixtime)
            if datatype == 'MATRIXNUMERIC':
                val = np.array(tt.getMatrixDoubleValues(),dtype=float)
            elif datatype == 'VECTORNUMERIC':
                val = np.array(tt.getDoubleValues(),dtype=float)
            elif datatype == 'VECTORSTRING':
                val = np.array(tt.getStringValues(),dtype='U')
            elif datatype == 'NUMERIC':
                val = tt.getDoubleValue()
            elif datatype == 'FUNDAMENTAL':
                val = 1
            elif datatype == 'TEXTUAL':
                val = unicode(tt.getVarcharValue())
            else:
                log.warning('Unsupported datatype, returning the java object')
                val = tt
            datas.append(val)
            tss.append(ts)
        tss = np.array(tss)
        datas = np.array(datas)
        return (tss, datas)

    def getAligned(self, pattern_or_list, t1, t2,
                   fundamental=None, master=None, unixtime=True):
        """Get data aligned to a variable"""
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
        variables = self.getVariablesList(pattern_or_list)

        if master is None:
            if isinstance(pattern_or_list, (list, tuple)):
                master_variable = variables.getVariable(pattern_or_list[0])
            else:
                master_variable = variables.getVariable(0)
        else:
            master_variable = variables.getVariable(master)

        if master_variable is None:
            log.warning('Master variable not found.')
            return {}

        master_name = master_variable.toString()

        if len(variables) == 0:
            log.warning('No variables found.')
            return {}
        else:
            logvars = []
            for v in variables:
                if v == master_name:
                    logvars.append('{0} (master)'.format(v))
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
            log.info('{0} seconds for aqn'.format(time.time()-start_time))
            out[v] = self.processDataset(
                       res, res.getVariableDataType().toString(), unixtime)[1]
        return out

    def searchFundamental(self, fundamental, t1, t2=None):
        """Search fundamental"""
        ts1 = self.toTimestamp(t1)
        if t2 is None:
            t2 = time.time()
        ts2 = self.toTimestamp(t2)
        fundamentals = self.getFundamentals(ts1, ts2, fundamental)
        if fundamentals is not None:
            return list(fundamentals.getVariableNames())
        else:
            return []

    def get(self, pattern_or_list, t1, t2=None,
            fundamental=None, unixtime=True):
        """Query the database for a list of variables or for variables whose
        name matches a pattern (string) in a time window from t1 to t2.

        If t2 is missing, None, "last", the last data point before t1 is given
        If t2 is "next", the first data point after t1 is given.

        If no pattern if given for the fundamental all the data are returned.

        If a fundamental pattern is provided, the end of the time window as to
        be explicitely provided.
        """
        ts1 = self.toTimestamp(t1)
        if t2 not in ['last','next',None]:
          ts2 = self.toTimestamp(t2)
        out = {}

        # Build variable list
        variables = self.getVariablesList(pattern_or_list)
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
            log.warning('Unsupported: if filtering by fundamentals'
                        'you must provide a correct time window')
            return {}
        if fundamental is not None:
            fundamentals = self.getFundamentals(ts1, ts2, fundamental)
            if fundamentals is None:
                return {}

        # Acquire
        for v in variables:
            jvar = variables.getVariable(v)
            if t2 is None or t2=='last':
                res = \
                  [self._ts.getLastDataPriorToTimestampWithinDefaultInterval(
                    jvar, ts1)]
                datatype = res[0].getVariableDataType().toString()
                log.info('Retrieved {0} values for {1}'.format(
                           1, jvar.getVariableName()))
            elif t2=='next':
                res = \
                  [self._ts.getNextDataAfterTimestampWithinDefaultInterval(
                    jvar, ts1)]
                if res[0] is None:
                  res=[]
                  datatype=None
                else:
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

    def getLHCFillData(self, fill_number=None, unixtime=True):
        """Gets times and beam modes for a particular LHC fill.
        Parameter fill_number can be an integer to get a particular fill or
        None to get the last completed fill.
        """
        if isinstance(fill_number, int):
            data = self._FillService.getLHCFillAndBeamModesByFillNumber(
                fill_number
            )
        else:
            data = self._FillService.getLastCompletedLHCFillAndBeamModes()

        if data is None:
            return None
        else:
            return {
                'fillNumber': data.getFillNumber(),
                'startTime': self.fromTimestamp(data.getStartTime(), unixtime),
                'endTime': self.fromTimestamp(data.getEndTime(), unixtime),
                'beamModes': [{
                    'mode':
                        mode.getBeamModeValue().toString(),
                    'startTime':
                        self.fromTimestamp(mode.getStartTime(), unixtime),
                    'endTime':
                        self.fromTimestamp(mode.getEndTime(), unixtime)
                } for mode in data.getBeamModes()]
            }

    def getLHCFillsByTime(self, t1, t2, beam_modes=None, unixtime=True):
        """Returns a list of the fills between t1 and t2.
        Optional parameter beam_modes allows filtering by beam modes.
        """
        ts1 = self.toTimestamp(t1)
        ts2 = self.toTimestamp(t2)

        if beam_modes is None:
            fills = self._FillService.getLHCFillsAndBeamModesInTimeWindow(
                ts1, ts2
            )
        else:
            if isinstance(beam_modes, str):
                beam_modes = beam_modes.split(',')

            valid_beam_modes = [
                mode
                for mode in beam_modes
                if BeamModeValue.isBeamModeValue(mode)
            ]

            if len(valid_beam_modes) == 0:
                raise ValueError('no valid beam modes found')

            java_beam_modes = BeamModeValue.parseBeamModes(
                ','.join(valid_beam_modes)
            )

            fills = (
                self._FillService
                .getLHCFillsAndBeamModesInTimeWindowContainingBeamModes(
                    ts1, ts2, java_beam_modes
                )
            )

        return [
            self.getLHCFillData(fill, unixtime)
            for fill in fills.getFillNumbers()
        ]


class Hierarchy(object):
    def __init__(self, name, obj, src, varsrc):
        self.name = name
        self.obj = obj
        self.varsrc = varsrc
        if src is not None:
            self.src = src
        for vvv in self.get_vars():
            if len(vvv) > 0:
                setattr(self, self.cleanName(vvv), vvv)

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
            if ss in ' _-;></:.':
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
        v = sorted([self.cleanName(i) for i in self.get_vars() if len(i) > 0])
        return sorted(self._dict.keys()) + v

    def __repr__(self):
        if self.obj is None:
            return '<Top Hierarchy>'
        else:
            name = self.obj.getHierarchyName()
            desc = self.obj.getDescription()
            return '<{0}: {1}>'.format(name, desc)

    def get_vars(self):
        if self.obj is not None:
            vvv = self.varsrc.getVariablesOfDataTypeAttachedToHierarchy(
                    self.obj, VariableDataType.ALL)
            return vvv.toString()[1:-1].split(', ')
        else:
            return []
