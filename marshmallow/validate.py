# -*- coding: utf-8 -*-
"""Validation classes for various types of data."""

from __future__ import unicode_literals

import re
from operator import attrgetter

from marshmallow.compat import basestring, text_type, zip_longest
from marshmallow.exceptions import ValidationError


class Validator(object):
    """Base abstract class for validators.

    .. note::
        This class does not provide any behavior. It is only used to
        add a useful `__repr__` implementation for validators.
    """

    def __repr__(self):
        args = self._repr_args()
        args = '{0}, '.format(args) if args else ''

        return (
            '<{self.__class__.__name__}({args}error={self.error!r})>'
            .format(self=self, args=args)
        )

    def _repr_args(self):
        """A string representation of the args passed to this validator. Used by
        `__repr__`.
        """
        return ''


class URL(Validator):
    """Validate a URL.

    :param bool relative: Whether to allow relative URLs.
    :param str error: Error message to raise in case of a validation error.
        Can be interpolated with `{input}`.
    :param set schemes: Valid schemes. By default, ``http``, ``https``,
        ``ftp``, and ``ftps`` are allowed.
    """

    URL_REGEX = re.compile(
        r'^(?:[a-z0-9\.\-\+]*)://'  # scheme is validated separately
        r'(?:[^:@]+?:[^:@]*?@|)'  # basic auth
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    RELATIVE_URL_REGEX = re.compile(
        r'^((?:[a-z0-9\.\-\+]*)://'  # scheme is validated separately
        r'(?:[^:@]+?:[^:@]*?@|)'  # basic auth
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # host is optional, allow for relative URLs

    default_message = 'Not a valid URL.'
    default_schemes = set(['http', 'https', 'ftp', 'ftps'])

    # TODO; Switch position of `error` and `schemes` in 3.0
    def __init__(self, relative=False, error=None, schemes=None):
        self.relative = relative
        self.error = error or self.default_message
        self.schemes = schemes or self.default_schemes

    def _repr_args(self):
        return 'relative={0!r}'.format(self.relative)

    def _format_error(self, value):
        return self.error.format(input=value)

    def __call__(self, value):
        message = self._format_error(value)
        if not value:
            raise ValidationError(message)

        # Check first if the scheme is valid
        if '://' in value:
            scheme = value.split('://')[0].lower()
            if scheme not in self.schemes:
                raise ValidationError(message)

        regex = self.RELATIVE_URL_REGEX if self.relative else self.URL_REGEX

        if not regex.search(value):
            raise ValidationError(message)

        return value


class Email(Validator):
    """Validate an email address.

    :param str error: Error message to raise in case of a validation error. Can be
        interpolated with `{input}`.
    """

    USER_REGEX = re.compile(
        r"(^[-!#$%&'*+/=?^`{}|~\w]+(\.[-!#$%&'*+/=?^`{}|~\w]+)*$"  # dot-atom
        # quoted-string
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]'
        r'|\\[\001-\011\013\014\016-\177])*"$)', re.IGNORECASE | re.UNICODE)

    DOMAIN_REGEX = re.compile(
        # domain
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}|[A-Z0-9-]{2,})$'
        # literal form, ipv4 address (SMTP 4.1.3)
        r'|^\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)'
        r'(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$', re.IGNORECASE | re.UNICODE)

    DOMAIN_WHITELIST = ('localhost',)

    default_message = 'Not a valid email address.'

    def __init__(self, error=None):
        self.error = error or self.default_message

    def _format_error(self, value):
        return self.error.format(input=value)

    def __call__(self, value):
        message = self._format_error(value)

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


class Range(Validator):
    """Validator which succeeds if the value it is passed is greater
    or equal to ``min`` and less than or equal to ``max``. If ``min``
    is not specified, or is specified as `None`, no lower bound
    exists. If ``max`` is not specified, or is specified as `None`,
    no upper bound exists.

    :param min: The minimum value (lower bound). If not provided, minimum
        value will not be checked.
    :param max: The maximum value (upper bound). If not provided, maximum
        value will not be checked.
    :param str error: Error message to raise in case of a validation error.
        Can be interpolated with `{input}`, `{min}` and `{max}`.
    """

    message_min = 'Must be at least {min}.'
    message_max = 'Must be at most {max}.'
    message_all = 'Must be between {min} and {max}.'

    def __init__(self, min=None, max=None, error=None):
        self.min = min
        self.max = max
        self.error = error

    def _repr_args(self):
        return 'min={0!r}, max={1!r}'.format(self.min, self.max)

    def _format_error(self, value, message):
        return (self.error or message).format(input=value, min=self.min, max=self.max)

    def __call__(self, value):
        if self.min is not None and value < self.min:
            message = self.message_min if self.max is None else self.message_all
            raise ValidationError(self._format_error(value, message))

        if self.max is not None and value > self.max:
            message = self.message_max if self.min is None else self.message_all
            raise ValidationError(self._format_error(value, message))

        return value


