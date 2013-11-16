# -*- coding: utf-8 -*-
# Adapted from https://github.com/twilio/flask-restful/blob/master/flask_restful/types.py
# See the NOTICE file for more licensing information.
import datetime
from email.utils import formatdate
import re

# https://code.djangoproject.com/browser/django/trunk/django/core/validators.py
from calendar import timegm

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
        r'^((?:http|ftp)s?://' # http:// or https://
        r'(?:[^:@]+?:[^:@]*?@|)'  # basic auth
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE) # host is optional, allow for relative URLs


def url(value, relative=False):
    """Validate a URL.

    :param string value: The URL to validate
    :returns: The URL if valid.
    :raises: ValueError
    """
    regex = RELATIVE_URL_REGEX if relative else URL_REGEX
    if not regex.search(value):
        message = u'"{0}" is not a valid URL'.format(value)
        if regex.search('http://' + value):
            message += u'. Did you mean: "http://{0}"?'.format(value)
        raise ValueError(message)
    return value

USER_REGEX = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*$"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"$)',  # quoted-string
    re.IGNORECASE)

DOMAIN_REGEX = re.compile(
    r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,})$'  # domain
    # literal form, ipv4 address (SMTP 4.1.3)
    r'|^\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$',
    re.IGNORECASE)

DOMAIN_WHITELIST = ("localhost", )


def email(value):
    """Validate an email address.

    :param string value: The email address to validate.
    :returns: The email address if valid.
    :raises: ValueError if email is invalid
    """
    error_message = '"{0}" is not a valid email address.'.format(value)
    if not value or '@' not in value:
        raise ValueError(error_message)

    user_part, domain_part = value.rsplit('@', 1)

    if not USER_REGEX.match(user_part):
        raise ValueError(error_message)

    if (not domain_part in DOMAIN_WHITELIST and
            not DOMAIN_REGEX.match(domain_part)):
        # Try for possible IDN domain-part
        try:
            domain_part = domain_part.encode('idna').decode('ascii')
            if not DOMAIN_REGEX.match(domain_part):
                raise ValueError(error_message)
        except UnicodeError:
            pass
        raise ValueError(error_message)
    return value

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
