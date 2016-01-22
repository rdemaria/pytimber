# pytimber changelog

## 01/2016 (T. Levens)

  * Updated repository structure
  * Added setup.py for setuptools/pip installation
  * Added support for the (in progress) [.jar management system](https://gitlab.cern.ch/bi/cmmnbuild-dep-manager)
    which allows better cohabitation with PyJapc.
  * By default, if this module is not installed then the bundled .jar file is used as before.

## 10/2015 (M. Betz)

Documentation (=examples) in pyTimberExamples.ipynb

Applied some changes to integrate pyTimber in the BI Anaconda installation.

  * Made compatible with Python3
  * Simplified the return value (less nesting of lists in dicts, etc.)
  * Specify a point in time or over a time range
