__version__ = "2.1.3"

cmmnbuild_deps = [
    "accsoft-cals-extr-client"
]

# When running setuptools without required dependencies installed
# we need to be able to access __version__, so print a warning but
# continue
try:
    from .pytimber import LoggingDB
except ImportError:
    import logging
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.warning("required dependencies are not installed")
