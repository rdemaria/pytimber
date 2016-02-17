#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

# should be done before importing pytimber
logging.basicConfig(level=logging.INFO)

import pytimber

ldb = pytimber.LoggingDB(source='ldb')

print('------------------------------------------------------------------------')

print(ldb.search('HX:BETA%'))

print('------------------------------------------------------------------------')

t1 = '2015-05-13 00:00:00.000'
t2 = '2015-05-15 00:00:00.000'
d = ldb.get('HX:FILLN', t1, t2)
print(d)

print('------------------------------------------------------------------------')

d = ldb.get('HX:FILLN', t1, t2, unixtime=False)
print(d)

print('------------------------------------------------------------------------')

t1 = '2015-05-13 12:00:00.000'
t2 = '2015-05-13 15:00:00.000'
d = ldb.get(ldb.search('HX:BETA%'), t1, t2, unixtime=True)
print(d)

print('------------------------------------------------------------------------')

t1 = '2015-05-13 12:00:00.000'
t2 = '2015-05-13 12:00:01.000'
d = ldb.get('LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H', t1, t2)
print(d)

print('------------------------------------------------------------------------')

print(dir(ldb.tree))

print('------------------------------------------------------------------------')

print(ldb.tree.LHC.Collimators.BPM.bpmColl.get_vars()[:10])

print('------------------------------------------------------------------------')