class Length(Range):
    """Validator which succeeds if the value passed to it has a
    length between a minimum and maximum. Uses len(), so it
    can work for strings, lists, or anything with length.

    :param int min: The minimum length. If not provided, minimum length
        will not be checked.
    :param int max: The maximum length. If not provided, maximum length
        will not be checked.
    :param int equal: The exact length. If provided, maximum and minimum
        length will not be checked.
    :param str error: Error message to raise in case of a validation error.
        Can be interpolated with `{input}`, `{min}` and `{max}`.
    """

    message_min = 'Shorter than minimum length {min}.'
    message_max = 'Longer than maximum length {max}.'
    message_all = 'Length must be between {min} and {max}.'
    message_equal = 'Length must be {equal}.'

    def __init__(self, min=None, max=None, error=None, equal=None):
        if equal is not None and any([min, max]):
            raise ValueError(
                'The `equal` parameter was provided, maximum or '
                'minimum parameter must not be provided.'
            )

        super(Length, self).__init__(min, max, error)
        self.equal = equal

    def _repr_args(self):
        return 'min={0!r}, max={1!r}, equal={2!r}'.format(self.min, self.max, self.equal)

    def _format_error(self, value, message):
        return (self.error or message).format(input=value, min=self.min, max=self.max,
                                              equal=self.equal)

    def __call__(self, value):
        length = len(value)

        if self.equal is not None:
            if length != self.equal:
                raise ValidationError(self._format_error(value, self.message_equal))
            return value

        if self.min is not None and length < self.min:
            message = self.message_min if self.max is None else self.message_all
            raise ValidationError(self._format_error(value, message))

        if self.max is not None and length > self.max:
            message = self.message_max if self.min is None else self.message_all
            raise ValidationError(self._format_error(value, message))

        return value


class Equal(Validator):
    """Validator which succeeds if the ``value`` passed to it is
    equal to ``comparable``.

    :param comparable: The object to compare to.
    :param str error: Error message to raise in case of a validation error.
        Can be interpolated with `{input}` and `{other}`.
    """

    default_message = 'Must be equal to {other}.'

    def __init__(self, comparable, error=None):
        self.comparable = comparable
        self.error = error or self.default_message

    def _repr_args(self):
        return 'comparable={0!r}'.format(self.comparable)

    def _format_error(self, value):
        return self.error.format(input=value, other=self.comparable)

    def __call__(self, value):
        if value != self.comparable:
            raise ValidationError(self._format_error(value))
        return value


class Regexp(Validator):
    """Validate ``value`` against the provided regex.

    :param regex: The regular expression string to use. Can also be a compiled
        regular expression pattern.
    :param flags: The regexp flags to use, for example re.IGNORECASE. Ignored
        if ``regex`` is not a string.
    :param str error: Error message to raise in case of a validation error.
        Can be interpolated with `{input}` and `{regex}`.
    """

    default_message = 'String does not match expected pattern.'

    def __init__(self, regex, flags=0, error=None):
        self.regex = re.compile(regex, flags) if isinstance(regex, basestring) else regex
        self.error = error or self.default_message

    def _repr_args(self):
        return 'regex={0!r}'.format(self.regex)

    def _format_error(self, value):
        return self.error.format(input=value, regex=self.regex.pattern)

    def __call__(self, value):
        if self.regex.match(value) is None:
            raise ValidationError(self._format_error(value))

        return value


