from pagestore import *
from numpy import *

from numpy.random import *

def mkrnd(calls=10,rng=100,test=True,pagedir='testdata'):
    db=PageStore('test.db',pagedir=pagedir)
    for cc in range(calls):
      a=randint(rng)
      b=a+randint(rng)
      step=randint(1,3)
      idx=arange(a,b+3,step)
      rec=rand(len(idx))
      print cc,a,b,step
      db.store('var',idx,rec)
      if test:
        for i,r in zip(idx,rec):
          [[ii],[rr]]=db.get('var',i,i)
          assert ii==i
          assert rr==r
    return db

db=mkrnd(30,100,test=True)

db.delete()

