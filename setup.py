#!/usr/bin/env python

import setuptools
from setuptools.command.install import install as _install

import pagestore

setuptools.setup(
    name='pagestore',
    version="0.0.7",
    description='Database of pages of data',
    author='Riccardo De Maria',
    author_email='riccardo.de.maria@cern.ch',
    url='https://github.com/rdemaria/pagestore',
    packages=['pagestore'],
    package_dir={'pagestore': 'pagestore'},
    install_requires=['numpy'],
)


