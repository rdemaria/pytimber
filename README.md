# pagestore
Database of pages


```python

import pagestore



db=pagestore.PageStore('/data/lhc/test/eos/project/abpdata/lhc.db',
             '/data/lhc/test/eos/project/abpdata/datadb/')

db.search('%BBQ%')

t1,t2=db.get_lim('LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H')

t1,t2=db.get_lim('LHC.BQBBQ.CONTINUOUS.B1:ACQ_DATA_H')

print pagestore.dumpdate(t1)
print pagestore.dumpdate(t2)


data=db.get('LHC.BQBBQ.CONTINUOUS.B1:ACQ_DATA_H',t1,t1+1000)
``` 
