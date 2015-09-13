#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand  # noqa

TEST_REQUIREMENTS = ['pytest', 'pytz']
EXTRA_REQUIREMENTS = ['python-dateutil', 'simplejson']


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--verbose', 'tests/']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ''
    with open(fname, 'r') as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError('Cannot find version information')
    return version

__version__ = find_version("marshmallow/__init__.py")


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content

setup(
    name='marshmallow',
    version=__version__,
    description=('A lightweight library for converting complex '
                'datatypes to and from native Python datatypes.'),
    long_description=read('README.rst'),
    author='Steven Loria',
    author_email='sloria1@gmail.com',
    url='https://github.com/marshmallow-code/marshmallow',
    packages=find_packages(exclude=('test*', 'examples')),
    package_dir={'marshmallow': 'marshmallow'},
    include_package_data=True,
    tests_require=TEST_REQUIREMENTS,
    extras_require={'reco': EXTRA_REQUIREMENTS},
    license=read('LICENSE'),
    zip_safe=False,
    keywords=('serialization', 'rest', 'json', 'api', 'marshal',
        'marshalling', 'deserialization', 'validation', 'schema'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    test_suite='tests',
    cmdclass={'test': PyTest},
)
