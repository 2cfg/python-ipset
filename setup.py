#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='python-ipset',
    version='0.0.1',
    packages=find_packages(),
    url='https://github.com/Lukasa/python-ipset',
    license='GPLv2',
    install_requires=[
        'ipaddress',
    ],
    author='Cory Benfield',
    author_email='cory@lukasa.co.uk',
    description='A Python wrapper around libipset.'
)
