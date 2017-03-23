import time

from pytimber.pagestore import *
from numpy import *

from numpy.random import *

def mkdata(nvar=5, maxvarnames=10,maxrecsize=150,reclen=10,istartmax=1000):
    data={}
    for vv in range(nvar):
      size=[-1,1,maxrecsize,randint(maxrecsize)][randint(4)]
      rectype=['U','int','float'][randint(3)]
      vname='var'+str(randint(maxvarnames))+rectype
      if size==-1:
          record=[rand(randint(maxrecsize)).astype(rectype)
                                      for x in range(reclen)]
      else:
          record=[rand(size).astype(rectype) for x in range(reclen)]
      istart=randint(istartmax)
      idx=range(istart,istart+reclen)
      data[vname]=(idx,record)
    return data


class DictDB(object):
    def get_var(self,name):
        return getattr(self,name,([],[]))
    def get(self):
        return self.__dict__
    def store(self,data):
        for name,(idx,rec) in data.items():
            new=dict(zip(*self.get_var(name)))
            for i,v in zip(idx,rec):
                new[i]=v
            idx,rec=zip(*sorted(new.items()))
            idx=array(idx);rec=array(rec)
            setattr(self,name,(idx,rec))

def check_data(a,b):
    if not set(a.keys())==set(b.keys()):
        print(a.keys())
        print(b.keys())
        return False
    for name,(idx,rec) in a.items():
        nidx,nrec=b[name]
        assert len(idx)==len(nidx)
        assert len(rec)==len(rec)
        assert list(idx)==list(nidx)
        for av,bv in zip(rec,nrec):
            if hasattr(av,'all'):
              if not (av==bv).all():
                print(name,av[0])
                print(name,bv[0])
                return False
            else:
              if not av==bv:
                  print(name,av)
                  print(name,av)
                  return False
    return True


a=DictDB()
try:
  b=PageStore('test.db','testdata',maxpagesize=100,keep_deleted_pages=True)
  data=mkdata()
  a.store(data)
  check_data(data,a.get())
  b.store(data)
  check_data(data,b.get('%'))
  check_data(a.get(),b.get('%'))
  for n in range(10):
    data=mkdata()
    a.store(data)
    b.store(data)
    check_data(a.get(),b.get('%'))
except Exception as e:
  raise e
finally:
  b.delete()
