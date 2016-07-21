#!/usr/bin/env python

from setuptools import setup

setup(
    name='txwrapplog',
    version='0.1.0',
    py_modules=['txwrapplog'],
    install_requires=[
        'twisted',
    ],
    zip_safe=False,
)