import sqlite3


db=sqlite3.connect('testsql.db')
db.execute('CREATE TABLE IF NOT EXISTS test(a,b,c)')


for l in range(10):
  db.execute('INSERT INTO test VALUES (?,?,?)',(l,l*3,l*6))
  print list(db.execute('SELECT * from test'))

