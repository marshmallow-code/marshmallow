# -*- coding: utf-8 -*-
"""Utility methods for marshmallow."""
from __future__ import absolute_import, unicode_literals

import collections
import datetime
import functools
import inspect
import json
import time
import types
from calendar import timegm
from decimal import Decimal, ROUND_HALF_EVEN, Context, Inexact
from email.utils import formatdate, parsedate
from pprint import pprint as py_pprint

from marshmallow.compat import OrderedDict, binary_type, text_type


dateutil_available = False
try:
    from dateutil import parser
    dateutil_available = True
except ImportError:
    dateutil_available = False

class _Missing(object):

    def __bool__(self):
        return False

    __nonzero__ = __bool__  # PY2 compat

    def __repr__(self):
        return '<marshmallow.missing>'


# Singleton value that indicates that a field's value is missing from input
# dict passed to :meth:`Schema.load`. If the field's value is not required,
# it's ``default`` value is used.
missing = _Missing()


def is_generator(obj):
    """Return True if ``obj`` is a generator
    """
    return inspect.isgeneratorfunction(obj) or inspect.isgenerator(obj)


def is_iterable_but_not_string(obj):
    """Return True if ``obj`` is an iterable object that isn't a string."""
    return (
        (isinstance(obj, collections.Iterable) and not hasattr(obj, "strip"))
        or is_generator(obj)
    )


def is_indexable_but_not_string(obj):
    """Return True if ``obj`` is indexable but isn't a string."""
    return not hasattr(obj, "strip") and hasattr(obj, "__getitem__")


def is_collection(obj):
    """Return True if ``obj`` is a collection type, e.g list, tuple, queryset."""
    return is_iterable_but_not_string(obj) and not isinstance(obj, collections.Mapping)


def is_instance_or_subclass(val, class_):
    """Return True if ``val`` is either a subclass or instance of ``class_``."""
    try:
        return issubclass(val, class_)
    except TypeError:
        return isinstance(val, class_)

def is_keyed_tuple(obj):
    """Return True if ``obj`` has keyed tuple behavior, such as
    namedtuples or SQLAlchemy's KeyedTuples.
    """
    return isinstance(obj, tuple) and hasattr(obj, '_fields')

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

ZERO_DECIMAL = Decimal()

def decimal_to_fixed(value, precision):
    """Convert a `Decimal` to a fixed-precision number as a string."""
    return text_type(value.quantize(precision, rounding=ROUND_HALF_EVEN))


def to_marshallable_type(obj, field_names=None):
    """Helper for converting an object to a dictionary only if it is not
    dictionary already or an indexable object nor a simple type"""
    if obj is None:
        return None  # make it idempotent for None

    if hasattr(obj, '__marshallable__'):
        return obj.__marshallable__()

    if hasattr(obj, '__getitem__') and not is_keyed_tuple(obj):
        return obj  # it is indexable it is ok

    if isinstance(obj, types.GeneratorType):
        return list(obj)
    if field_names:
        # exclude field names that aren't actual attributes of the object
        attrs = set(dir(obj)) & set(field_names)
    else:
        attrs = set(dir(obj))
    return dict([(attr, getattr(obj, attr, None)) for attr in attrs
                  if not attr.startswith("__") and not attr.endswith("__")])


def pprint(obj, *args, **kwargs):
    """Pretty-printing function that can pretty-print OrderedDicts
    like regular dictionaries. Useful for printing the output of
    :meth:`marshmallow.Schema.dump`.
    """
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


def local_rfcformat(dt):
    """Return the RFC822-formatted representation of a timezone-aware datetime
    with the UTC offset.
    """
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
    month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
             "Oct", "Nov", "Dec"][dt.month - 1]
    tz_offset = dt.strftime("%z")
    return "%s, %02d %s %04d %02d:%02d:%02d %s" % (weekday, dt.day, month,
        dt.year, dt.hour, dt.minute, dt.second, tz_offset)


def rfcformat(dt, localtime=False):
    """Return the RFC822-formatted representation of a datetime object.

    :param datetime dt: The datetime.
    :param bool localtime: If ``True``, return the date relative to the local
        timezone instead of UTC, displaying the proper offset,
        e.g. "Sun, 10 Nov 2013 08:23:45 -0600"
    """
    if not localtime:
        return formatdate(timegm(dt.utctimetuple()))
    else:
        return local_rfcformat(dt)


