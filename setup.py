#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import os
from setuptools import setup, find_packages

from setuptools.command.install import install as _install


def get_version_from_init():
    init_file = os.path.join(
        os.path.dirname(__file__), 'pytimber', '__init__.py'
    )
    with open(init_file, 'r') as fd:
        for line in fd:
            if line.startswith('__version__'):
                return ast.literal_eval(line.split('=', 1)[1].strip())


# Custom install function to install and register with cmmnbuild-dep-manager
class install(_install):
    '''Install and perform the jar resolution'''
    user_options = _install.user_options + [
        ('no-jars', None, 'do not register with cmmnbuild_dep_manager')
    ]

    def initialize_options(self):
        self.no_jars = False
        _install.initialize_options(self)

    def run(self):
        try:
            import pagestore
            import pip
            print('WARNING: removing standalone pagestore package')
            pip.main(['uninstall', 'pagestore', '-y'])
        except:
            pass

        if not self.no_jars:
            import cmmnbuild_dep_manager
            mgr = cmmnbuild_dep_manager.Manager()
            mgr.install('pytimber')
            print('registered pytimber with cmmnbuild_dep_manager')
        _install.run(self)


setup(
    name='pytimber',
    version=get_version_from_init(),
    description='A Python wrapping of CALS API',
    author='Riccardo De Maria',
    author_email='riccardo.de.maria@cern.ch',
    url='https://github.com/rdemaria/pytimber',
    packages=find_packages(),
    install_requires=[
        'python-dateutil',
        'JPype1>=0.6.2',
        'cmmnbuild-dep-manager>=2.1.2',
        'matplotlib',
        'pytz',
        'scipy',
    ],
    extras_require={'test': ['pytest']},
    cmdclass={
        'install': install
    }
)
