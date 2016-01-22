# pytimber

A Python wrapping of CALS API.

## Installation

    pip install git+https://github.com/rdemaria/pytimber.git

## Usage

Import

    import pytimber
    ldb=pytimber.LoggingDB()

Search for variables

    print ldb.search('HX:BETA%')

Get data

    t1='2015-05-13 00:00:00.000'
    t2='2015-05-15 00:00:00.000'
    d=ldb.get('HX:FILLN',t1,t2)
    print d
    t1='2015-05-13 12:00:00.000'
    t2='2015-05-13 12:00:01.000'
    d=ldb.get('LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H',t1,t2)
    print d

Explore variable hierarchies

    ldb.tree
    print dir(ldb.tree)
    print ldb.tree.LHC.Collimators.BPM.bpmColl.get_vars()

