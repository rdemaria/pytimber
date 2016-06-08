__version__ = "2.1.10"

cmmnbuild_deps = [
    "accsoft-cals-extr-client"
]

# When running setuptools without required dependencies installed
# we need to be able to access __version__, so print a warning but
# continue
try:
    from .pytimber import LoggingDB
    from .dataquery import DataQuery, parsedate, dumpdate, \
                           flattenoverlap,set_xaxis_date, \
                           set_xaxis_utctime, set_xlim_date, get_xlim_date
    from . import timberdata
except ImportError:
    import logging
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.warning("required dependencies are not installed")
