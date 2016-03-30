#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

# should be done before importing pytimber
logging.basicConfig(level=logging.INFO)

import pytimber

ldb = pytimber.LoggingDB()

t1 = '2016-03-28 00:00:00.000'
t2 = '2016-03-28 23:59:59.999'


d = ldb.get('LHC.BOFSU:BPM_NAMES_H', t1, t2)

t1 = '2016-03-28 04:50:00.000'
t2 = '2016-03-28 05:01:00.000'
d=ldb.get('LHC.BSRT.5R4.B1:FIT_POSITION_H',t1,t2)


