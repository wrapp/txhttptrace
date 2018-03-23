#!/usr/bin/env python

from setuptools import setup

setup(
    name='txhttptrace',
    version='0.1.0',
    py_modules=['txhttptrace'],
    install_requires=[
        'six',
        'twisted',
    ],
    zip_safe=False,
)