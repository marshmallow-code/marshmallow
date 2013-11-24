# -*- coding: utf-8 -*-
'''Field classes for formatting and validating the serialized object.
'''
# Adapted from https://github.com/twilio/flask-restful/blob/master/flask_restful/fields.py.
# See the `NOTICE <https://github.com/sloria/marshmallow/blob/master/NOTICE>`_
# file for more licensing information.

from __future__ import absolute_import
from decimal import Decimal as MyDecimal, ROUND_HALF_EVEN

from marshmallow import validate, utils
from marshmallow.base import FieldABC, SerializerABC
from marshmallow.compat import text_type, OrderedDict, iteritems, total_seconds
from marshmallow.exceptions import MarshallingError


class Marshaller(object):
    '''Callable class responsible for marshalling data and storing errors.

    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.
    :param bool strict: If ``True``, raise errors if invalid data are passed in
        instead of failing silently and storing the errors.
    '''
    def __init__(self, prefix='', strict=False):
        self.prefix = prefix
        self.strict = strict
        self.errors = {}

    def marshal(self, data, fields_dict):
        """Takes raw data (in the form of a dict, list, object) and a dict of
        fields to output and filters the data based on those fields.

        :param data: The actual object(s) from which the fields are taken from
        :param dict fields: A dict whose keys will make up the final serialized
                       response output.
        """
        if utils.is_collection(data):
            return [self.marshal(d, fields_dict) for d in data]
        items = []
        for attr_name, field_obj in iteritems(fields_dict):
            key = self.prefix + attr_name
            try:
                if isinstance(field_obj, dict):
                    item = (key, self.marshal(data, field_obj))
                else:
                    try:
                        item = (key, field_obj.output(attr_name, data))
                    except TypeError:
                        # field declared as a class, not an instance
                        if isinstance(field_obj, type) and \
                            issubclass(field_obj, FieldABC):
                            msg = ('Field for "{0}" must be declared as a '
                                            "Field instance, not a class. "
                                            'Did you mean "fields.{1}()"?'
                                            .format(attr_name, field_obj.__name__))
                            raise TypeError(msg)
                        raise
            except MarshallingError as err:  # Store errors
                if self.strict:
                    raise err
                self.errors[key] = text_type(err)
                item = (key, None)
            items.append(item)
        return OrderedDict(items)

    # Make an instance callable
    __call__ = marshal

# Singleton marshaller method for use in this module
marshal = Marshaller(strict=True)


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
    if utils.is_indexable_but_not_string(obj):
        try:
            return obj[key]
        except KeyError:
            return default
    if hasattr(obj, key):
        return getattr(obj, key)
    return default


class Raw(FieldABC):
    """Basic field from which other fields should extend. It applies no
    formatting by default, and should only be used in cases where
    data does not need to be formatted before being serialized. Fields should
    throw a MarshallingError in case of parsing problem.

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
        :exception MarshallingError: In case of formatting problem

        Ex::

            class TitleCase(Raw):
                def format(self, value):
                    return unicode(value).title()
        """
        return value

    def output(self, key, obj):
        """Pulls the value for the given key from the object, applies the
        field's formatting and returns the result.
        :exception MarshallingError: In case of formatting problem
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
    :param iterable exclude: A list or tuple of fields to exclude.
    :param iterable only: A list or tuple of fields to marshal. If ``None``, all fields
        will be marshalled. Takes precedence over ``exclude``.
    :param bool allow_null: Whether to return None instead of a dictionary
        with null keys, if a nested dictionary has all-null keys
    """

    def __init__(self, nested, exclude=None, only=None, allow_null=False, **kwargs):
        self.nested = nested
        self.allow_null = allow_null
        self.only = only
        self.exclude = exclude
        self.serializer = None
        super(Nested, self).__init__(**kwargs)

    def __get_fields_to_marshal(self, all_fields):
        '''Filter the all_fields based on self.only and self.exclude.'''
        # Default 'only' to all the nested fields
        only = set(all_fields) if self.only is None else set(self.only)
        if self.exclude and self.only:
            # Make sure that only takes precedence
            exclude = set(self.exclude) - only
        else:
            exclude = set([]) if self.exclude is None else set(self.exclude)
        filtered = ((k, v) for k, v in all_fields.items()
                    if k in only and k not in exclude)
        return OrderedDict(filtered)

    def output(self, key, obj):
        nested_obj = self.get_value(key, obj)
        if self.allow_null and nested_obj is None:
            return None
        if isinstance(self.nested, SerializerABC):
            self.serializer = self.nested
            self.nested._data = nested_obj
        elif isinstance(self.nested, type) and \
                issubclass(self.nested, SerializerABC):
            self.serializer = self.nested(nested_obj)
        else:
            raise ValueError("Nested fields must be passed a Serializer, not {0}."
                            .format(self.nested.__class__))
        fields = self.__get_fields_to_marshal(self.serializer.fields)
        ret = self.serializer.marshal(nested_obj, fields)
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
            if not issubclass(cls_or_instance, FieldABC):
                raise MarshallingError("The type of the list elements "
                                           "must be a subclass of "
                                           "marshmallow.base.FieldABC")
            self.container = cls_or_instance()
        else:
            if not isinstance(cls_or_instance, FieldABC):
                raise MarshallingError("The instances of the list "
                                           "elements must be of type "
                                           "marshmallow.base.FieldABC")
            self.container = cls_or_instance

    def output(self, key, data):
        value = self.get_value(key, data)
        # we cannot really test for external dict behavior
        if utils.is_indexable_but_not_string(value) and not isinstance(value, dict):
            # Convert all instances in typed list to container type
            return [self.container.output(idx, value) for idx
                    in range(len(value))]

        if value is None:
            return self.default

        return [marshal(value, self.container.nested)]


