#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import re

with open('README.rst') as f:
    readme = f.read()

requirements = [
    "celery",
    "redis"
]

__version__ = ''
with open('celery_once/__init__.py', 'r') as fd:
    reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
    for line in fd:
        m = reg.match(line)
        if m:
            __version__ = m.group(1)
            break

if not __version__:
    raise RuntimeError('Cannot find version information')



setup(
    name='celery_once',
    version=__version__,
    description='Allows you to prevent multiple execution and queuing of celery tasks.',
    long_description=readme,
    author='Cameron Maske',
    author_email='cam@trackmaven.com',
    url='https://github.com/trackmaven/celery-once',
    packages=find_packages(),
    install_requires=requirements,
    license="BSD",
    keywords='celery, mutex, once, lock, redis',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: System :: Distributed Computing'
    ],
)
