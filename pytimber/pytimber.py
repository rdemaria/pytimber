#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyTimber -- A Python wrapping of CALS API

Copyright (c) CERN 2015-2017

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Authors:
    R. De Maria     <riccardo.de.maria@cern.ch>
    T. Levens       <tom.levens@cern.ch>
    C. Hernalsteens <cedric.hernalsteens@cern.ch>
    M. Betz         <michael.betz@cern.ch>
    M. Fitterer     <mfittere@fnal.gov>
    R. Castellotti  <riccardo.castellotti@cern.ch>
    L. Coyle        <loic.coyle@epfl.ch>
    P. Sowinski     <piotr.sowinski@cern.ch>
"""

import time
import datetime
import six
import logging

from .check_kerberos import check_kerberos
from .sparkresources import SparkResources

try:
    import jpype
    import cmmnbuild_dep_manager
except ImportError:
    print(
        """ERROR: module jpype and cmmnbuild_dep_manager not found!
        Exporting data from the logging database will not be
        available!"""
    )
import numpy as np
from collections import namedtuple

Stat = namedtuple(
    "Stat",
    [
        "MinTstamp",
        "MaxTstamp",
        "ValueCount",
        "MinValue",
        "MaxValue",
        "AvgValue",
        "StandardDeviationValue",
    ],
)


def _Timestamp2float(ts):
    return int(ts.getTime() / 1000.0) + ts.getNanos() / 1e9


if six.PY3:
    long = int


# Documentation CALS API
# http://abwww.cern.ch/ap/dist/accsoft/cals/accsoft-cals-extr-client/PRO/build/docs/api/


class LoggingDB(object):
    try:
        _jpype = jpype
    except NameError:
        print("ERROR: jpype is note defined!")

    def __init__(
        self,
        appid="PYTIMBER3",
        clientid="PYTIMBER3",
        source="all",
        loglevel=None,
        sparkconf=None,
        sparkprops=None
    ):
        # Configure logging
        logging.basicConfig()
        self._log = logging.getLogger(__name__)
        if loglevel is not None:
            self._log.setLevel(loglevel)

        # Start JVM
        mgr = cmmnbuild_dep_manager.Manager("pytimber")
        mgr.start_jpype_jvm()
        self._mgr = mgr

        # log4j config
        null = jpype.JPackage("org").apache.log4j.varia.NullAppender()
        jpype.JPackage("org").apache.log4j.BasicConfigurator.configure(null)

        self._source = source

        if source == "nxcals":
            check_kerberos()
            self._System = jpype.java.lang.System
            self._System.setProperty(
                "service.url",
                "https://cs-ccr-nxcals6.cern.ch:19093,https://cs-ccr-nxcals7.cern.ch:19093,https://cs-ccr-nxcals8.cern.ch:19093",
            )
            ServiceBuilder = jpype.JPackage(
                "cern"
            ).nxcals.api.backport.client.service.ServiceBuilder

            if sparkconf is not None:
                conf = SparkResources.from_str(sparkconf.upper())

                spark_properties = jpype.JPackage("cern").nxcals.api.config.SparkProperties()
                spark_properties.setAppName(appid)
                spark_properties.setMasterType("yarn")

                properties = jpype.JClass('java.util.HashMap')()

                for key, value in conf.properties.items():
                    properties[key] = value

                if conf == SparkResources.CUSTOM:
                    for key, value in sparkprops:
                        properties[key] = value

                spark_properties.setProperties(properties)

                builder = ServiceBuilder.getInstance(spark_properties)
            else:
                builder = ServiceBuilder.getInstance()

            self._md = builder.createMetaService()
            self._ts = builder.createTimeseriesService()
            self._FillService = builder.createLHCFillService()
            self._VariableDataType = jpype.JPackage(
                "cern"
            ).nxcals.api.backport.domain.core.constants.VariableDataType
            # self.tree = Hierarchy("root", None, None, self._md, self._VariableDataType)
            self._BeamModeValue = jpype.JPackage(
                "cern"
            ).nxcals.api.backport.domain.core.constants.BeamModeValue

#            h = self._md.getAllHierarchies()
#            print(h)
        else:
            # Data source preferences
            DataLocPrefs = jpype.JPackage(
                "cern"
            ).accsoft.cals.extr.domain.core.datasource.DataLocationPreferences
            loc = {
                "mdb": DataLocPrefs.MDB_PRO,
                "ldb": DataLocPrefs.LDB_PRO,
                "all": DataLocPrefs.MDB_AND_LDB_PRO,
            }[source]

            ServiceBuilder = jpype.JPackage(
                "cern"
            ).accsoft.cals.extr.client.service.ServiceBuilder
            builder = ServiceBuilder.getInstance(appid, clientid, loc)
            self._builder = builder
            self._md = builder.createMetaService()
            self._ts = builder.createTimeseriesService()
            self._FillService = builder.createLHCFillService()
            self._VariableDataType = jpype.JPackage(
                "cern"
            ).accsoft.cals.extr.domain.core.constants.VariableDataType
            self.tree = Hierarchy("root", None, None, self._md, self._VariableDataType)
            self._BeamModeValue = jpype.JPackage(
                "cern"
            ).accsoft.cals.extr.domain.core.constants.BeamModeValue

            h = self._md.getAllHierarchies()
            print(h)

    def toTimestamp(self, t):
        Timestamp = jpype.java.sql.Timestamp
        if isinstance(t, six.string_types):
            return Timestamp.valueOf(t)
        elif isinstance(t, datetime.datetime):
            return Timestamp.valueOf(t.strftime("%Y-%m-%d %H:%M:%S.%f"))
        elif t is None:
            return None
        elif isinstance(t, Timestamp):
            return t
        else:
            ts = Timestamp(long(t * 1000))
            sec = int(t)
            nanos = int((t - sec) * 1e9)
            ts.setNanos(nanos)
            return ts

    def fromTimestamp(self, ts, unixtime):
        if ts is None:
            return None
        else:
            t = _Timestamp2float(ts)
            if unixtime:
                return t
            else:
                return datetime.datetime.fromtimestamp(t)

    def toStringList(self, myArray):
        myList = jpype.java.util.ArrayList()
        for s in myArray:
            myList.add(s)
        return myList

    def toTimescale(self, timescale_list):
        if self._source == "nxcals":
            Timescale = jpype.JPackage(
                "cern"
            ).nxcals.api.backport.domain.core.constants.TimescalingProperties
        else:
            Timescale = jpype.JPackage(
                "cern"
            ).accsoft.cals.extr.domain.core.constants.TimescalingProperties
        try:
            timescale_str = "_".join(timescale_list)
            return Timescale.valueOf(timescale_str)
        except Exception as e:
            self._log.warning("exception in timescale:{}".format(e))

    def search(self, pattern):
        """Search for parameter names. Wildcard is '%'."""
        types = self._VariableDataType.ALL
        vl = self._md.getVariablesOfDataTypeWithNameLikePattern(pattern, types)
        return [vv.getVariableName() for vv in vl.getVariables()]

    def getDescription(self, pattern):
        """Get Variable Description from pattern. Wildcard is '%'."""
        return dict(
            [
                (vv.getVariableName(), vv.getDescription())
                for vv in self._getVariableList(pattern)
            ]
        )

    def getUnit(self, pattern):
        """Get Variable Unit from pattern. Wildcard is '%'."""
        return dict(
            [
                (vv.getVariableName(), vv.getUnit())
                for vv in self._getVariableList(pattern)
            ]
        )

    def _getFundamentals(self, t1, t2, fundamental):
        self._log.info(
            "Querying fundamentals (pattern: {0}):".format(fundamental)
        )
        fundamentals = self._md.getFundamentalsInTimeWindowWithNameLikePattern(
            t1, t2, fundamental
        )
        if fundamentals is None:
            self._log.info("No fundamental found in time window")
        else:
            logfuns = []
            for f in fundamentals.getVariables():  # workaround 0.7.1
                logfuns.append(f.toString())
            self._log.info(
                "List of fundamentals found: {0}".format(", ".join(logfuns))
            )
        return fundamentals

    def getFundamentals(self, t1, t2, fundamental):
        self._log.warning("getFundamentals will be deprecated")
        return self.searchFundamental(fundamental, t1, t2)

    def getVariableSet(self, pattern_or_list):
        """Get a list of variables based on a list of strings or a pattern.
        Wildcard for the pattern is '%'.
        """
        if isinstance(pattern_or_list, six.string_types):
            types = self._VariableDataType.ALL
            variables = self._md.getVariablesOfDataTypeWithNameLikePattern(
                pattern_or_list, types
            )
        elif isinstance(pattern_or_list, (list, tuple)):
            variables = self._md.getVariablesWithNameInListofStrings(
                jpype.java.util.Arrays.asList(pattern_or_list)
            )
        else:
            raise ValueError(f"{pattern_or_list} not pattern or list")
        return variables

    def _getVariableList(self, pattern_or_list):
        """work around for jpype 0.7.1 as list(vset) gives strings
        """
        return self.getVariableSet(pattern_or_list).getVariables()

    def processDataset(self, dataset, datatype, unixtime):
        spi = jpype.JPackage(
            "cern"
        ).accsoft.cals.extr.domain.core.timeseriesdata.spi

        if type(dataset) is list:
            new_ds = jpype.JPackage(
                "cern"
            ).accsoft.cals.extr.domain.core.timeseriesdata.spi.TimeseriesDataSetImpl()
            for data in dataset:
                new_ds.add(data)
            dataset = new_ds

        if dataset.isEmpty():
            return (np.array([], dtype=float), np.array([], dtype=float))

        # PrimitiveDataSets = jpype.JPackage("cern").lhc.commons.cals.PrimitiveDataSets
        if self._source == "nxcals":
            PrimitiveDataSets = jpype.JPackage(
                "org"
            ).pytimber.utils.BackPortDataSets
        else:
            PrimitiveDataSets = jpype.JPackage(
                "org"
            ).pytimber.utils.PrimitiveDataSets

        timestamps = np.array(
            PrimitiveDataSets.unixTimestamps(dataset)[:], dtype=float
        )
        if not unixtime:
            timestamps = np.array(
                [datetime.datetime.fromtimestamp(t) for t in timestamps]
            )

        dataclass = PrimitiveDataSets.dataClass(dataset)

        if self._source == "nxcals":

            # idx = ~np.array([d.isNullValue() for d in dataset])
            # ds = np.array(dataset)[idx]
            # timestamps = timestamps[idx]

            ds = dataset

            if datatype == "NUMERIC":
                try:
                    ds = np.array([d.getDoubleValue() for d in ds])
                except jpype.java.lang.NoSuchMethodException:
                    try:
                        ds = np.array([d.getLongValue() for d in ds])
                    except jpype.java.lang.NoSuchMethodException:
                        self._log.warning(
                            "unsupported datatype, returning the java object"
                        )
            elif datatype == "VECTORNUMERIC":
                try:
                    ds = np.array([d.getDoubleValues() for d in ds])
                except jpype.java.lang.NoSuchMethodException:
                    try:
                        ds = np.array([d.getLongValues() for d in ds])
                    except jpype.java.lang.NoSuchMethodException:
                        self._log.warning(
                            "unsupported datatype, returning the java object"
                        )
            elif datatype == "TEXTUAL":
                try:
                    ds = np.array([d.getVarcharValue() for d in ds])
                except jpype.java.lang.NoSuchMethodException:
                    self._log.warning(
                        "unsupported datatype, returning the java object"
                    )
            elif datatype == "VECTORSTRING":
                try:
                    ds = np.array([d.getStringValues() for d in ds])
                except jpype.java.lang.NoSuchMethodException:
                    self._log.warning(
                        "unsupported datatype, returning the java object"
                    )
            else:
                self._log.warning(
                    "unsupported datatype, returning the java object"
                )
            return (timestamps, ds)

        if datatype == "MATRIXNUMERIC":
            if dataclass == spi.MatrixNumericDoubleData:
                data = np.array(
                    [
                        [np.array(a[:], dtype=float) for a in matrix]
                        for matrix in PrimitiveDataSets.doubleMatrixData(
                            dataset
                        )
                    ]
                )
            elif dataclass == spi.MatrixNumericLongData:
                data = np.array(
                    [
                        [np.array(a[:], dtype=int) for a in matrix]
                        for matrix in PrimitiveDataSets.longMatrixData(dataset)
                    ]
                )
            else:
                self._log.warning(
                    "'%s' unsupported datatype, returning the java object"
                    % (datatype)
                )
                data = [t for t in dataset]
        elif datatype == "VECTORNUMERIC":
            if dataclass == spi.VectorNumericDoubleData:
                data = np.array(
                    [
                        np.array(a[:], dtype=float)
                        for a in PrimitiveDataSets.doubleVectorData(dataset)
                    ]
                )
            elif dataclass == spi.VectorNumericLongData:
                data = np.array(
                    [
                        np.array(a[:], dtype=int)
                        for a in PrimitiveDataSets.longVectorData(dataset)
                    ]
                )
            else:
                self._log.warning(
                    "Unsupported datatype, returning the " "java object"
                )
                data = [t for t in dataset]
        elif datatype == "VECTORSTRING":
            data = np.array(
                [
                    np.array(a[:], dtype="U")
                    for a in PrimitiveDataSets.stringVectorData(dataset)
                ]
            )
        elif datatype == "NUMERIC":
            if dataclass == spi.NumericDoubleData:
                data = np.array(
                    PrimitiveDataSets.doubleData(dataset)[:], dtype=float
                )
            elif dataclass == spi.NumericLongData:
                data = np.array(
                    PrimitiveDataSets.longData(dataset)[:], dtype=int
                )
            else:
                self._log.warning(
                    "Unsupported datatype, returning the " "java object"
                )
                data = [t for t in dataset]
        elif datatype == "FUNDAMENTAL":
            data = np.ones_like(timestamps, dtype=bool)
        elif datatype == "TEXTUAL":
            data = np.array(
                PrimitiveDataSets.stringData(dataset)[:], dtype="U"
            )
        else:
            self._log.warning(
                "Unsupported datatype, returning the " "java object"
            )
            data = [t for t in dataset]
        return (timestamps, data)

    def getAligned(
        self,
        pattern_or_list,
        t1,
        t2,
        fundamental=None,
        master=None,
        unixtime=True,
    ):
        """Get data aligned to a variable"""
        ts1 = self.toTimestamp(t1)
        ts2 = self.toTimestamp(t2)
        out = {}
        master_variable = None

        # Fundamentals
        if fundamental is not None:
            fundamentals = self._getFundamentals(ts1, ts2, fundamental)
            if fundamentals is None:
                return {}

        # Build variable list
        variables = self._getVariableList(pattern_or_list)

        if master is None:
            if isinstance(pattern_or_list, (list, tuple)):
                master_variable = variables.getVariable(pattern_or_list[0])
            else:
                master_variable = variables.getVariable(0)
        else:
            master_variable = variables.getVariable(master)

        if master_variable is None:
            self._log.warning("Master variable not found.")
            return {}

        master_name = master_variable.toString()

        if len(variables) == 0:
            self._log.warning("No variables found.")
            return {}
        else:
            logvars = []
            for jvar in variables:
                vname = jvar.getVariableName()
                if vname == master_name:
                    logvars.append("{0} (master)".format(vname))
                else:
                    logvars.append(vname)

            self._log.info(
                "List of variables to be queried: {0}".format(
                    ", ".join(logvars)
                )
            )

        # Acquire master dataset
        if fundamental is not None:
            master_ds = self._ts.getDataInTimeWindowFilteredByFundamentals(
                master_variable, ts1, ts2, fundamentals
            )
        else:
            master_ds = self._ts.getDataInTimeWindow(master_variable, ts1, ts2)

        self._log.info(
            "Retrieved {0} values for {1} (master)".format(
                master_ds.size(), master_name
            )
        )

        # Prepare master dataset for output
        out["timestamps"], out[master_name] = self.processDataset(
            master_ds, master_ds.getVariableDataType().toString(), unixtime
        )

        # Acquire aligned data based on master dataset timestamps
        for jvar in variables:
            if jvar.toString() == master_name:
                continue
            start_time = time.time()
            res = self._ts.getDataAlignedToTimestamps(jvar, master_ds)
            self._log.info(
                "Retrieved {0} values for {1}".format(
                    res.size(), jvar.getVariableName()
                )
            )
            self._log.info(
                "{0} seconds for aqn".format(time.time() - start_time)
            )
            out[jvar.getVariableName()] = self.processDataset(
                res, res.getVariableDataType().toString(), unixtime
            )[1]
        return out

    def searchFundamental(self, fundamental, t1, t2=None):
        """Search fundamental"""
        ts1 = self.toTimestamp(t1)
        if t2 is None:
            t2 = time.time()
        ts2 = self.toTimestamp(t2)
        fundamentals = self._getFundamentals(ts1, ts2, fundamental)
        if fundamentals is not None:
            return list(fundamentals.getVariableNames())
        else:
            return []

    def getStats(self, pattern_or_list, t1, t2, unixtime=True):
        ts1 = self.toTimestamp(t1)
        ts2 = self.toTimestamp(t2)

        # Build variable list
        variables = self.getVariableSet(pattern_or_list)
        if len(variables) == 0:
            self._log.warning("No variables found.")
            return {}
        else:
            logvars = []
            for jvar in variables.getVariables():  # workaround 0.7.1
                logvars.append(jvar.toString())
            self._log.info(
                "List of variables to be queried: {0}".format(
                    ", ".join(logvars)
                )
            )

        # Acquire
        data = self._ts.getVariableStatisticsOverMultipleVariablesInTimeWindow(
            variables, ts1, ts2
        )

        out = {}
        for stat in data.getStatisticsList():
            count = stat.getValueCount()
            if count > 0:
                s = Stat(
                    self.fromTimestamp(stat.getMinTstamp(), unixtime),
                    self.fromTimestamp(stat.getMaxTstamp(), unixtime),
                    int(count),
                    stat.getMinValue().doubleValue(),
                    stat.getMaxValue().doubleValue(),
                    stat.getAvgValue().doubleValue(),
                    stat.getStandardDeviationValue().doubleValue(),
                )

                out[stat.getVariableName()] = s

        return out

    #    def getSize(self, pattern_or_list, t1, t2):
    #        ts1 = self.toTimestamp(t1)
    #        ts2 = self.toTimestamp(t2)
    #
    #        # Build variable list
    #        variables = self._getVariableList(pattern_or_list)
    #        if len(variables) == 0:
    #            log.warning('No variables found.')
    #            return {}
    #        else:
    #            logvars = []
    #            for v in variables:
    #                logvars.append(v)
    #            log.info('List of variables to be queried: {0}'.format(
    #                ', '.join(logvars)))
    #        # Acquire
    #        for v in variables:
    #            return self._ts.getJVMHeapSizeEstimationForDataInTimeWindow(v,ts1,ts2,None,None)

    def get(
        self, pattern_or_list, t1, t2=None, fundamental=None, unixtime=True
    ):
        """Query the database for a list of variables or for variables whose
        name matches a pattern (string) in a time window from t1 to t2.

        If t2 is missing, None, "last", the last data point before t1 is given
        If t2 is "next", the first data point after t1 is given.

        If no pattern if given for the fundamental all the data are returned.

        If a fundamental pattern is provided, the end of the time window as to
        be explicitely provided.
        """

        ts1 = self.toTimestamp(t1)
        if t2 not in ["last", "next", None]:
            ts2 = self.toTimestamp(t2)
        out = {}

        # Build variable list
        variables = self._getVariableList(pattern_or_list)
        if len(variables) == 0:
            self._log.warning("No variables found.")
            return {}
        else:
            logvars = []
            for jvar in variables:
                logvars.append(jvar.toString())
            self._log.info(
                "List of variables to be queried: {0}".format(
                    ", ".join(logvars)
                )
            )

        # Fundamentals
        if fundamental is not None and ts2 is None:
            self._log.warning(
                "Unsupported: if filtering by fundamentals "
                "you must provide a correct time window"
            )
            return {}
        if fundamental is not None:
            fundamentals = self._getFundamentals(ts1, ts2, fundamental)
            if fundamentals is None:
                return {}

        # Acquire
        for jvar in variables:
            if t2 is None or t2 == "last":
                res = [
                    self._ts.getLastDataPriorToTimestampWithinDefaultInterval(
                        jvar, ts1
                    )
                ]
                if res[0] is None:
                    res = []
                    datatype = None
                else:
                    datatype = res[0].getVariableDataType().toString()
                    self._log.info(
                        "Retrieved {0} values for {1}".format(
                            1, jvar.getVariableName()
                        )
                    )
            elif t2 == "next":
                res = [
                    self._ts.getNextDataAfterTimestampWithinDefaultInterval(
                        jvar, ts1
                    )
                ]
                if res[0] is None:
                    res = []
                    datatype = None
                else:
                    datatype = res[0].getVariableDataType().toString()
                    self._log.info(
                        "Retrieved {0} values for {1}".format(
                            1, jvar.getVariableName()
                        )
                    )
            else:
                if fundamental is not None:
                    res = self._ts.getDataInTimeWindowFilteredByFundamentals(
                        jvar, ts1, ts2, fundamentals
                    )
                else:
                    res = self._ts.getDataInTimeWindow(jvar, ts1, ts2)
                datatype = res.getVariableDataType().toString()
                self._log.info(
                    "Retrieved {0} values for {1}".format(
                        res.size(), jvar.getVariableName()
                    )
                )
            out[jvar.getVariableName()] = self.processDataset(
                res, datatype, unixtime
            )
        return out

    def getVariable(
        self, variable, t1, t2=None, fundamental=None, unixtime=True
    ):
        return self.get(variable, t1, t2, fundamental, unixtime)[variable]

    def getScaled(
        self,
        pattern_or_list,
        t1,
        t2,
        unixtime=True,
        scaleAlgorithm="SUM",
        scaleInterval="MINUTE",
        scaleSize="1",
    ):
        """Query the database for a list of variables or for variables whose
        name matches a pattern (string) in a time window from t1 to t2.

        If no pattern if given for the fundamental all the data are returned.

        If a fundamental pattern is provided, the end of the time window as to
        be explicitely provided.

        Applies the scaling with supplied scaleAlgorithm, scaleSize, scaleInterval
        """
        ts1 = self.toTimestamp(t1)
        ts2 = self.toTimestamp(t2)
        timescaling = self.toTimescale(
            [scaleSize, scaleInterval, scaleAlgorithm]
        )

        out = {}
        # Build variable list
        variables = self._getVariableList(pattern_or_list)
        if len(variables) == 0:
            self._log.warning("No variables found.")
            return {}
        else:
            logvars = []
            for jvar in variables:
                logvars.append(jvar.toString())
            self._log.info(
                "List of variables to be queried: {0}".format(
                    ", ".join(logvars)
                )
            )

        # Acquire
        for jvar in variables:
            try:
                res = self._ts.getDataInFixedIntervals(
                    jvar, ts1, ts2, timescaling
                )
            except jpype.JException as e:
                print(e.message())
                print(
                    """
                   scaleAlgorithm should be one of:{},
                   scaleInterval one of:{},
                   scaleSize an integer""".format(
                        [
                            "MAX",
                            "MIN",
                            "AVG",
                            "COUNT",
                            "SUM",
                            "REPEAT",
                            "INTERPOLATE",
                        ],
                        [
                            "SECOND",
                            "MINUTE",
                            "HOUR",
                            "DAY",
                            "WEEK",
                            "MONTH",
                            "YEAR",
                        ],
                    )
                )
                return
            datatype = res.getVariableDataType().toString()
            self._log.info(
                "Retrieved {0} values for {1}".format(
                    res.size(), jvar.getVariableName()
                )
            )
            vname = jvar.getVariableName()
            out[vname] = self.processDataset(res, datatype, unixtime)
            if np.isnan(out[vname][1]).any():
                self._log.warning(
                    "Variable {} contains NaN values".format(vname)
                )
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
                "fillNumber": data.getFillNumber(),
                "startTime": self.fromTimestamp(data.getStartTime(), unixtime),
                "endTime": self.fromTimestamp(data.getEndTime(), unixtime),
                "beamModes": [
                    {
                        "mode": mode.getBeamModeValue().toString(),
                        "startTime": self.fromTimestamp(
                            mode.getStartTime(), unixtime
                        ),
                        "endTime": self.fromTimestamp(
                            mode.getEndTime(), unixtime
                        ),
                    }
                    for mode in data.getBeamModes()
                ],
            }

    def getLHCFillsByTime(self, t1, t2, beam_modes=None, unixtime=True):
        """Returns a list of the fills between t1 and t2.
        Optional parameter beam_modes allows filtering by beam modes.
        """
        ts1 = self.toTimestamp(t1)
        ts2 = self.toTimestamp(t2)

        BeamModeValue = self._BeamModeValue

        if beam_modes is None:
            fills = self._FillService.getLHCFillsAndBeamModesInTimeWindow(
                ts1, ts2
            )
        else:
            if isinstance(beam_modes, str):
                beam_modes = beam_modes.split(",")

            valid_beam_modes = [
                mode
                for mode in beam_modes
                if BeamModeValue.isBeamModeValue(mode)
            ]

            if len(valid_beam_modes) == 0:
                raise ValueError("no valid beam modes found")

            java_beam_modes = BeamModeValue.parseBeamModes(
                ",".join(valid_beam_modes)
            )

            fills = self._FillService.getLHCFillsAndBeamModesInTimeWindowContainingBeamModes(
                ts1, ts2, java_beam_modes
            )

        return [
            self.getLHCFillData(fill, unixtime)
            for fill in fills.getFillNumbers()
        ]

    def getIntervalsByLHCModes(
        self,
        t1,
        t2,
        mode1,
        mode2,
        unixtime=True,
        mode1time="startTime",
        mode2time="endTime",
        mode1idx=0,
        mode2idx=-1,
    ):
        """Returns a list of the fill numbers and interval between t1 and
        t2 between the startTime of first beam mode in mode1 and the
        endTime of the first beam mode.

        The optional parameters 'mode[12]time' can take
        'startTime' or 'endTime'

        The otional parameter 'mode[12]idx' selects which mode in case of
        multiple occurrence of mode

        """
        ts1 = self.toTimestamp(t1)
        ts2 = self.toTimestamp(t2)
        fills = self.getLHCFillsByTime(ts1, ts2, [mode1, mode2])
        out = []
        for fill in fills:
            fn = fill["fillNumber"]
            m1 = []
            m2 = []
            for bm in fill["beamModes"]:
                if bm["mode"] == mode1:
                    m1.append(bm[mode1time])
                if bm["mode"] == mode2:
                    m2.append(bm[mode2time])
            if len(m1) > 0 and len(m2) > 0:
                out.append([fn, m1[mode1idx], m2[mode2idx]])
        return out

    def getMetaData(self, pattern_or_list):
        """Get All MetaData for a variable defined by a pattern_or_list"""
        out = {}
        variables = self._getVariableList(pattern_or_list)
        for jvar in variables:
            metadata = self._md.getVectorElements(
                jvar
            ).getVectornumericElements()
            ts = [_Timestamp2float(tt) for tt in metadata]
            #            vv=[dict([(aa.key,aa.value) for aa in a.iterator()])
            #                    for a in metadata.values()]
            vv = [
                [aa.getValue() for aa in a.iterator()]
                for a in metadata.values()
            ]
            out[jvar.getVariableName()] = ts, vv
        return out


class Hierarchy(object):
    def __init__(self, name, obj, src, varsrc, vardtype):
        self.name = name
        self.obj = obj
        self.varsrc = varsrc
        self.vardatatype = vardtype
        if src is not None:
            self.src = src
        for vvv in self._get_vars():
            if len(vvv) > 0:
                setattr(self, self._cleanName(vvv), vvv)

    def _get_childs(self):
        if self.obj is None:
            objs = self.src.getHierachies(1)
        else:
            objs = self.src.getChildHierarchies(self.obj)
        return dict(
            [(self._cleanName(hh.getHierarchyName()), hh) for hh in objs]
        )

    def _cleanName(self, s):
        if s[0].isdigit():
            s = "_" + s
        out = []
        for ss in s:
            if ss in " _-;></:.":
                out.append("_")
            else:
                out.append(ss)
        return "".join(out)

    def __getattr__(self, k):
        if k == "src":
            self.src = self.varsrc.getAllHierarchies()
            return self.src
        elif k == "_dict":
            self._dict = self._get_childs()
            return self._dict
        else:
            return Hierarchy(k, self._dict[k], self.src, self.varsrc, self.vardatatype)

    def __dir__(self):
        if jpype.isThreadAttachedToJVM() == 0:
            jpype.attachThreadToJVM()
        v = sorted(
            [self._cleanName(i) for i in self._get_vars() if len(i) > 0]
        )
        return sorted(self._dict.keys()) + v

    def __repr__(self):
        if self.obj is None:
            return "<Top Hierarchy>"
        else:
            name = self.obj.getHierarchyName()
            desc = self.obj.getDescription()
            return "<{0}: {1}>".format(name, desc)

    def _get_vars(self):

        VariableDataType = self.vardatatype
        #VariableDataType = jpype.JPackage(
        #    "cern"
        #).accsoft.cals.extr.domain.core.constants.VariableDataType


        if self.obj is not None:
            vvv = self.varsrc.getVariablesOfDataTypeAttachedToHierarchy(
                self.obj, VariableDataType.ALL
            )
            return vvv.toString()[1:-1].split(", ")
        else:
            return []

    def get_vars(self):
        return self._get_vars()
