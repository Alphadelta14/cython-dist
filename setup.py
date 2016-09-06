#!/usr/bin/env python
"""
cython-dist

Setuptools Cythonized Builds

2016 Alphadelta14 <alpha@alphservcomputing.solutions>
"""

from __future__ import print_function

import os

from setuptools import setup, find_packages


with open('requirements.txt') as req_file:
    requirements = []
    for line in req_file:
        line = line.split('#', 1)[0].strip()
        if line:
            requirements.append(line)


__version__ = '0.1.0'  # Overwritten below
with open('cython_dist/version.py') as handle:
    exec(handle.read())  # pylint: disable=exec-used

setup(
    name='cython-dist',
    version=__version__,
    description='Setuptools Cythonized Building',
    url='https://github.com/Alphadelta14/cython-dist',
    author='Alphadelta14',
    author_email='alpha@alphaservcomputing.solutions',
    license='Other/Proprietary License',
    install_requires=requirements,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'License :: Other/Proprietary License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
