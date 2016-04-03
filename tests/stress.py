import time

from pagestore import *
from numpy import *

from numpy.random import *

def mkrnd(calls=10,rng=100,test=True):
    db=PageStore('test.db',maxpagesize=100)
    totrec={}
    for cc in range(calls):
      a=randint(rng)
      b=a+randint(rng)
      step=randint(1,3)
      idx=arange(a,b+3,step)
      rec=rand(len(idx))
      print db.get_info()
      db.store({'var':(idx,rec)})
      totrec.update(zip(idx,rec))
      if test:
       for i,r in sorted(totrec.items()):
        out=db.get('var',i,i)['var']
        try:
          [[ii],[rr]]=out
        except ValueError:
          print "Error"
          print out
    return db

db=mkrnd(5,300,test=True)

db.get('var',0,1000)['var']

db.delete()

