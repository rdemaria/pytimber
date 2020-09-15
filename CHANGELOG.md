# pytimber changelog
### 3.0.3
  Add support for new data conversion methods spark2numpy and spark2pandas [V. Baggiolini] 

### 3.0.2
  Add spark context support [P. Sowinski]
  Add check nxcals version [R. De Maria]
  Add matrixnumeric support for nxcals [R. De Maria]

### 3.0.0
  Add NXCALS support
  Requiring Python >=3.6
  Removing getVariables and getVariablesList
  Requiring >=0.7.1

### 2.8.0
  Fix incompatibility with Jpype 0.7.x

### 2.7.1 (L. Coyle)

  Reworked the LHCBSRT and LHCBWS classes.

  LHCBSRT:

  * Data processing makes use of pandas DataFrames
  * Output data is now a MultiIndex DataFrame instead of a dict of structured arrays

  The plotting could be improved by making use of DataFrame plotting functionalities.

  LHCBWS:

  * PEP 8 compliance
  * Separated the gaussian fitting from the data fetching
  * Improved gaussian fitting 
  * Output format is a MultiIndex DataFrame of the compatible data and a dict of structured arrays (the original data format) for the rest

  toolbox:

  * PEP8 compliance

  dataquery:

  * PEP8 compliance

Added examples/BWSExample.ipynb to provide some example usages of LHCBWS

Added an example of emittance plotting with error bars estimates in examples/BSRTExample.ipynb.


### 2.7.0

  * Fix PEP8 issues in LHCBSRT


### 06/2016 (T. Levens)

  * Now requires cmmnbuild_dep_manager.

### 04/2016 (T. Levens)

  * Added functions to get LHC fill information.

### 01/2016 (T. Levens)

  * Updated repository structure
  * Added setup.py for setuptools/pip installation
  * Added support for the (in progress) [.jar management system](https://gitlab.cern.ch/bi/cmmnbuild-dep-manager)
    which allows better cohabitation with PyJapc.
  * By default, if this module is not installed then the bundled .jar file is
    used as before.

### 12/2015 (C. Hernalsteens)

Merged from my own package. The API should be identical, except for the new
functionalities that should be transparent for existing use.

  * Developed for use with 'cycled' machines (PSB, PS, SPS)
  * Filtering by fundamental data
  * Aligned datasets (*getAligned()*)
  * (minor) Support for MATRIXNUMERIC datatype
  * (minor) Split some functions into smaller pieces

### 10/2015 (M. Betz)

Documentation (=examples) in pyTimberExamples.ipynb

Applied some changes to integrate pyTimber in the BI Anaconda installation.

  * Made compatible with Python3
  * Simplified the return value (less nesting of lists in dicts, etc.)
  * Specify a point in time or over a time range
