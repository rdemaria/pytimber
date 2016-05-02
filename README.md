# pagestore
Database of pages

## Simple example
```python

import pagestore

db=pagestore.PageStore('data.db','./data')
set1={'var1':([1,2,3,4],[.3,.1,.2,.2])}
set2={'var1':([4,5,6,7],[.5,.6,.7,.9]),
      'var2':([.1,.2,.3,.4],[.3,.1,.2,.2])}

db.store(set1)
db.store(set2)

db.get_info()

db.search('var%')
db.get('var1',3,6)

``` 

## If loogged to lxplus-c6b 
```python

import pagestore

db=pagestore.PageStore('/eos/project/abpdata/lhc/lhc.db',
                       '/eos/project/abpdata/lhc/datadb/')

db.search('%BBQ%')

t1,t2=db.get_lim('LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H')

t1,t2=db.get_lim('LHC.BQBBQ.CONTINUOUS.B1:ACQ_DATA_H')

print pagestore.dumpdate(t1)
print pagestore.dumpdate(t2)


data=db.get('LHC.BQBBQ.CONTINUOUS.B1:ACQ_DATA_H',t1,t1+1000)
``` 
