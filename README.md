# Changelog

## 12/2015 (C. Hernalsteens)

Merged from my own package. The API should be identical, except for the new functionalities that should be transparent for existing use.

    * Developed for use with 'cycled' machines (PSB, PS, SPS)
    * Filtering by fundamental data
    * Aligned datasets (*getAligned()*)
    * (minor) Support for MATRIXNUMERIC datatype
    * (minor) Split some functions into smaller pieces

## 10/2015 (M. Betz)

Documentation (=examples) in pyTimberExamples.ipynb

Applied some changes to integrate pyTimber in the BI Anaconda installation.

    * Made compatible with Python3
    * Simplified the return value (less nesting of lists in dicts, etc.)
    * Specify a point in time or over a time range
    
## Original repository from R. De Maria


# pytimber

Python Wrapping of CALS API. 

**Documentation:**

See *pyTimberExamples.pynb*.

**Usage:**

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
