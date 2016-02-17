#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging

# should be done before importing pytimber
logging.basicConfig(level=logging.INFO)

import pytimber

ldb = pytimber.LoggingDB()

print('------------------------------------------------------------------------')

time_str = "2015-10-12 12:12:32.453255123"

print('Original str:')
print('  {}'.format(time_str))

print('------------------------------------------------------------------------')

ta = ldb.toTimestamp(time_str)

print('Passed to toTimestamp() as str:')
print('  {}'.format(ta.toLocaleString()))
print('  {:.0f}.{}'.format(ta.getTime()/1000.0, ta.getNanos()))

print('------------------------------------------------------------------------')

unix = int(ta.getTime()/1000.0) + ta.getNanos()/1e9

print('Converted to float in python:')
print('  {}'.format(time.strftime('%b %-d, %Y %-I:%M:%S %p', time.localtime(unix))))
print('  {}'.format(unix))

print('------------------------------------------------------------------------')

tb = ldb.toTimestamp(unix)

print('Passed to toTimestamp() as float:')
print('  {}'.format(tb.toLocaleString()))
print('  {:.0f}.{}'.format(tb.getTime()/1000.0, tb.getNanos()))

print('------------------------------------------------------------------------')
