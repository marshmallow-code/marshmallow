#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from setuptools import setup, find_packages

EXTRAS_REQUIRE = {
    'reco': ['python-dateutil>=2.7.0', 'simplejson'],
    'tests': [
        'pytest',
        'pytz',
    ],
    'lint': [
        'flake8==3.7.5',
        'pre-commit==1.14.3',
    ],
}
EXTRAS_REQUIRE['dev'] = (
    EXTRAS_REQUIRE['reco'] +
    EXTRAS_REQUIRE['tests'] +
    EXTRAS_REQUIRE['lint'] +
    ['tox']
)

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


__version__ = find_version('marshmallow/__init__.py')


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name='marshmallow',
    version=__version__,
    description=(
        'A lightweight library for converting complex '
        'datatypes to and from native Python datatypes.'
    ),
    long_description=read('README.rst'),
    author='Steven Loria',
    author_email='sloria1@gmail.com',
    url='https://github.com/marshmallow-code/marshmallow',
    packages=find_packages(exclude=('test*', 'examples')),
    package_dir={'marshmallow': 'marshmallow'},
    include_package_data=True,
    extras_require=EXTRAS_REQUIRE,
    license='MIT',
    zip_safe=False,
    keywords=(
        'serialization', 'rest', 'json', 'api', 'marshal',
        'marshalling', 'deserialization', 'validation', 'schema',
    ),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    project_urls={
        'Changelog': 'https://marshmallow.readthedocs.io/en/latest/changelog.html',
        'Issues': 'https://github.com/marshmallow-code/marshmallow/issues',
        'Funding': 'https://opencollective.com/marshmallow',
        'Tidelift': 'https://tidelift.com/subscription/pkg/pypi-marshmallow?utm_source=pypi-marshmallow&utm_medium=pypi',  # noqa
    },
)
