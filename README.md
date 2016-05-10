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
