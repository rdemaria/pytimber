from pytimber import *
import time


ta=toTimeStamp("2015-10-12 12:12:32.453255")

unix=ta.getTime()/1000.

time.asctime(time.localtime(unix))

tb=toTimeStamp(unix)



