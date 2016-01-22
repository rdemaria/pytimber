#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

import pytimber

setuptools.setup(
    name='pytimber',
    version=pytimber.__version__,
    description='A Python wrapping of CALS API',
    author='Riccardo De Maria',
    author_email='riccardo.de.maria@cern.ch',
    url='https://github.com/rdemaria/pytimber',
    packages=['pytimber'],
    package_dir={'pytimber': 'pytimber'},
    install_requires=[ 'JPype1>=0.6.1' ],
    package_data={'pytimber': ['jars/*']},
    zip_safe=False
)

