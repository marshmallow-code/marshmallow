"""Utility methods for marshmallow."""
import collections
import functools
import datetime as dt
import inspect
import json
import re
from collections.abc import Mapping, Iterable
from email.utils import format_datetime, parsedate_to_datetime
from pprint import pprint as py_pprint

from marshmallow.base import FieldABC
from marshmallow.exceptions import FieldInstanceResolutionError

EXCLUDE = "exclude"
INCLUDE = "include"
RAISE = "raise"


class _Missing:
    def __bool__(self):
        return False

    def __copy__(self):
        return self

    def __deepcopy__(self, _):
        return self

    def __repr__(self):
        return "<marshmallow.missing>"


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
    return (isinstance(obj, Iterable) and not hasattr(obj, "strip")) or is_generator(
        obj
    )


def is_collection(obj):
    """Return True if ``obj`` is a collection type, e.g list, tuple, queryset."""
    return is_iterable_but_not_string(obj) and not isinstance(obj, Mapping)


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
    return isinstance(obj, tuple) and hasattr(obj, "_fields")


def pprint(obj, *args, **kwargs):
    """Pretty-printing function that can pretty-print OrderedDicts
    like regular dictionaries. Useful for printing the output of
    :meth:`marshmallow.Schema.dump`.
    """
    if isinstance(obj, collections.OrderedDict):
        print(json.dumps(obj, *args, **kwargs))
    else:
        py_pprint(obj, *args, **kwargs)


# From pytz: http://pytz.sourceforge.net/
ZERO = dt.timedelta(0)


class UTC(dt.tzinfo):
    """UTC

    Optimized UTC implementation. It unpickles using the single module global
    instance defined beneath this class declaration.
    """

    zone = "UTC"

    _utcoffset = ZERO
    _dst = ZERO
    _tzname = zone

    def fromutc(self, datetime):
        if datetime.tzinfo is None:
            return self.localize(datetime)
        return super(utc.__class__, self).fromutc(datetime)

    def utcoffset(self, datetime):
        return ZERO

    def tzname(self, datetime):
        return "UTC"

    def dst(self, datetime):
        return ZERO

    def localize(self, datetime, is_dst=False):
        """Convert naive time to local time"""
        if datetime.tzinfo is not None:
            raise ValueError("Not naive datetime (tzinfo is already set)")
        return datetime.replace(tzinfo=self)

    def normalize(self, datetime, is_dst=False):
        """Correct the timezone information on the given datetime"""
        if datetime.tzinfo is self:
            return datetime
        if datetime.tzinfo is None:
            raise ValueError("Naive time - no tzinfo set")
        return datetime.astimezone(self)

    def __repr__(self):
        return "<UTC>"

    def __str__(self):
        return "UTC"


UTC = utc = UTC()  # UTC is a singleton


def from_rfc(datestring):
    """Parse a RFC822-formatted datetime string and return a datetime object.

    https://stackoverflow.com/questions/885015/how-to-parse-a-rfc-2822-date-time-into-a-python-datetime  # noqa: B950
    """
    return parsedate_to_datetime(datestring)


def rfcformat(datetime, *, localtime=False):
    """Return the RFC822-formatted representation of a datetime object.

    :param datetime datetime: The datetime.
    :param bool localtime: If ``True``, return the date relative to the local
        timezone instead of UTC, displaying the proper offset,
        e.g. "Sun, 10 Nov 2013 08:23:45 -0600"
    """
    if localtime and datetime.tzinfo is None:
        datetime = UTC.localize(datetime)
    if not localtime and datetime.tzinfo is not None:
        # Remove timezone to format as "-0000" rather than "+0000"
        datetime = datetime.astimezone(UTC).replace(tzinfo=None)
    return format_datetime(datetime)


# Hat tip to Django for ISO8601 deserialization functions

_iso8601_datetime_re = re.compile(
    r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})"
    r"[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})"
    r"(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?"
    r"(?P<tzinfo>Z|[+-]\d{2}(?::?\d{2})?)?$"
)

_iso8601_date_re = re.compile(r"(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$")

_iso8601_time_re = re.compile(
    r"(?P<hour>\d{1,2}):(?P<minute>\d{1,2})"
    r"(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?"
)


def get_fixed_timezone(offset):
    """Return a tzinfo instance with a fixed offset from UTC."""
    if isinstance(offset, dt.timedelta):
        offset = offset.total_seconds() // 60
    sign = "-" if offset < 0 else "+"
    hhmm = "%02d%02d" % divmod(abs(offset), 60)
    name = sign + hhmm
    return dt.timezone(dt.timedelta(minutes=offset), name)


def from_iso_datetime(value):
    """Parse a string and return a datetime.datetime.

    This function supports time zone offsets. When the input contains one,
    the output uses a timezone with a fixed offset from UTC.
    """
    match = _iso8601_datetime_re.match(value)
    if not match:
        raise ValueError("Not a valid ISO8601-formatted datetime string")
    kw = match.groupdict()
    kw["microsecond"] = kw["microsecond"] and kw["microsecond"].ljust(6, "0")
    tzinfo = kw.pop("tzinfo")
    if tzinfo == "Z":
        tzinfo = utc
    elif tzinfo is not None:
        offset_mins = int(tzinfo[-2:]) if len(tzinfo) > 3 else 0
        offset = 60 * int(tzinfo[1:3]) + offset_mins
        if tzinfo[0] == "-":
            offset = -offset
        tzinfo = get_fixed_timezone(offset)
    kw = {k: int(v) for k, v in kw.items() if v is not None}
    kw["tzinfo"] = tzinfo
    return dt.datetime(**kw)


