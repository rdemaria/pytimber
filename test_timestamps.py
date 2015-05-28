from pytimber import *
import time


ta=toTimeStamp("2015-10-12 12:12:32.453255123")

unix=int(ta.getTime()/1000.)+ta.getNanos()/1e9

time.asctime(time.localtime(unix))

tb=toTimeStamp(unix)

ta.getNanos()
ta.getTime()
ta.toLocaleString()

tb.getNanos()
tb.getTime()
tb.toLocaleString()

