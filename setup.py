#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
from setuptools.command.install import install as _install

import pytimber


class install(_install):
    '''Install and perform the jar resolution'''
    def run(self):
        import cmmnbuild_dep_manager
        mgr = cmmnbuild_dep_manager.Manager()
        mgr.install('pytimber')
        print('registered pytimber with cmmnbuild_dep_manager')
        super().run(self)

setuptools.setup(
    name='pytimber',
    version=pytimber.__version__,
    description='A Python wrapping of CALS API',
    author='Riccardo De Maria',
    author_email='riccardo.de.maria@cern.ch',
    url='https://github.com/rdemaria/pytimber',
    packages=['pytimber'],
    package_dir={
        'pytimber': 'pytimber'
    },
    setup_requires=[
        'cmmnbuild-dep-manager'
    ],
    install_requires=[
        'numpy',
        'JPype1',
        'cmmnbuild-dep-manager'
    ],
    cmdclass={
        'install': install
    },
    zip_safe=False
)
