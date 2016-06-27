#!/usr/bin/env python
"""Setup script for the project."""

from __future__ import print_function

import codecs
import os

from setuptools import setup

NAME = 'sphinxcontrib-versioning'
VERSION = '0.0.1'


def readme():
    """Try to read README.rst or return empty string if failed.

    :return: File contents.
    :rtype: str
    """
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), 'README.rst'))
    handle = None
    url_prefix = 'https://raw.githubusercontent.com/Robpol86/{name}/v{version}/'.format(name=NAME, version=VERSION)
    try:
        handle = codecs.open(path, encoding='utf-8')
        return handle.read(131072).replace('.. image:: docs', '.. image:: {0}docs'.format(url_prefix))
    except IOError:
        return ''
    finally:
        getattr(handle, 'close', lambda: None)()


setup(
    author='@Robpol86',
    author_email='robpol86@gmail.com',
    classifiers=[
        'Private :: Do Not Upload',
    ],
    description='Sphinx extension that allows building versioned docs for self-hosting.',
    entry_points={'console_scripts': ['sphinx-versioning = sphinxcontrib.versioning.__main__:entry_point']},
    install_requires=['docoptcfg', 'sphinx'],
    keywords='sphinx versioning versions version branches tags',
    license='MIT',
    long_description=readme(),
    name=NAME,
    packages=[NAME.split('-')[0]],
    url='https://github.com/Robpol86/' + NAME,
    version=VERSION,
    zip_safe=True,
)
