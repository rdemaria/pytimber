# pytimber
Python Wrapping of CALS API

Usage

    import pytimber

    ldb=pytimber.LoggingDB()


     print ldb.search('HX:BETA%')

     t1='2015-05-13 00:00:00.000'
    t2='2015-05-15 00:00:00.000'
    d=ldb.get('HX:FILLN',t1,t2)
    print d

    t1='2015-05-13 12:00:00.000'
   t2='2015-05-13 12:00:01.000'
   d=ldb.get('LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H',t1,t2)

   print d


   ldb.tree
   print dir(ldb.tree)
   print ldb.tree.LHC.Collimators.BPM.bpmColl.get_vars()
