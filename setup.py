#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
from setuptools.command.install import install as _install

import pytimber


class install(_install):
    def run(self):
        try:
            import cmmnbuild_dep_manager
            mgr = cmmnbuild_dep_manager.Manager()
            mgr.install('pytimber')
            print('registered pytimber with cmmnbuild_dep_manager')
        except ImportError:
            pass
        _install.run(self)

setuptools.setup(
    name='pytimber',
    version=pytimber.__version__,
    description='A Python wrapping of CALS API',
    author='Riccardo De Maria',
    author_email='riccardo.de.maria@cern.ch',
    url='https://github.com/rdemaria/pytimber',
    packages=['pytimber'],
    package_dir={'pytimber': 'pytimber'},
    install_requires=['JPype1>=0.6.1'],
    cmdclass={'install': install},
    package_data={'pytimber': ['jars/*']},
    zip_safe=False
)
