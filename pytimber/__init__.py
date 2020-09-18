# -*- coding: utf-8 -*-

from .pytimber import LoggingDB
from .dataquery import (
    DataQuery,
    parsedate,
    dumpdate,
    flattenoverlap,
    set_xaxis_date,
    set_xaxis_utctime,
    set_xlim_date,
    get_xlim_date,
)
from .LHCBSRT import BSRT
from .LHCBWS import BWS

from . import timberdata

from .pagestore import PageStore

from .nxcals import NXCals
from .check_kerberos import check_kerberos
from .sparkresources import SparkResources

__version__ = "3.0.3"

__cmmnbuild_deps__ = [
    "pytimber-utils",
    #    "accsoft-cals-extr-client",
    #    "accsoft-cals-extr-domain",
    "nxcals-backport-api",  # needed although it is also in pytimber-utils
    #    "lhc-commons-cals-utils",
    #    "slf4j-log4j12",
    #    "slf4j-api",
    #    "log4j",
    # {"product": "jackson-databind", "version": "2.9.8"},
    # {"product": "jackson-core", "version": "2.9.8"},
    # {"product": "jackson-datatype-guava", "version": "2.9.8"},
    # {"product": "jackson-datatype-jsr310", "version": "2.9.8"},
    # {"product": "jackson-annotations", "version": "2.9.8"},
    # {"product": "jackson-dataformat-yaml", "version": "2.9.8"},
    # {"product": "jackson-datatype-jdk8", "version": "2.9.8"},
    # {"product": "jackson-module-parameter-names", "version": "2.9.8"},
    # {"product": "jackson-module-paranamer", "version": "2.9.8"},
    #    {"product": "jackson-module-scala", "version": "2.9.8"},
]

__all__ = [
    "LoggingDB",
    "DataQuery",
    "parsedate",
    "dumpdate",
    "flattenoverlap",
    "set_xaxis_date",
    "set_xaxis_utctime",
    "set_xlim_date",
    "get_xlim_date",
    "BSRT",
    "BWS",
    "timberdata",
    "PageStore",
    "NXCals",
    "check_kerberos",
]

# workaround for missing keyword
# see (https://github.com/jpype-project/jpype/issues/540) to be fixed in new version
import jpype

if hasattr(jpype._pykeywords, "_KEYWORDS"):
    jpype._pykeywords._KEYWORDS.add("and")