class String(Raw):
    """A string field."""

    def __init__(self, default='', attribute=None):
        return super(String, self).__init__(default, attribute)

    def format(self, value):
        try:
            return text_type(value)
        except ValueError as ve:
            raise MarshallingError(ve)


class UUID(String):
    """A UUID field."""
    pass


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
            raise MarshallingError(ve)


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
            data = utils.to_marshallable_type(obj)
            return self.src_str.format(**data)
        except (TypeError, IndexError) as error:
            raise MarshallingError(error)


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
                return text_type(utils.float_to_decimal(float(self.default)))
            return text_type(utils.float_to_decimal(float(value)))
        except ValueError as ve:
            raise MarshallingError(ve)

DATEFORMAT_FUNCTIONS = {
    "iso": utils.isoformat,
    "rfc": utils.rfcformat,
}


class DateTime(Raw):
    """A formatted datetime string in UTC.
        ex. ``"Sun, 10 Nov 2013 07:23:45 -0000"``

    :param str format: Either ``"rfc"`` (for RFC822), ``"iso"`` (for ISO8601),
        or a date format string. If ``None``, defaults to "rfc".
    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        ``None``, assumes the attribute has the same name as the field.
    """
    localtime = False

    def __init__(self, format=None, default=None, attribute=None):
        super(DateTime, self).__init__(default=default, attribute=attribute)
        self.dateformat = format

    def format(self, value):
        self.dateformat = self.dateformat or 'rfc'
        try:
            format_func = DATEFORMAT_FUNCTIONS.get(self.dateformat, None)
            if format_func:
                return format_func(value, localtime=self.localtime)
            else:
                return value.strftime(self.dateformat)
        except AttributeError as ae:
            raise MarshallingError(ae)


class LocalDateTime(DateTime):
    """A formatted datetime string in localized time, relative to UTC.
        ex. ``"Sun, 10 Nov 2013 08:23:45 -0600"``
    Takes the same arguments as :class:`DateTime <marshmallow.fields.DateTime>`.

    .. warning::
        Output may be different on different operating systems due to variations
        in how localtimes are handled. When in doubt, use the
        :class:`DateTime <marshmallow.fields.DateTime>` field.
    """
    localtime = True


class Time(Raw):
    """ISO8601-formatted time string."""

    def format(self, value):
        try:
            ret = value.isoformat()
        except AttributeError:
            raise MarshallingError('{0} cannot be formatted as a time.'
                                    .format(repr(value)))
        if value.microsecond:
            return ret[:12]
        return ret


class Date(Raw):
    """ISO8601-formatted date string."""

    def format(self, value):
        try:
            return value.isoformat()
        except AttributeError:
            raise MarshallingError('{0} cannot be formatted as a date.'
                                    .format(repr(value)))
        return value


class TimeDelta(Raw):
    '''Formats time delta objects, returning the total number of seconds
    as a float.
    '''

    def format(self, value):
        try:
            return total_seconds(value)
        except AttributeError:
            raise MarshallingError('{0} cannot be formatted as a timedelta.'
                                    .format(repr(value)))
        return value


ZERO = MyDecimal()


class Fixed(NumberField):
    """A fixed-precision number as a string.
    """

    def __init__(self, decimals=5, default=0, attribute=None):
        super(Fixed, self).__init__(default=default, attribute=attribute)
        self.precision = MyDecimal('0.' + '0' * (decimals - 1) + '1')

    def format(self, value):
        try:
            dvalue = utils.float_to_decimal(float(value))
        except ValueError as ve:
            raise MarshallingError(ve)
        if not dvalue.is_normal() and dvalue != ZERO:
            raise MarshallingError('Invalid Fixed precision number.')
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
            return validate.url(value, relative=self.relative)
        except Exception as err:
            raise MarshallingError(err)


class Email(Raw):
    """A validated email field.
    """
    def output(self, key, obj):
        value = self.get_value(key, obj)
        if value is None:
            return self.default
        try:
            return validate.email(value)
        except Exception as err:
            raise MarshallingError(err)


class Method(Raw):
    """A field that takes the value returned by a Serializer method.

    :param str method_name: The name of the Serializer method from which
        to retrieve the value. The method must take two arguments, the first is
        ``key`` identifying the name of the attribute to be serialised and the
        second is ``obj`` which is the object (in addition to self) that is the
        object to be serialized.
    """

    def __init__(self, method_name):
        self.method_name = method_name
        super(Method, self).__init__()

    def output(self, key, obj):
        try:
            return getattr(self.parent, self.method_name)(key, obj)
        except AttributeError:
            pass


class Function(Raw):
    '''A field that takes the value returned by a function.

    :param function func: A callable function from which to retrieve the value.
        The function must take two arguments, the first is ``key`` identifying
        the name of the attribute to be serialised and the second is ``obj``
        which is the object to be serialized.
    '''

    def __init__(self, func):
        self.func = func

    def output(self, key, obj):
        try:
            return self.func(key, obj)
        except TypeError as te:  # Function is not callable
            raise MarshallingError(te)
        except AttributeError:
            pass
