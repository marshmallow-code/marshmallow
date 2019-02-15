# -*- coding: utf-8 -*-
from __future__ import absolute_import

from marshmallow.schema import Schema, SchemaOpts

from . import fields
from marshmallow.decorators import (
    pre_dump, post_dump, pre_load, post_load, validates, validates_schema,
)
from marshmallow.utils import EXCLUDE, INCLUDE, RAISE, pprint, missing
from marshmallow.exceptions import ValidationError
from distutils.version import LooseVersion

__version__ = '3.0.0rc4'
__version_info__ = tuple(LooseVersion(__version__).version)
__all__ = [
    'EXCLUDE',
    'INCLUDE',
    'RAISE',
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
    'ValidationError',
    'missing',
]
