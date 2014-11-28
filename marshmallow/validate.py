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


def length(value, min=None, max=None, error=None):
    """Validator which succeeds if the value passed to it has a
    length between a minimum and maximum. Uses len(), so
    it can work for strings, lists, or anything with length.

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
    if value is None:
        return None

    len_ = len(value)

    if (min is not None and len_ < min) or (max is not None and len_ > max):
        message = error
        if message is None:
            if min is None:
                message = 'Longer than maximum length {max}.'
            elif max is None:
                message = 'Shorter than minimum length {min}.'
            else:
                message = 'Length must be between {min} and {max}.'
        raise ValidationError(message.format(min=min, max=max))

    return value


def ranging(value, min=None, max=None, error=None):
    """Validator which succeeds if the value it is passed is greater
    or equal to ``min`` and less than or equal to ``max``. If ``min``
    is not specified, or is specified as ``None``, no lower bound
    exists. If ``max`` is not specified, or is specified as ``None``,
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
    if value is None:
        return None

    if (min is not None and value < min) or (max is not None and value > max):
        message = error
        if message is None:
            if min is None:
                message = 'Must be at most {max}.'
            elif max is None:
                message = 'Must be at least {min}.'
            else:
                message = 'Must be between {min} and {max}.'
        raise ValidationError(message.format(min=min, max=max))

    return value
