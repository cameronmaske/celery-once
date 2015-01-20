#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


readme = open('README.md').read()
history = open('HISTORY.md').read()

requirements = [
    "celery",
    "redis"
]

test_requirements = [
    "pytest",
    "pytest-cov",
    "python-coveralls",
    "mock==1.0.1"
    "tox"
]

setup(
    name='celery_once',
    version='0.0.1',
    description='A celery extension to ensure only one tasks is run at a time',
    long_description=readme + '\n\n' + history,
    author='Cameron Maske',
    author_email='cam@trackmaven.com',
    url='https://github.com/trackmaven/celery_once',
    packages=[
        'celery_once',
    ],
    package_dir={'celery_once':
                 'celery_once'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='celery, mutex, once',
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
    ],
)
