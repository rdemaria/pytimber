#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ast
import setuptools
from setuptools.command.install import install as _install

def get_version_from_init():
    init_file = os.path.join(
        os.path.dirname(__file__), 'pytimber', '__init__.py'
    )
    with open(init_file, 'r') as file:
        for line in file:
            if line.startswith('__version__'):
                return ast.literal_eval(line.split('=', 1)[1].strip())


class install(_install):
    '''Install and perform the jar resolution'''
    def run(self):
        import cmmnbuild_dep_manager
        mgr = cmmnbuild_dep_manager.Manager()
        mgr.install('pytimber')
        print('registered pytimber with cmmnbuild_dep_manager')
        _install.run(self)

setuptools.setup(
    name='pytimber',
    version=get_version_from_init(),
    description='A Python wrapping of CALS API',
    author='Riccardo De Maria',
    author_email='riccardo.de.maria@cern.ch',
    url='https://github.com/rdemaria/pytimber',
    packages=['pytimber'],
    package_dir={
        'pytimber': 'pytimber'
    },
    setup_requires=[
        'cmmnbuild-dep-manager>=1.2.9'
    ],
    install_requires=[
        'JPype1>=0.6.1',
        'cmmnbuild-dep-manager>=1.2.9'
    ],
    cmdclass={
        'install': install
    }
)
