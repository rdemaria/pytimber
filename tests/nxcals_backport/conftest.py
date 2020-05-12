import pytest
import logging
import pytimber
from pytimber.sparkresources import SparkResources

# should be done before importing pytimber
logging.basicConfig(level=logging.INFO)


def pytest_addoption(parser):
    parser.addoption(
        "--runcore",
        action="store_true",
        default=False,
        help="run core tests only",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "core: mark test as essential for running"
    )
    config.addinivalue_line("markers", "unit: mark class for unit tests")
    config.addinivalue_line(
        "markers", "integration: mark class for integration tests"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runcore"):
        skip_not_core = pytest.mark.skip(reason="not marked as a core test")
        for item in items:
            if "core" not in item.keywords:
                item.add_marker(skip_not_core)


@pytest.fixture(scope="session")
def nxcals():
    return pytimber.LoggingDB(source="nxcals", sparkconf=SparkResources.SMALL.name) #, sparkconf="small"
