#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

# should be done before importing pytimber
logging.basicConfig(level=logging.INFO)

import pytimber

ldb = pytimber.LoggingDB(source='ldb')

def test_search():
   variables=ldb.search('HX:BETA%')
   assert 'HX:BETASTAR_IP1' in variables
   assert len(variables)==4

def test_get_simple():
    t1 = '2015-05-13 12:00:00.000'
    t2 = '2015-05-15 00:00:00.000'
    data = ldb.get('HX:FILLN', t1, t2)

    t,v= data[ 'HX:FILLN' ]
    assert len(t)==6
    assert len(v)==6

    assert t[0]==1431523684.764
    assert v[0]==3715.

def test_get_unixtime():
    t1 = '2015-05-13 12:00:00.000'
    t2 = '2015-05-15 00:00:00.000'
    data = ldb.get('HX:FILLN', t1, t2, unixtime=False)
    t,v= data[ 'HX:FILLN' ]
    import datetime

    assert  t[0]==  datetime.datetime(2015, 5, 13, 15, 28, 4, 764000)

def test_get_vectonumeric():
    t1 = '2015-05-13 12:00:00.000'
    t2 = '2015-05-13 12:00:01.000'
    data = ldb.get('LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H', t1, t2)

    t,v = data['LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H']

    for vv in v:
        assert len(vv)==4096

def test_getScaled():
    t1 = '2015-05-15 12:00:00.000'
    t2 = '2015-05-15 15:00:00.000'
    data = ldb.getScaled('MSC01.ZT8.107:COUNTS',t1,t2,
            scaleInterval='HOUR',scaleAlgorithm='SUM',scaleSize='1')

    t,v =data['MSC01.ZT8.107:COUNTS']

    import numpy as np

    assert (v[:4] - np.array([1174144., 1172213., 1152831.])).sum()==0


def test_Timestamp():
    import time
    now=time.time()
    ts_now=ldb.toTimestamp(now)
    now2=ldb.fromTimestamp(ts_now,unixtime=True)
    dt_now2=ldb.fromTimestamp(ts_now,unixtime=False)
    assert now==now2
    assert str(ts_now)[:26]==dt_now2.strftime("%Y-%m-%d %H:%M:%S.%f")[:26]




