from numpy import *
from pagestore import *

db=PageStore('test.db','testdata')

name='var'
idx=range(3)
rec=['123','232','123']
db.store_variable(name,idx,rec)
print(db.get_variable('var'))

rec=['123','232','333123441']
db.store_variable(name,idx,rec)
print(db.get_variable('var'))

rec=array(['123','232','333'],dtype='U')
db.store_variable(name,idx,rec)
print(db.get_variable('var'))

rec=[['123','123412'],['232','4241','fdasfa'],['333','434123']]

db.store_variable(name,idx,rec)
print(db.get_variable('var'))

db.delete()
