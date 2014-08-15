#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

TEST_REQUIREMENTS = ['pytest', 'pytz']


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--verbose']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


def find_version(fname):
    '''Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    '''
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
                'datatypes into native Python datatypes.'),
    long_description=(read("README.rst") + '\n\n' +
                        read("HISTORY.rst")),
    author='Steven Loria',
    author_email='sloria1@gmail.com',
    url='https://github.com/sloria/marshmallow',
    packages=find_packages(exclude=("test*", )),
    package_dir={'marshmallow': 'marshmallow'},
    include_package_data=True,
    install_requires=['inflection'],
    tests_require=TEST_REQUIREMENTS,
    license=read("LICENSE"),
    zip_safe=False,
    keywords=('serialization', "rest", "json", "api", "marshal", "marshalling"),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    cmdclass={'test': PyTest},
)
