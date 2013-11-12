# -*- coding: utf-8 -*-
'''Field classes for formatting and validating the serialized object.

Adapted from https://github.com/twilio/flask-restful/blob/master/flask_restful/fields.py.
See the `NOTICE <https://github.com/sloria/marshmallow/blob/master/NOTICE>`_
file for more licensing information.
'''
from __future__ import absolute_import
from decimal import Decimal as MyDecimal, ROUND_HALF_EVEN, Inexact, Context

from marshmallow import core, types
from marshmallow.base import Field
from marshmallow.compat import text_type, OrderedDict
from marshmallow.exceptions import MarshallingException


def _is_indexable_but_not_string(obj):
    return not hasattr(obj, "strip") and hasattr(obj, "__getitem__")


def _get_value(key, obj, default=None):
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
    if _is_indexable_but_not_string(obj):
        try:
            return obj[key]
        except KeyError:
            return default
    if hasattr(obj, key):
        return getattr(obj, key)
    return default


def _to_marshallable_type(obj):
    """Helper for converting an object to a dictionary only if it is not
    dictionary already or an indexable object nor a simple type"""
    if obj is None:
        return None  # make it idempotent for None

    if hasattr(obj, '__getitem__'):
        return obj  # it is indexable it is ok

    if hasattr(obj, '__marshallable__'):
        return obj.__marshallable__()

    return dict(obj.__dict__)


def float_to_decimal(f):
    "Convert a floating point number to a Decimal with no loss of information"
    n, d = f.as_integer_ratio()
    numerator, denominator = MyDecimal(n), MyDecimal(d)
    ctx = Context(prec=60)
    result = ctx.divide(numerator, denominator)
    while ctx.flags[Inexact]:
        ctx.flags[Inexact] = False
        ctx.prec *= 2
        result = ctx.divide(numerator, denominator)
    return result


class Raw(Field):
    """Basic field from which other fields should extend. It applies no
    formatting by default, and should only be used in cases where
    data does not need to be formatted before being serialized. Fields should
    throw a MarshallingException in case of parsing problem.

    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        ``None``, assumes the attribute has the same name as the field.
    """

    def __init__(self, default=None, attribute=None):
        self.attribute = attribute
        self.default = default

    def get_value(self, key, obj):
        '''Return the value for a given key from an object.'''
        return _get_value(key if self.attribute is None else self.attribute, obj)

    def format(self, value):
        """Formats a field's value. No-op by default, concrete fields should
        override this and apply the appropriate formatting.

        :param value: The value to format
        :exception MarshallingException: In case of formatting problem

        Ex::

            class TitleCase(Raw):
                def format(self, value):
                    return unicode(value).title()
        """
        return value

    def output(self, key, obj):
        """Pulls the value for the given key from the object, applies the
        field's formatting and returns the result.
        :exception MarshallingException: In case of formatting problem
        """
        value = self.get_value(key, obj)
        if value is None:
            return self.default
        return self.format(value)


class Nested(Raw):
    """Allows you to nest a :class:`Serializer <marshmallow.Serializer>`
    or set of fields inside a field.

    Example: ::

        user = fields.Nested(UserSerializer)

    :param Serializer nested: The Serializer class or instance to nest.
    :param bool exclude: A list or tuple of fields to exclude.
    :param bool only: A list or tuple of fields to marshal. If ``None``, all fields
        will be marshalled. Takes precedence over ``exclude``.
    :param bool allow_null: Whether to return None instead of a dictionary
        with null keys, if a nested dictionary has all-null keys
    """

    def __init__(self, nested, exclude=None, only=None, allow_null=False, **kwargs):
        try:
            if issubclass(nested, core.Serializer):
                self.serializer = nested()
        except TypeError:
            if isinstance(nested, core.Serializer):
                self.serializer = nested

        self.nested =  self.serializer.fields
        self.allow_null = allow_null
        # Marshall all fields by default
        self.only = set(self.nested) if only is None else set(only)
        if exclude and only:
            # Make sure the only takes precedence
            self.exclude = set(exclude) - self.only
        else:
            self.exclude = set([]) if exclude is None else set(exclude)
        super(Nested, self).__init__(**kwargs)

    def output(self, key, obj):
        value = self.get_value(key, obj)
        if self.allow_null and value is None:
            return None
        filtered = ((k, v) for k, v in self.nested.items()
                    if k in self.only and k not in self.exclude)
        fields = OrderedDict(filtered)
        ret = self.serializer.marshal(value, fields)
        # Parent should get any errors stored after marshalling
        if self.serializer.errors:
            self.parent.errors[key] = self.serializer.errors
        return ret


class List(Raw):
    '''A list field.

    Example: ::

        numbers = fields.List(fields.Float)

    :param cls_or_instance: A field class or instance.
    '''
    def __init__(self, cls_or_instance, **kwargs):
        super(List, self).__init__(**kwargs)
        if isinstance(cls_or_instance, type):
            if not issubclass(cls_or_instance, Field):
                raise MarshallingException("The type of the list elements "
                                           "must be a subclass of "
                                           "marshmallow.base.Field")
            self.container = cls_or_instance()
        else:
            if not isinstance(cls_or_instance, Field):
                raise MarshallingException("The instances of the list "
                                           "elements must be of type "
                                           "marshmallow.base.Field")
            self.container = cls_or_instance

    def output(self, key, data):
        value = self.get_value(key, data)
        # we cannot really test for external dict behavior
        if _is_indexable_but_not_string(value) and not isinstance(value, dict):
            # Convert all instances in typed list to container type
            return [self.container.output(idx, value) for idx, val
                    in enumerate(value)]

        if value is None:
            return self.default

        return [core.marshal(value, self.container.nested)]


