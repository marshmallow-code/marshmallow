# -*- coding: utf-8 -*-
"""Utility methods for marshmallow."""
from __future__ import absolute_import
import json
import datetime
from email.utils import formatdate
from calendar import timegm
import types

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

    if hasattr(obj, '__marshallable__'):
        return obj.__marshallable__()

    if hasattr(obj, '__getitem__'):
        return obj  # it is indexable it is ok

    if isinstance(obj, types.GeneratorType):
        return list(obj)

    return dict([(name, getattr(obj, name, None))  for name in dir(obj)
                if not name.startswith("__") and not name.endswith("__")])



def pprint(obj, *args, **kwargs):
    '''Pretty-printing function that can pretty-print OrderedDicts
    like regular dictionaries.
    '''
    if isinstance(obj, OrderedDict):
        print(json.dumps(obj, *args, **kwargs))
    else:
        py_pprint(obj, *args, **kwargs)

# From pytz: http://pytz.sourceforge.net/
ZERO = datetime.timedelta(0)
HOUR = datetime.timedelta(hours=1)


class UTC(datetime.tzinfo):
    """UTC

    Optimized UTC implementation. It unpickles using the single module global
    instance defined beneath this class declaration.
    """
    zone = "UTC"

    _utcoffset = ZERO
    _dst = ZERO
    _tzname = zone

    def fromutc(self, dt):
        if dt.tzinfo is None:
            return self.localize(dt)
        return super(utc.__class__, self).fromutc(dt)

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

    def __reduce__(self):
        return _UTC, ()

    def localize(self, dt, is_dst=False):
        '''Convert naive time to local time'''
        if dt.tzinfo is not None:
            raise ValueError('Not naive datetime (tzinfo is already set)')
        return dt.replace(tzinfo=self)

    def normalize(self, dt, is_dst=False):
        '''Correct the timezone information on the given datetime'''
        if dt.tzinfo is self:
            return dt
        if dt.tzinfo is None:
            raise ValueError('Naive time - no tzinfo set')
        return dt.astimezone(self)

    def __repr__(self):
        return "<UTC>"

    def __str__(self):
        return "UTC"

UTC = utc = UTC()  # UTC is a singleton


def rfcformat(dt, localtime=False):
    '''Return the RFC822-formatted represenation of a datetime object.

    :param bool localtime: If ``True``, return the date relative to the local
        timezone instead of UTC, properly taking daylight savings time into account.
    '''
    return formatdate(timegm(dt.utctimetuple()), localtime=localtime)


def isoformat(dt, localtime=False, *args, **kwargs):
    '''Return the ISO8601-formatted UTC representation of a datetime object.
    '''
    if localtime and dt.tzinfo is not None:
        localized = dt
    else:
        if dt.tzinfo is None:
            localized = UTC.localize(dt)
        else:
            localized = dt.astimezone(UTC)
    return localized.isoformat(*args, **kwargs)
