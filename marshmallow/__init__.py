# -*- coding: utf-8 -*-
from __future__ import absolute_import

from marshmallow.schema import (
    Schema,
    SchemaOpts,
    MarshalResult,
    UnmarshalResult,
)
from . import fields
from marshmallow.decorators import (
    pre_dump, post_dump, pre_load, post_load, validates, validates_schema
)
from marshmallow.utils import pprint, missing
from marshmallow.exceptions import ValidationError
from distutils.version import LooseVersion

__version__ = '2.18.0'
__version_info__ = tuple(LooseVersion(__version__).version)
__author__ = 'Steven Loria'
__all__ = [
    'Schema',
    'SchemaOpts',
    'fields',
    'validates',
    'validates_schema',
    'pre_dump',
    'post_dump',
    'pre_load',
    'post_load',
    'pprint',
    'MarshalResult',
    'UnmarshalResult',
    'ValidationError',
    'missing',
]
