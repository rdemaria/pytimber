"""
setup.py for pytimber.

For reference see
https://packaging.python.org/guides/distributing-packages-using-setuptools/

"""
import ast
import os
from pathlib import Path
from setuptools import setup, find_packages


HERE = Path(__file__).parent.absolute()
with (HERE / 'README.md').open('rt') as fh:
    LONG_DESCRIPTION = fh.read().strip()


REQUIREMENTS: dict = {
    'core': [
        "python-dateutil",
        "JPype1>=0.7.1",
        "cmmnbuild-dep-manager>=2.4.0",
        "matplotlib",
        "pytz",
        "scipy",
        "six",
        "numpy",
    ],
    'test': [
        'pytest',
    ],
}


def get_version_from_init():
    init_file = os.path.join(
        os.path.dirname(__file__), "pytimber", "__init__.py"
    )
    with open(init_file, "r") as fd:
        for line in fd:
            if line.startswith("__version__"):
                return ast.literal_eval(line.split("=", 1)[1].strip())


VERSION = get_version_from_init()

setup(
    name="pytimber",
    version=VERSION,
    description="A Python wrapping of CALS API",
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',

    maintainer="CERN BE-CO-APS",
    maintainer_email="acc-logging-support@cern.ch",
    author="Riccardo De Maria",
    author_email="riccardo.de.maria@cern.ch",
    url="https://gitlab.cern.ch/scripting-tools/pytimber",
    packages=find_packages(exclude="tests"),

    python_requires="~=3.6",
    install_requires=REQUIREMENTS['core'],
    extras_require={
        **REQUIREMENTS,
        # The 'dev' extra is the union of 'test' and 'doc', with an option
        # to have explicit development dependencies listed.
        'dev': [req
                for extra in ['dev', 'test', 'doc']
                for req in REQUIREMENTS.get(extra, [])],
        # The 'all' extra is the union of all requirements.
        'all': [req for reqs in REQUIREMENTS.values() for req in reqs],
    },

    entry_points={
        # Register with cmmnbuild_dep_manager.
        "cmmnbuild_dep_manager": [f"pytimber={VERSION}"],
    },
)
