from pytimber import *
import time

ldb = pytimber.LoggingDB()

time_str = "2015-10-12 12:12:32.453255123"
print(time_str)
print('------------------------------------------------------------------------')

ta=ldb.toTimestamp(time_str)
print(ta.toLocaleString())
print(ta.getTime(), ta.getNanos())
print('------------------------------------------------------------------------')

unix=int(ta.getTime()/1000.0)+ta.getNanos()/1e9
print(unix)
print(time.asctime(time.localtime(unix)))
print('------------------------------------------------------------------------')

tb=ldb.toTimestamp(unix)
print(tb.toLocaleString())
print(tb.getTime(), tb.getNanos())
print('------------------------------------------------------------------------')
