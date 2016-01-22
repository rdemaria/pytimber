__version__ = "1.0.0"

# When running setuptools without required dependencies installed
# we need to be able to access __version__, so print a warning but
# continue
try:
    from .pytimber import LoggingDB
except ImportError:
    import logging
    logging.basicConfig()
    log = logging.getLogger(__name__)
    log.warn("required dependencies are not installed")
