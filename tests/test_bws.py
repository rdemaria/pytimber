import os
import sys

# sys.path.insert(0,os.getenv('HOME')+"/cernbox/lib/python/pagestore/")
# sys.path.insert(0,os.getenv('HOME')+"/cernbox/lib/python/pytimber/")

import pytimber
from pytimber import BWS,BSRT
import pytimber.pagestore as pagestore

datadir=os.getenv('HOME')+"/data/MDs/MD2202/datadb"
dbfile_ro=os.getenv('HOME')+"/data/MDs/MD2202/md2202.db"

db=pagestore.PageStore(dbfile_ro,datadir,readonly=True)

t1=pytimber.parsedate("2017-07-01 15:48:00.348")
t2=pytimber.parsedate("2017-07-02 00:12:29.255")

data = BWS.fromdb(t1=t1,t2=t2,db=db)