class Predicate(Validator):
    """Call the specified ``method`` of the ``value`` object. The
    validator succeeds if the invoked method returns an object that
    evaluates to True in a Boolean context. Any additional keyword
    argument will be passed to the method.

    :param str method: The name of the method to invoke.
    :param str error: Error message to raise in case of a validation error.
        Can be interpolated with `{input}` and `{method}`.
    :param kwargs: Additional keyword arguments to pass to the method.
    """

    default_message = 'Invalid input.'

    def __init__(self, method, error=None, **kwargs):
        self.method = method
        self.error = error or self.default_message
        self.kwargs = kwargs

    def _repr_args(self):
        return 'method={0!r}, kwargs={1!r}'.format(self.method, self.kwargs)

    def _format_error(self, value):
        return self.error.format(input=value, method=self.method)

    def __call__(self, value):
        method = getattr(value, self.method)

        if not method(**self.kwargs):
            raise ValidationError(self._format_error(value))

        return value


class NoneOf(Validator):
    """Validator which fails if ``value`` is a member of ``iterable``.

    :param iterable iterable: A sequence of invalid values.
    :param str error: Error message to raise in case of a validation error. Can be
        interpolated using `{input}` and `{values}`.
    """

    default_message = 'Invalid input.'

    def __init__(self, iterable, error=None):
        self.iterable = iterable
        self.values_text = ', '.join(text_type(each) for each in self.iterable)
        self.error = error or self.default_message

    def _repr_args(self):
        return 'iterable={0!r}'.format(self.iterable)

    def _format_error(self, value):
        return self.error.format(
            input=value,
            values=self.values_text,
        )

    def __call__(self, value):
        try:
            if value in self.iterable:
                raise ValidationError(self._format_error(value))
        except TypeError:
            pass

        return value


class OneOf(Validator):
    """Validator which succeeds if ``value`` is a member of ``choices``.

    :param iterable choices: A sequence of valid values.
    :param iterable labels: Optional sequence of labels to pair with the choices.
    :param str error: Error message to raise in case of a validation error. Can be
        interpolated with `{input}`, `{choices}` and `{labels}`.
    """

    default_message = 'Not a valid choice.'

    def __init__(self, choices, labels=None, error=None):
        self.choices = choices
        self.choices_text = ', '.join(text_type(choice) for choice in self.choices)
        self.labels = labels if labels is not None else []
        self.labels_text = ', '.join(text_type(label) for label in self.labels)
        self.error = error or self.default_message

    def _repr_args(self):
        return 'choices={0!r}, labels={1!r}'.format(self.choices, self.labels)

    def _format_error(self, value):
        return self.error.format(
            input=value,
            choices=self.choices_text,
            labels=self.labels_text,
        )

    def __call__(self, value):
        try:
            if value not in self.choices:
                raise ValidationError(self._format_error(value))
        except TypeError:
            raise ValidationError(self._format_error(value))

        return value

    def options(self, valuegetter=text_type):
        """Return a generator over the (value, label) pairs, where value
        is a string associated with each choice. This convenience method
        is useful to populate, for instance, a form select field.

        :param valuegetter: Can be a callable or a string. In the former case, it must
            be a one-argument callable which returns the value of a
            choice. In the latter case, the string specifies the name
            of an attribute of the choice objects. Defaults to `str()`
            or `unicode()`.
        """
        valuegetter = valuegetter if callable(valuegetter) else attrgetter(valuegetter)
        pairs = zip_longest(self.choices, self.labels, fillvalue='')

        return ((valuegetter(choice), label) for choice, label in pairs)


class ContainsOnly(OneOf):
    """Validator which succeeds if ``value`` is a sequence and each element
    in the sequence is also in the sequence passed as ``choices``.

    :param iterable choices: Same as :class:`OneOf`.
    :param iterable labels: Same as :class:`OneOf`.
    :param str error: Same as :class:`OneOf`.
    """

    default_message = 'One or more of the choices you made was not acceptable.'

    def _format_error(self, value):
        value_text = ', '.join(text_type(val) for val in value)
        return super(ContainsOnly, self)._format_error(value_text)

    def __call__(self, value):
        choices = list(self.choices)

        if not value and choices:
            raise ValidationError(self._format_error(value))

        # We check list.index instead of using set.issubset so that
        # unhashable types are handled.
        for val in value:
            try:
                index = choices.index(val)
            except ValueError:
                raise ValidationError(self._format_error(value))
            else:
                del choices[index]

        return value
