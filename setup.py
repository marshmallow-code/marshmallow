#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import os
import re
import sys
from os import path
from setuptools import setup, find_packages, Extension

LIBRARY_DIR = path.abspath(os.path.dirname(__file__))

CYTHON = False
JYTHON = 'java' in sys.platform
try:
    sys.pypy_version_info
    PYPY = True
except AttributeError:
    PYPY = False

if not PYPY and not JYTHON:
    try:
        from Cython.Distutils import build_ext
        CYTHON = True
    except ImportError:
        CYTHON = False

ext_modules = []
cmdclass = {}
if CYTHON:
    def list_modules(dirname):
        filenames = glob.glob(path.join(dirname, '*.py'))
        module_names = []
        for name in filenames:
            module, ext = path.splitext(path.basename(name))
            if module != '__init__':
                module_names.append(module)
        return module_names
    ext_modules = [
        Extension('marshmallow.' + ext, [path.join('marshmallow', ext + '.py')])
        for ext in list_modules(path.join(LIBRARY_DIR, 'marshmallow'))]
    cmdclass['build_ext'] = build_ext


EXTRA_REQUIREMENTS = ['python-dateutil', 'simplejson']

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
    extras_require={'reco': EXTRA_REQUIREMENTS},
    cmdclass=cmdclass,
    ext_modules=ext_modules,
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
    test_suite='tests'
)
