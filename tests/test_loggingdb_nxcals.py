#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

# should be done before importing pytimber
logging.basicConfig(level=logging.INFO)

import pytimber

ldb = pytimber.LoggingDB(source="nxcals")


def test_search():
    variables = ldb.search("HX:BETA%")
    assert "HX:BETASTAR_IP1" in variables
    assert len(variables) == 4


def test_get_simple():
    t1 = "2015-05-13 12:00:00.000"
    t2 = "2015-05-15 00:00:00.000"
    data = ldb.get("HX:FILLN", t1, t2)

    t, v = data["HX:FILLN"]
    assert len(t) == 6
    assert len(v) == 6

    assert t[0] == 1431523684.764
    assert v[0] == 3715.0


def test_getVariable():
    t1 = "2015-05-13 12:00:00.000"
    t2 = "2015-05-15 00:00:00.000"
    t, v = ldb.getVariable("HX:FILLN", t1, t2)

    assert len(t) == 6
    assert len(v) == 6

    assert t[0] == 1431523684.764
    assert v[0] == 3715.0


def test_get_unixtime():
    t1 = "2015-05-13 12:00:00.000"
    t2 = "2015-05-15 00:00:00.000"
    data = ldb.get("HX:FILLN", t1, t2, unixtime=False)
    t, v = data["HX:FILLN"]
    import datetime

    assert t[0] == datetime.datetime(2015, 5, 13, 15, 28, 4, 764000)


def test_get_vectornumeric():
    t1 = "2015-05-13 12:00:00.000"
    t2 = "2015-05-13 12:00:01.000"
    data = ldb.get("LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H", t1, t2)

    t, v = data["LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H"]

    for vv in v:
        assert len(vv) == 4096

def test_get_vectorstring():
    t1 = "2016-03-28 00:00:00.000"
    t2 = "2016-03-28 23:59:59.999"

    t, v = ldb.getVariable("LHC.BOFSU:BPM_NAMES_H", t1, t2)
    assert v[0][123] == "BPM.16L3.B1"


def test_getScaled():
    t1 = "2015-05-15 12:00:00.000"
    t2 = "2015-05-15 15:00:00.000"
    data = ldb.getScaled(
        "MSC01.ZT8.107:COUNTS",
        t1,
        t2,
        scaleInterval="HOUR",
        scaleAlgorithm="SUM",
        scaleSize="1",
    )

    t, v = data["MSC01.ZT8.107:COUNTS"]

    import numpy as np

    assert (v[:4] - np.array([1174144.0, 1172213.0, 1152831.0])).sum() == 0


def test_Timestamp():
    import time

    now = time.time()
    ts_now = ldb.toTimestamp(now)
    now2 = ldb.fromTimestamp(ts_now, unixtime=True)
    dt_now2 = ldb.fromTimestamp(ts_now, unixtime=False)
    assert now == now2
    assert str(ts_now)[:25] == dt_now2.strftime("%Y-%m-%d %H:%M:%S.%f")[:25]

    time_str = "2015-10-12 12:12:32.453255123"
    ta = ldb.toTimestamp(time_str)
    assert ta.toLocaleString() == "Oct 12, 2015 12:12:32 PM"
    unix = ldb.fromTimestamp(ta, unixtime=True)
    assert unix == 1444644752.4532552
    assert (
        time.strftime("%b %-d, %Y %-I:%M:%S %p", time.localtime(unix))
        == "Oct 12, 2015 12:12:32 PM"
    )


def test_hierarchy():
    assert hasattr(ldb.tree.LHC, "Beam_Instrumentation")


def test_getUnit():
    units = ldb.getUnit("%:LUMI_TOT_INST")
    assert units["ATLAS:LUMI_TOT_INST"] == "Hz/ub"


def test_getDescription():
    units = ldb.getDescription("%:LUMI_TOT_INST")
    assert (
        units["ATLAS:LUMI_TOT_INST"]
        == "ATLAS: Total instantaneous luminosity summed over all bunches"
    )


def test_fundamentals():
    fundamental = "CPS:%:SFTPRO%"
    t1 = "2015-05-15 12:00:00.000"
    t2 = "2015-05-15 12:01:00.000"
    t, v = ldb.getVariable("CPS.TGM:USER", t1, t2, fundamental=fundamental)
    assert v[0] == "SFTPRO2"


def test_getStats():
    t1 = "2016-03-01 00:00:00.000"
    t2 = "2016-04-03 00:00:00.000"

    vn = "LHC.BOFSU:EIGEN_FREQ_2_B1"
    stat = ldb.getStats(vn, t1, t2)[vn]

    assert stat.MinTstamp == 1457962796.971
    assert stat.StandardDeviationValue == 0.00401594
