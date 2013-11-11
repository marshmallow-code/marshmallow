# -*- coding: utf-8 -*-
# Adapted from https://github.com/twilio/flask-restful/blob/master/flask_restful/types.py
# See the NOTICE file for more licensing information.
from datetime import datetime
from email.utils import formatdate
import re

# https://code.djangoproject.com/browser/django/trunk/django/core/validators.py
# basic auth added by frank
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


def url(value):
    """Validate a URL.

    :param string value: The URL to validate
    :returns: The URL if valid.
    :raises: ValueError
    """
    if not URL_REGEX.search(value):
        message = u"{0} is not a valid URL".format(value)
        if URL_REGEX.search('http://' + value):
            message += u'. Did you mean: "http://{0}"?'.format(value)
        raise ValueError(message)
    return value


def date(value):
    """Parse a valid looking date in the format YYYY-mm-dd"""
    date = datetime.strptime(value, "%Y-%m-%d")
    if date.year < 1900:
        raise ValueError(u"Year must be >= 1900")
    return date


def natural(value):
    """Parse a non-negative integer value"""
    value = int(value)
    if value < 0:
        raise ValueError("Invalid literal for natural(): '{}'".format(value))
    return value


def boolean(value):
    """Parse the string "true" or "false" as a boolean (case insensitive)"""
    value = value.lower()
    if value == 'true':
        return True
    if value == 'false':
        return False
    raise ValueError("Invalid literal for boolean(): {}".format(value))


def rfc822(dt, localtime=False):
    '''Return the RFC822-formatted represenation of a datetime oect.

    :param bool localtime: If ``True``, return the date relative to the local
        timezone instead of UTC, properly taking daylight savings time into account.
    '''
    return formatdate(timegm(dt.utctimetuple()), localtime=localtime)
