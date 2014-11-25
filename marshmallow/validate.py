# -*- coding: utf-8 -*-
"""Validation functions for various types of data."""
import re
from marshmallow.exceptions import ValidationError


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


def url(value, relative=False, error=None):
    """Validate a URL.

    :param string value: The URL to validate
    :param bool relative: Whether to allow relative URLs.
    :returns: The URL if valid.
    :raises: ValidationError if url is invalid.
    """
    regex = RELATIVE_URL_REGEX if relative else URL_REGEX
    if value and not regex.search(value):
        message = u'"{0}" is not a valid URL'.format(value)
        if regex.search('http://' + value):
            message += u'. Did you mean: "http://{0}"?'.format(value)
        raise ValidationError(error or message)
    return value

USER_REGEX = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*$"  # dot-atom
    # quoted-string
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"$)',
    re.IGNORECASE)

DOMAIN_REGEX = re.compile(
    r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,})$'  # domain
    # literal form, ipv4 address (SMTP 4.1.3)
    r'|^\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$',
    re.IGNORECASE)

DOMAIN_WHITELIST = ("localhost", )


def email(value, error=None):
    """Validate an email address.

    :param str error: Error message to show.
    :param string value: The email address to validate.
    :returns: The email address if valid.
    :raises: ValidationError if email is invalid
    """
    if value is None:
        return None
    error_message = error or '"{0}" is not a valid email address.'.format(value)
    if not value or '@' not in value:
        raise ValidationError(error_message)

    user_part, domain_part = value.rsplit('@', 1)

    if not USER_REGEX.match(user_part):
        raise ValidationError(error_message)

    if (domain_part not in DOMAIN_WHITELIST and
            not DOMAIN_REGEX.match(domain_part)):
        # Try for possible IDN domain-part
        try:
            domain_part = domain_part.encode('idna').decode('ascii')
            if not DOMAIN_REGEX.match(domain_part):
                raise ValidationError(error_message)
        except UnicodeError:
            pass
        raise ValidationError(error_message)
    return value


def length(value, min=None, max=None, error_min=None, error_max=None):
    """Validator which succeeds if the value passed to it has a
    length between a minimum and maximum. Uses len(), so
    it can work for strings, lists, or anything with length.

    :param int min: Minimum length.
    :param int max: Maximum length.
    :param str error_min: Error message to show if length is less than min.
    :param str error_max: Error message to show if length is less than max.
    """
    if value is None:
        return None

    if min is not None and len(value) < min:
        error_message = error_min or 'Shorter than minimum length {min}.'
        raise ValidationError(error_message.format(min=min))

    if max is not None and len(value) > max:
        error_message = error_max or 'Longer than maximum length {max}.'
        raise ValidationError(error_message.format(max=max))

    return value
