from pagestore import *

db=PageStore('test.db')

name='var'
idx=range(3)
rec=['123','232','123666666']
db.store_variable(name,idx,rec)
db.get_variable('var')

rec=['123','232','333']
db.store_variable(name,idx,rec)
db.get_variable('var')


db.delete()
