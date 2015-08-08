# -*- coding: utf-8 -*-
"""Validation classes for various types of data."""
from __future__ import unicode_literals
import re
import functools
import warnings

from marshmallow.compat import basestring
from marshmallow.exceptions import ValidationError


class URL(object):
    """Validate a URL.

    :param bool relative:
        Whether to allow relative URLs.
    :param str error:
        Error message to raise in case of a validation error.
    """
    URL_REGEX = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:[^:@]+?:[^:@]*?@|)'  # basic auth
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    RELATIVE_URL_REGEX = re.compile(
        r'^((?:http|ftp)s?://'  # http:// or https://
        r'(?:[^:@]+?:[^:@]*?@|)'  # basic auth
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # host is optional, allow for relative URLs

    def __init__(self, relative=False, error=None):
        self.relative = relative
        self.error = error

    def __call__(self, value):
        message = '"{0}" is not a valid URL.'.format(value)

        if not value:
            raise ValidationError(self.error or message)

        regex = self.RELATIVE_URL_REGEX if self.relative else self.URL_REGEX

        if not regex.search(value):
            if regex.search('http://' + value):
                message += ' Did you mean: "http://{0}"?'.format(value)
            raise ValidationError(self.error or message)

        return value


class Email(object):
    """Validate an email address.

    :param str error:
        Error message to raise in case of a validation error.
    """
    USER_REGEX = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*$"  # dot-atom
        # quoted-string
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]'
        r'|\\[\001-\011\013\014\016-\177])*"$)', re.IGNORECASE)

    DOMAIN_REGEX = re.compile(
        # domain
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}|[A-Z0-9-]{2,})$'
        # literal form, ipv4 address (SMTP 4.1.3)
        r'|^\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)'
        r'(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$', re.IGNORECASE)

    DOMAIN_WHITELIST = ('localhost',)

    def __init__(self, error=None):
        self.error = error or '"{0}" is not a valid email address.'

    def __call__(self, value):
        message = self.error.format(value)

        if not value or '@' not in value:
            raise ValidationError(message)

        user_part, domain_part = value.rsplit('@', 1)

        if not self.USER_REGEX.match(user_part):
            raise ValidationError(message)

        if domain_part not in self.DOMAIN_WHITELIST:
            if not self.DOMAIN_REGEX.match(domain_part):
                try:
                    domain_part = domain_part.encode('idna').decode('ascii')
                except UnicodeError:
                    pass
                else:
                    if self.DOMAIN_REGEX.match(domain_part):
                        return value
                raise ValidationError(message)

        return value


class Range(object):
    """Validator which succeeds if the value it is passed is greater
    or equal to ``min`` and less than or equal to ``max``. If ``min``
    is not specified, or is specified as `None`, no lower bound
    exists. If ``max`` is not specified, or is specified as `None`,
    no upper bound exists.

    :param min:
        The minimum value (lower bound). If not provided, minimum
        value will not be checked.
    :param max:
        The maximum value (upper bound). If not provided, maximum
        value will not be checked.
    :param str error:
        Error message to raise in case of a validation error.
        Can be interpolated using `{min}` and `{max}`.
    """
    message_min = 'Must be at least {min}.'
    message_max = 'Must be at most {max}.'
    message_all = 'Must be between {min} and {max}.'

    def __init__(self, min=None, max=None, error=None):
        self.min = min
        self.max = max
        self.error = error
        self._format = lambda m: (self.error or m).format(min=self.min, max=self.max)

    def __call__(self, value):
        if self.min is not None and value < self.min:
            message = self.message_min if self.max is None else self.message_all
            raise ValidationError(self._format(message))

        if self.max is not None and value > self.max:
            message = self.message_max if self.min is None else self.message_all
            raise ValidationError(self._format(message))

        return value