def isoformat(dt, localtime=False, *args, **kwargs):
    """Return the ISO8601-formatted UTC representation of a datetime object.
    """
    if localtime and dt.tzinfo is not None:
        localized = dt
    else:
        if dt.tzinfo is None:
            localized = UTC.localize(dt)
        else:
            localized = dt.astimezone(UTC)
    return localized.isoformat(*args, **kwargs)


def from_datestring(datestring):
    """Parse an arbitrary datestring and return a datetime object using
    dateutils' parser.
    """
    if dateutil_available:
        return parser.parse(datestring)
    else:
        raise RuntimeError('from_datestring requires the python-dateutil library')

def from_rfc(datestring, use_dateutil=True):
    """Parse a RFC822-formatted datetime string and return a datetime object.

    Use dateutil's parser if possible.

    https://stackoverflow.com/questions/885015/how-to-parse-a-rfc-2822-date-time-into-a-python-datetime
    """
    # Use dateutil's parser if possible
    if dateutil_available and use_dateutil:
        return parser.parse(datestring)
    else:
        parsed = parsedate(datestring)  # as a tuple
        timestamp = time.mktime(parsed)
        return datetime.datetime.fromtimestamp(timestamp)


def from_iso(datestring, use_dateutil=True):
    """Parse an ISO8601-formatted datetime string and return a datetime object.

    Use dateutil's parser if possible and return a timezone-aware datetime.
    """
    # Use dateutil's parser if possible
    if dateutil_available and use_dateutil:
        return parser.parse(datestring)
    else:
        # Strip off timezone info.
        return datetime.datetime.strptime(datestring[:19], '%Y-%m-%dT%H:%M:%S')


def from_iso_time(timestring, use_dateutil=True):
    """Parse an ISO8601-formatted datetime string and return a datetime.time
    object.
    """
    if dateutil_available and use_dateutil:
        return parser.parse(timestring).time()
    else:
        if len(timestring) > 8:  # has microseconds
            fmt = '%H:%M:%S.%f'
        else:
            fmt = '%H:%M:%S'
        return datetime.datetime.strptime(timestring, fmt).time()

def from_iso_date(datestring, use_dateutil=True):
    if dateutil_available and use_dateutil:
        return parser.parse(datestring).date()
    else:
        return datetime.datetime.strptime(datestring[:10], '%Y-%m-%d').date()

def ensure_text_type(val):
    if isinstance(val, binary_type):
        val = val.decode('utf-8')
    return text_type(val)

def pluck(dictlist, key):
    """Extracts a list of dictionary values from a list of dictionaries.
    ::

        >>> dlist = [{'id': 1, 'name': 'foo'}, {'id': 2, 'name': 'bar'}]
        >>> pluck(dlist, 'id')
        [1, 2]
    """
    return [d[key] for d in dictlist]

# Various utilities for pulling keyed values from objects

def get_value(key, obj, default=missing):
    """Helper for pulling a keyed value off various types of objects"""
    if type(key) == int:
        return _get_value_for_key(key, obj, default)
    else:
        return _get_value_for_keys(key.split('.'), obj, default)


def _get_value_for_keys(keys, obj, default):
    if len(keys) == 1:
        return _get_value_for_key(keys[0], obj, default)
    else:
        return _get_value_for_keys(
            keys[1:], _get_value_for_key(keys[0], obj, default), default)


def _get_value_for_key(key, obj, default):
    try:
        return obj[key]
    except (KeyError, AttributeError, IndexError, TypeError):
        try:
            attr = getattr(obj, key)
            return attr() if callable(attr) else attr
        except AttributeError:
            return default
    return default


def callable_or_raise(obj):
    """Check that an object is callable, else raise a :exc:`ValueError`.
    """
    if not callable(obj):
        raise ValueError('Object {0!r} is not callable.'.format(obj))
    return obj


def get_func_args(func):
    """Given a callable, return a tuple of argument names. Handles
    `functools.partial` objects and class-based callables.
    """
    if isinstance(func, functools.partial):
        return inspect.getargspec(func.func).args
    if inspect.isfunction(func) or inspect.ismethod(func):
        return inspect.getargspec(func).args
    # Callable class
    return inspect.getargspec(func.__call__).args


def if_none(value, default):
    return value if value is not None else default