def from_iso_time(value):
    """Parse a string and return a datetime.time.

    This function doesn't support time zone offsets.
    """
    match = _iso8601_time_re.match(value)
    if not match:
        raise ValueError("Not a valid ISO8601-formatted time string")
    kw = match.groupdict()
    kw["microsecond"] = kw["microsecond"] and kw["microsecond"].ljust(6, "0")
    kw = {k: int(v) for k, v in kw.items() if v is not None}
    return dt.time(**kw)


def from_iso_date(value):
    """Parse a string and return a datetime.date."""
    match = _iso8601_date_re.match(value)
    if not match:
        raise ValueError("Not a valid ISO8601-formatted date string")
    kw = {k: int(v) for k, v in match.groupdict().items()}
    return dt.date(**kw)


def isoformat(datetime, *args, localtime=False, **kwargs):
    """Return the ISO8601-formatted UTC representation of a datetime object."""
    if localtime and datetime.tzinfo is not None:
        localized = datetime
    else:
        if datetime.tzinfo is None:
            localized = UTC.localize(datetime)
        else:
            localized = datetime.astimezone(UTC)
    return localized.isoformat(*args, **kwargs)


def to_iso_date(date, *args, **kwargs):
    return dt.date.isoformat(date)


def ensure_text_type(val):
    if isinstance(val, bytes):
        val = val.decode("utf-8")
    return str(val)


def pluck(dictlist, key):
    """Extracts a list of dictionary values from a list of dictionaries.
    ::

        >>> dlist = [{'id': 1, 'name': 'foo'}, {'id': 2, 'name': 'bar'}]
        >>> pluck(dlist, 'id')
        [1, 2]
    """
    return [d[key] for d in dictlist]


# Various utilities for pulling keyed values from objects


def get_value(obj, key, default=missing):
    """Helper for pulling a keyed value off various types of objects. Fields use
    this method by default to access attributes of the source object. For object `x`
    and attribute `i`, this method first tries to access `x[i]`, and then falls back to
    `x.i` if an exception is raised.

    .. warning::
        If an object `x` does not raise an exception when `x[i]` does not exist,
        `get_value` will never check the value `x.i`. Consider overriding
        `marshmallow.fields.Field.get_value` in this case.
    """
    if not isinstance(key, int) and "." in key:
        return _get_value_for_keys(obj, key.split("."), default)
    else:
        return _get_value_for_key(obj, key, default)


def _get_value_for_keys(obj, keys, default):
    if len(keys) == 1:
        return _get_value_for_key(obj, keys[0], default)
    else:
        return _get_value_for_keys(
            _get_value_for_key(obj, keys[0], default), keys[1:], default
        )


def _get_value_for_key(obj, key, default):
    if not hasattr(obj, "__getitem__"):
        return getattr(obj, key, default)

    try:
        return obj[key]
    except (KeyError, IndexError, TypeError, AttributeError):
        return getattr(obj, key, default)


def set_value(dct, key, value):
    """Set a value in a dict. If `key` contains a '.', it is assumed
    be a path (i.e. dot-delimited string) to the value's location.

    ::

        >>> d = {}
        >>> set_value(d, 'foo.bar', 42)
        >>> d
        {'foo': {'bar': 42}}
    """
    if "." in key:
        head, rest = key.split(".", 1)
        target = dct.setdefault(head, {})
        if not isinstance(target, dict):
            raise ValueError(
                "Cannot set {key} in {head} "
                "due to existing value: {target}".format(
                    key=key, head=head, target=target
                )
            )
        set_value(target, rest, value)
    else:
        dct[key] = value


def callable_or_raise(obj):
    """Check that an object is callable, else raise a :exc:`ValueError`.
    """
    if not callable(obj):
        raise ValueError("Object {!r} is not callable.".format(obj))
    return obj


def _signature(func):
    if hasattr(inspect, "signature"):
        return list(inspect.signature(func).parameters.keys())
    if hasattr(func, "__self__"):
        # Remove bound arg to match inspect.signature()
        return inspect.getargspec(func).args[1:]
    # All args are unbound
    return inspect.getargspec(func).args


def get_func_args(func):
    """Given a callable, return a tuple of argument names. Handles
    `functools.partial` objects and class-based callables.

    .. versionchanged:: 3.0.0a1
        Do not return bound arguments, eg. ``self``.
    """
    if isinstance(func, functools.partial):
        return _signature(func.func)
    if inspect.isfunction(func) or inspect.ismethod(func):
        return _signature(func)
    # Callable class
    return _signature(func.__call__)


def resolve_field_instance(cls_or_instance):
    """Return a Schema instance from a Schema class or instance.

    :param type|Schema cls_or_instance: Marshmallow Schema class or instance.
    """
    if isinstance(cls_or_instance, type):
        if not issubclass(cls_or_instance, FieldABC):
            raise FieldInstanceResolutionError
        return cls_or_instance()
    else:
        if not isinstance(cls_or_instance, FieldABC):
            raise FieldInstanceResolutionError
        return cls_or_instance