class String(Raw):
    def format(self, value):
        try:
            return text_type(value)
        except ValueError as ve:
            raise MarshallingException(ve)


class NumberField(Raw):
    '''Base class for number fields.'''

    num_type = int

    def __init__(self, default=0, attribute=None, as_string=False):
        self.as_string = as_string
        super(NumberField, self).__init__(default=default, attribute=attribute)

    def _format_num(self, value):
        '''Return the correct value for a number, given the passed in
        arguments to __init__.
        '''
        if self.as_string:
            return repr(self.num_type(value))
        else:
            return self.num_type(value)

    def format(self, value):
        try:
            if value is None:
                return self._format_num(self.default)
            return self._format_num(value)
        except ValueError as ve:
            raise MarshallingException(ve)


class Integer(NumberField):
    """An integer field.

    :param bool as_string: If True, format the value as a string.
    """

    num_type = int


class Boolean(Raw):
    '''A boolean field.'''
    def format(self, value):
        return bool(value)


class FormattedString(Raw):
    def __init__(self, src_str):
        super(FormattedString, self).__init__()
        self.src_str = text_type(src_str)

    def output(self, key, obj):
        try:
            data = _to_marshallable_type(obj)
            return self.src_str.format(**data)
        except (TypeError, IndexError) as error:
            raise MarshallingException(error)


class Float(NumberField):
    """
    A double as IEEE-754 double precision string.

    :param bool as_string: If True, format the value as a string.
    """

    num_type = float


class Arbitrary(NumberField):
    """A floating point number with an arbitrary precision,
    formatted as as string.
    ex: 634271127864378216478362784632784678324.23432
    """
    # No as_string param
    def __init__(self, default=0, attribute=None):
        super(Arbitrary, self).__init__(default=default, attribute=attribute)

    def format(self, value):
        try:
            if value is None:
                return text_type(float_to_decimal(float(self.default)))
            return text_type(float_to_decimal(float(value)))
        except ValueError as ve:
            raise MarshallingException(ve)


class DateTime(Raw):
    """A RFC822-formatted datetime string in UTC.
    """

    def format(self, value):
        try:
            return types.rfc822(value, localtime=False)
        except AttributeError as ae:
            raise MarshallingException(ae)


class LocalDateTime(Raw):
    """A RFC822-formatted datetime string in localized time, relative to UTC.

    .. warning::
        Output may be different on different operating systems due to variations
        in how localtimes are handled. When in doubt, use the
        :class:`DateTime <marshmallow.fields.DateTime>` field.
    """

    def format(self, value):
        try:
            return types.rfc822(value, localtime=True)
        except AttributeError as ae:
            raise MarshallingException(ae)

ZERO = MyDecimal()


class Fixed(NumberField):
    """A fixed-precision number as a string.
    """

    def __init__(self, decimals=5, default=0, attribute=None):
        super(Fixed, self).__init__(default=default, attribute=attribute)
        self.precision = MyDecimal('0.' + '0' * (decimals - 1) + '1')

    def format(self, value):
        try:
            dvalue = float_to_decimal(float(value))
        except ValueError as ve:
            raise MarshallingException(ve)
        if not dvalue.is_normal() and dvalue != ZERO:
            raise MarshallingException('Invalid Fixed precision number.')
        return text_type(dvalue.quantize(self.precision, rounding=ROUND_HALF_EVEN))


class Price(Fixed):
    def __init__(self, decimals=2, **kwargs):
        super(Price, self).__init__(decimals=decimals, **kwargs)


class Url(Raw):
    """A validated URL field.

    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        ``None``, assumes the attribute has the same name as the field.
    :param bool relative: Allow relative URLs.
    """
    def __init__(self, default=None, attribute=None, relative=False):
        super(Url, self).__init__(default=default, attribute=attribute)
        self.relative = relative

    def output(self, key, obj):
        value = self.get_value(key, obj)
        if value is None:
            return self.default
        try:
            return types.url(value, relative=self.relative)
        except Exception as err:
            raise MarshallingException(err)


class Email(Raw):
    """A validated email field.
    """
    def output(self, key, obj):
        value = self.get_value(key, obj)
        if value is None:
            return self.default
        try:
            return types.email(value)
        except Exception as err:
            raise MarshallingException(err)


class Method(Raw):
    """A field that takes the value returned by a Serializer method.

    :param str method_name: The name of the Serializer method from which
        to retrieve the value. The method must take a single argument ``obj``
        (in addition to self) that is the object to be serialized.
    """

    def __init__(self, method_name):
        self.method_name = method_name
        super(Method, self).__init__()

    def output(self, key, obj):
        try:
            return getattr(self.parent, self.method_name)(obj)
        except AttributeError:
            pass


class Function(Raw):
    '''A field that takes the value returned by a function.

    :param function func: A callable function from which to retrieve the value.
        The function must take a single argument ``obj`` which is the object
        to be serialized.
    '''

    def __init__(self, func):
        self.func = func

    def output(self, key, obj):
        try:
            return self.func(obj)
        except TypeError as te:  # Function is not callable
            raise MarshallingException(te)
        except AttributeError:
            pass
