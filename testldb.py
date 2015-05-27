import pytimber

ldb=pytimber.LDB()


ldb.search('HX:%')

t1='2015-05-13 00:00:00.000'
t2='2015-05-15 00:00:00.000'
d=ldb.get('HX:FILLN',t1,t2)
d=ldb.get('HX:BMODE_%',t1,t2)

t1='2015-05-13 12:00:00.000'
t2='2015-05-13 12:00:01.000'
d=ldb.get('LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H',t1,t2)



ldb.tree
dir(ldb.tree)
ldb.tree.LHC.Collimators.BPM.bpmColl.get_vars()