class Length(Range):
    """Validator which succeeds if the value passed to it has a
    length between a minimum and maximum. Uses len(), so it
    can work for strings, lists, or anything with length.

    :param int min:
        The minimum length. If not provided, minimum length
        will not be checked.
    :param int max:
        The maximum length. If not provided, maximum length
        will not be checked.
    :param str error:
        Error message to raise in case of a validation error.
        Can be interpolated using `{min}` and `{max}`.
    """
    message_min = 'Shorter than minimum length {min}.'
    message_max = 'Longer than maximum length {max}.'
    message_all = 'Length must be between {min} and {max}.'

    def __call__(self, value):
        super(Length, self).__call__(len(value))
        return value


class Equal(object):
    """Validator which succeeds if the ``value`` passed to it is
    equal to ``comparable``.

    :param comparable:
        The object to compare to.
    :param str error:
        Error message to raise in case of a validation error.
        Can be interpolated using `{other}`.
    """
    def __init__(self, comparable, error=None):
        self.comparable = comparable
        self.error = error or 'Must be equal to {other}.'

    def __call__(self, value):
        if value != self.comparable:
            raise ValidationError(self.error.format(other=self.comparable))

        return value


class Regexp(object):
    """Validate ``value`` against the provided regex.

    :param regex:
        The regular expression string to use. Can also be a compiled
        regular expression pattern.
    :param flags:
        The regexp flags to use, for example re.IGNORECASE. Ignored
        if ``regex`` is not a string.
    :param str error:
        Error message to raise in case of a validation error.
    """
    def __init__(self, regex, flags=0, error=None):
        self.regex = re.compile(regex, flags) if isinstance(regex, basestring) else regex
        self.error = error or 'String does not match expected pattern.'

    def __call__(self, value):
        if self.regex.match(value) is None:
            raise ValidationError(self.error)

        return value


class Predicate(object):
    """Call the specified ``method`` of the ``value`` object. The
    validator succeeds if the invoked method returns an object that
    evaluates to True in a Boolean context. Any additional keyword
    argument will be passed to the method.

    :param str method:
        The name of the method to invoke.
    :param str error:
        Error message to raise in case of a validation error.
    :param kwargs:
        Additional keyword arguments to pass to the method.
    """
    def __init__(self, method, error=None, **kwargs):
        self.method = method
        self.error = error or 'Invalid input.'
        self.kwargs = kwargs

    def __call__(self, value):
        method = getattr(value, self.method)

        if not method(**self.kwargs):
            raise ValidationError(self.error)

        return value


class NoneOf(object):
    """Validator which fails if ``value`` is a member of ``iterable``.

    :param iterable iterable:
        A sequence of invalid values.
    :param str error:
        Error message to raise in case of a validation error.
    """
    def __init__(self, iterable, error=None):
        self.iterable = iterable
        self.error = error or 'Invalid input.'

    def __call__(self, value):
        try:
            if value in self.iterable:
                raise ValidationError(self.error)
        except TypeError:
            pass

        return value


#
# Backward compatibility
#

def _deprecated(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn('{0} is deprecated. Use the class-based '
                      'equivalent instead.'.format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    return wrapper

@_deprecated
def url(value, relative=False, error=None):
    return URL(relative, error)(value) if value is not None else None

@_deprecated
def email(value, error=None):
    return Email(error)(value) if value is not None else None

@_deprecated
def ranging(value, min=None, max=None, error=None):
    return Range(min, max, error)(value) if value is not None else None

@_deprecated
def length(value, min=None, max=None, error=None):
    return Length(min, max, error)(value) if value is not None else None

@_deprecated
def equal(value, comparable, error=None):
    return Equal(comparable, error)(value) if value is not None else None

@_deprecated
def regexp(value, regex, flags=0, error=None):
    return Regexp(regex, flags, error)(value) if value is not None else None

@_deprecated
def predicate(value, method, error=None, **kwargs):
    return Predicate(method, error, **kwargs)(value) if value is not None else None
