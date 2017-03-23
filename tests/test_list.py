from numpy import *
from pagestore import *

db=PageStore('test.db','testdata')

data={'v1':([1,2,3],[4,5,6]),
      'v2':([1,2,3],[4,5,6])}

db.store(data)
data1=db.get(['v1','v2'])
data2=db.get('v%')

print set(data1.keys())==set(data1.keys())


db.delete()
