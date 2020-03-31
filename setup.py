#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import os
from setuptools import setup, find_packages

from setuptools.command.install import install as _install


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
    author="Riccardo De Maria",
    author_email="riccardo.de.maria@cern.ch",
    url="https://github.com/rdemaria/pytimber",
    packages=find_packages(),
    python_requires=">=3.6, <4",
    install_requires=[
        "python-dateutil",
        "JPype1>=0.7.1",
        "cmmnbuild-dep-manager>=2.4.0",
        "matplotlib",
        "pytz",
        "scipy",
        "six",
        "numpy",
    ],
    extras_require={"dev": ["pytest"]},
    entry_points={
        # Register with cmmnbuild_dep_manager.
        "cmmnbuild_dep_manager": [f"pytimber={VERSION}"],
    },
)
