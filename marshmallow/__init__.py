# -*- coding: utf-8 -*-
from __future__ import absolute_import

from marshmallow.schema import (
    Schema,
    SchemaOpts,
    MarshalResult,
    UnmarshalResult,
)
from marshmallow.utils import pprint
from marshmallow.exceptions import MarshallingError, UnmarshallingError, ValidationError

__version__ = '2.0.0-dev'
__author__ = 'Steven Loria'
__license__ = 'MIT'

__all__ = [
    'Schema',
    'SchemaOpts',
    'pprint',
    'MarshalResult',
    'UnmarshalResult',
    'MarshallingError',
    'UnmarshallingError',
    'ValidationError',
]
