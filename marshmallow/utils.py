# -*- coding: utf-8 -*-
"""Utility methods for marshmallow."""
from __future__ import absolute_import
import json
from decimal import Decimal, Context, Inexact
from pprint import pprint as py_pprint

from marshmallow.compat import OrderedDict


def is_iterable_but_not_string(obj):
    '''Return True if ``obj`` is an iterable object that isn't a string.'''
    return hasattr(obj, "__iter__") and not hasattr(obj, "strip")


def is_indexable_but_not_string(obj):
    '''Return True if ``obj`` is indexable but isn't a string.'''
    return not hasattr(obj, "strip") and hasattr(obj, "__getitem__")


def is_collection(obj):
    '''Return True if ``obj`` is a collection type, e.g list, tuple, queryset.
    '''
    return is_iterable_but_not_string(obj) and not isinstance(obj, dict)


def is_instance_or_subclass(val, class_):
    '''Return True if ``val`` is either a subclass or instance of ``class_``.
    '''
    try:
        return issubclass(val, class_)
    except TypeError:
        return isinstance(val, class_)

def float_to_decimal(f):
    """Convert a floating point number to a Decimal with no loss of information.
        See: http://docs.python.org/release/2.6.7/library/decimal.html#decimal-faq
    """
    n, d = f.as_integer_ratio()
    numerator, denominator = Decimal(n), Decimal(d)
    ctx = Context(prec=60)
    result = ctx.divide(numerator, denominator)
    while ctx.flags[Inexact]:
        ctx.flags[Inexact] = False
        ctx.prec *= 2
        result = ctx.divide(numerator, denominator)
    return result


def to_marshallable_type(obj):
    """Helper for converting an object to a dictionary only if it is not
    dictionary already or an indexable object nor a simple type"""
    if obj is None:
        return None  # make it idempotent for None

    if hasattr(obj, '__getitem__'):
        return obj  # it is indexable it is ok

    if hasattr(obj, '__marshallable__'):
        return obj.__marshallable__()

    return dict(obj.__dict__)


def pprint(obj, *args, **kwargs):
    '''Pretty-printing function that can pretty-print OrderedDicts
    like regular dictionaries.
    '''
    if isinstance(obj, OrderedDict):
        print(json.dumps(obj, *args, **kwargs))
    else:
        py_pprint(obj, *args, **kwargs)
