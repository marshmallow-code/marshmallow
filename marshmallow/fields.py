# -*- coding: utf-8 -*-
"""Field classes for formatting and validating the serialized object.
"""
# Adapted from https://github.com/twilio/flask-restful/blob/master/flask_restful/fields.py.
# See the `NOTICE <https://github.com/sloria/marshmallow/blob/master/NOTICE>`_
# file for more licensing information.

from __future__ import absolute_import
from decimal import Decimal as MyDecimal, ROUND_HALF_EVEN
import inspect

from marshmallow import validate, utils, class_registry
from marshmallow.base import FieldABC, SerializerABC
from marshmallow.compat import (text_type, OrderedDict, iteritems, total_seconds,
                                basestring)
from marshmallow.exceptions import (
    MarshallingError,
    DeserializationError,
    ForcedError,
)

__all__ = [
    'Marshaller',
    'Raw',
    'Nested',
    'List',
    'String',
    'UUID',
    'Number',
    'Integer',
    'Boolean',
    'FormattedString',
    'Float',
    'Arbitrary',
    'DateTime',
    'LocalDateTime',
    'Time',
    'Date',
    'TimeDelta',
    'Fixed',
    'ZERO',
    'Price',
    'Url',
    'Email',
    'Method',
    'Function',
    'Select',
    'Enum',
]


class Marshaller(object):
    """Callable class responsible for marshalling data and storing errors.

    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.
    :param bool strict: If ``True``, raise errors if invalid data are passed in
        instead of failing silently and storing the errors.
    :param callable error_handler: Error handling function that receieves a
        dictionary of stored errors.
    """
    def __init__(self, prefix='', strict=False, error_handler=None):
        self.prefix = prefix
        self.strict = strict
        self.errors = {}

    def marshal(self, data, fields_dict, many=False):
        """Takes raw data (a dict, list, or other object) and a dict of
        fields to output and filters the data based on those fields.

        :param data: The actual object(s) from which the fields are taken from
        :param dict fields: A dict whose keys will make up the final serialized
                       response output.
        :param bool many: Set to ``True`` if ``data`` is a collection object
                        that is iterable.
        :returns: An OrderedDict of the marshalled data
        """
        if many and data is not None:
            return [self.marshal(d, fields_dict, many=False) for d in data]
        items = []
        for attr_name, field_obj in iteritems(fields_dict):
            key = self.prefix + attr_name
            try:
                item = (key, field_obj.output(attr_name, data))
            except MarshallingError as err:  # Store errors
                if self.strict:
                    raise err
                self.errors[key] = text_type(err)
                item = (key, None)
            except TypeError:
                # field declared as a class, not an instance
                if (isinstance(field_obj, type) and
                       issubclass(field_obj, FieldABC)):
                    msg = ('Field for "{0}" must be declared as a '
                                    "Field instance, not a class. "
                                    'Did you mean "fields.{1}()"?'
                                    .format(attr_name, field_obj.__name__))
                    raise TypeError(msg)
                raise
            items.append(item)
        return OrderedDict(items)

    # Make an instance callable
    __call__ = marshal

# Singleton marshaller function for use in this module
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
    if isinstance(key, basestring) and hasattr(obj, key):
        return getattr(obj, key)
    if utils.is_indexable_but_not_string(obj):
        try:
            return obj[key]
        except KeyError:
            return default
    return default


class Raw(FieldABC):
    """Basic field from which other fields should extend. It applies no
    formatting by default, and should only be used in cases where
    data does not need to be formatted before being serialized. Fields should
    throw a MarshallingError in case of parsing problem.

    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        ``None``, assumes the attribute has the same name as the field.
    :param str error: Error message stored upon validation failure.
    :param callable validate: Validation function that takes the output as its
        only paramter and returns a boolean. If it returns False, a
        MarshallingError is raised.
    :param bool required: Make a field required. If a field is ``None``,
        raise a MarshallingError.
    """
    _CHECK_REQUIRED = True

    def __init__(self, default=None, attribute=None, error=None,
                validate=None, required=False):
        self.attribute = attribute
        self.default = default
        self.error = error
        self.validate = validate
        self.required = required

    def get_value(self, key, obj):
        """Return the value for a given key from an object."""
        check_key = key if self.attribute is None else self.attribute
        return _get_value(check_key, obj)

    def _call_with_validation(self, method, exception_class, *args, **kwargs):
        """Invoke ``method``and validate the output. Call self.validate when
        appropriate, and raise ``exception_class`` if a validation error
        occurs.
        """
        try:
            func = getattr(self, method)
            output = func(*args, **kwargs)
            if callable(self.validate):
                if not self.validate(output):
                    msg = 'Validator {0}({1}) is not True'.format(
                        self.validate.__name__, output
                    )
                    raise exception_class(self.error or msg)
            return output
        # TypeErrors should be raised if fields are not declared as instances
        except TypeError:
            raise
        # Raise ForcedErrors
        except ForcedError as err:
            if err.underlying_exception:
                raise err.underlying_exception
            else:
                raise err
        except Exception as error:
            raise exception_class(getattr(self, 'error', None) or error)

    def output(self, key, obj):
        """Pulls the value for the given key from the object, applies the
        field's formatting and returns the result.

        :param str key: The attibute or key to get.
        :param str obj: The object to pull the key from.
        :exception MarshallingError: In case of validation or formatting problem
        """
        value = self.get_value(key, obj)
        if value is None and self._CHECK_REQUIRED:
            if hasattr(self, 'required') and self.required:
                raise MarshallingError('Missing data for required field.')
            elif hasattr(self, 'default'):
                return self._format(self.default)
            else:
                return None
        return self._call_with_validation('_serialize', MarshallingError,
                                          value, key, obj)

    def deserialize(self, value):
        """Deserialize ``value``."""
        return self._call_with_validation('_deserialize', DeserializationError, value)

    # Methods for concrete classes to override.

    def _format(self, value):
        """Formats a field's value. No-op by default, concrete fields should
        override this and apply the appropriate formatting.

        :param value: The value to format
        :exception MarshallingError: In case of formatting problem

        Ex::

            class TitleCase(Raw):
                def _format(self, value):
                    return unicode(value).title()
        """
        return value

    def _serialize(self, value, key, obj):
        """Serializes ``value`` to a basic Python datatype.

        :param value: The value to be serialized.
        :param str key: The attribute or key on the object to be serialized.
        :param obj: The object the value was pulled from.
        """
        return self._format(value)

    def _deserialize(self, value):
        """Deserialize value."""
        return value


class Nested(Raw):
    """Allows you to nest a :class:`Serializer <marshmallow.Serializer>`
    inside a field.

    Examples: ::

        user = fields.Nested(UserSerializer)
        user2 = fields.Nested('UserSerializer')  # Equivalent to above
        collaborators = fields.Nested(UserSerializer(many=True, only='id'))
        parent = fields.Nested('self')

    :param Serializer nested: The Serializer class, instance, or class name (string)
        to nest, or ``"self"`` to nest the serializer within itself.
    :param tuple exclude: A list or tuple of fields to exclude.
    :param only: A tuple or string of the field(s) to marshal. If ``None``, all fields
        will be marshalled. If a field name (string) is given, only a single
        value will be returned as output instead of a dictionary.
        This parameter takes precedence over ``exclude``.
    :param bool allow_null: Whether to return None instead of a dictionary
        with null keys, if a nested dictionary has all-null keys
    :param bool many: Whether the field is a collection of objects.
    """
    _CHECK_REQUIRED = False

    def __init__(self, nested, exclude=None, only=None, allow_null=False,
                many=False, **kwargs):
        self.nested = nested
        self.allow_null = allow_null
        self.only = only
        self.exclude = exclude or ()
        self.many = many
        self.__serializer = None
        self.__updated_fields = False  # ensures serializer fields are updated only once
        super(Nested, self).__init__(**kwargs)

    def __get_fields_to_marshal(self, all_fields):
        """Filter all_fields based on self.only and self.exclude """
        # Default 'only' to all the nested fields
        ret = OrderedDict()
        if all_fields is None:
            return ret
        elif isinstance(self.only, basestring):
            ret[self.only] = all_fields[self.only]
            return ret
        else:
            only = set(all_fields) if self.only is None else set(self.only)
        if self.exclude and self.only:
            # Make sure that only takes precedence
            exclude = set(self.exclude) - only
        else:
            exclude = set([]) if self.exclude is None else set(self.exclude)
        filtered = ((k, v) for k, v in all_fields.items()
                    if k in only and k not in exclude)
        return OrderedDict(filtered)

    @property
    def serializer(self):
        """The nested Serializer object."""
        # Cache the serializer instance
        if not self.__serializer:
            if isinstance(self.nested, SerializerABC):
                self.__serializer = self.nested
            elif isinstance(self.nested, type) and \
                    issubclass(self.nested, SerializerABC):
                self.__serializer = self.nested(None, many=self.many)
            elif isinstance(self.nested, basestring):
                if self.nested == 'self':
                    self.__serializer = self.parent  # The serializer this fields belongs to
                    # For now, don't allow nesting of depth > 1
                    self.exclude += (self.name, )  # Exclude this field
                else:
                    serializer_class = class_registry.get_class(self.nested)
                    self.__serializer = serializer_class(None, many=self.many)
            else:
                raise ForcedError(ValueError("Nested fields must be passed a Serializer, not {0}."
                                .format(self.nested.__class__)))
        return self.__serializer

    def _serialize(self, nested_obj, key, obj):
        if self.allow_null and nested_obj is None:
            return None
        self.serializer.many = self.many
        self.serializer.obj = nested_obj
        if not self.__updated_fields:
            self.__updated_fields = True
            self.serializer._update_fields()
        fields = self.__get_fields_to_marshal(self.serializer.fields)
        try:
            ret = self.serializer.marshal(nested_obj, fields, many=self.many)
        except TypeError as err:
            raise TypeError('Could not marshal nested object due to error:\n"{0}"\n'
                            'If the nested object is a collection, you need to set '
                            '"many=True".'.format(err))
        # Parent should get any errors stored after marshalling
        if self.serializer.errors:
            self.parent.errors[key] = self.serializer.errors
        if isinstance(self.only, basestring):  # self.only is a field name
            if self.many:
                return flatten(ret, key=self.only)
            else:
                return ret[self.only]
        return ret


def flatten(dictlist, key):
    """Flattens a list of dicts into just a list of values.
    ::

        >>> d = [{'id': 1, 'name': 'foo'}, {'id': 2, 'name': 'bar'}]
        >>> flatten(d, 'id')
        [1, 2]
    """
    return [d[key] for d in dictlist]


class List(Raw):
    """A list field.

    Example: ::

        numbers = fields.List(fields.Float)

    :param cls_or_instance: A field class or instance.
    """
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

    def _format(self, value):
        if utils.is_indexable_but_not_string(value) and not isinstance(value, dict):
            # Convert all instances in typed list to container type
            return [self.container.output(idx, value) for idx
                    in range(len(value))]
        if value is None:
            return self.default

        return [marshal(value, self.container.nested)]

    # Deserialization is identical to _format behavior
    _deserialize = _format


class String(Raw):
    """A string field."""

    def __init__(self, default='', attribute=None, *args, **kwargs):
        return super(String, self).__init__(default, attribute, *args, **kwargs)

    def _format(self, value):
        return text_type(value)

    def _deserialize(self, value):
        return text_type(value)


class UUID(String):
    """A UUID field."""
    pass


class Number(Raw):
    '''Base class for number fields.'''

    num_type = float

    def __init__(self, default=0.0, attribute=None, as_string=False, error=None, **kwargs):
        self.as_string = as_string
        super(Number, self).__init__(default=default, attribute=attribute,
            error=error, **kwargs)

    def _format_num(self, value):
        '''Return the correct value for a number, given the passed in
        arguments to __init__.
        '''
        if self.as_string:
            return repr(self.num_type(value))
        else:
            return self.num_type(value)

    def _validated(self, value, exception_class):
        """Format the value or raise ``exception_class`` if an error occurs."""
        try:
            if value is None:
                return self._format_num(self.default)
            return self._format_num(value)
        except ValueError as ve:
            raise exception_class(ve)

    def _format(self, value):
        return self._validated(value, MarshallingError)

    def _deserialize(self, value):
        return self._validated(value, DeserializationError)


class Integer(Number):
    """An integer field.

    :param bool as_string: If True, format the value as a string.
    """

    num_type = int

    def __init__(self, default=0, attribute=None, as_string=False, error=None, **kwargs):
        self.as_string = as_string
        super(Number, self).__init__(default=default, attribute=attribute,
            error=error, **kwargs)

class Boolean(Raw):
    """A boolean field."""

    #: Values that will deserialize to ``True``. If an empty set, any non-falsy
    #  value will deserialize to ``True``.
    truthy = set()
    #: Values that will deserialize to ``False``.
    falsy = set(['False', 'false', '0', 'null', 'None'])

    def _format(self, value):
        return bool(value)

    def _deserialize(self, value):
        if not value:
            return False
        try:
            value_str = text_type(value)
        except TypeError as error:
            raise DeserializationError(error)
        if value_str in self.falsy:
            return False
        elif self.truthy:
            if value_str in self.truthy:
                return True
            else:
                raise DeserializationError(
                    '{0!r} is not in {1} nor {2}'.format(
                        value_str, self.truthy, self.falsy
                    ))
        return True

class FormattedString(Raw):
    def __init__(self, src_str):
        super(FormattedString, self).__init__()
        self.src_str = text_type(src_str)

    def _serialize(self, value, key, obj):
        try:
            data = utils.to_marshallable_type(obj)
            return self.src_str.format(**data)
        except (TypeError, IndexError) as error:
            raise MarshallingError(error)


class Float(Number):
    """
    A double as IEEE-754 double precision string.

    :param bool as_string: If True, format the value as a string.
    """

    num_type = float


class Arbitrary(Number):
    """A floating point number with an arbitrary precision,
    formatted as as string.
    ex: 634271127864378216478362784632784678324.23432
    """
    # No as_string param
    def __init__(self, default=0, attribute=None, **kwargs):
        super(Arbitrary, self).__init__(default=default, attribute=attribute, **kwargs)

    def _validated(self, value, exception_class):
        """Format ``value`` or raise ``exception_class`` if an error occurs."""
        try:
            if value is None:
                return text_type(utils.float_to_decimal(float(self.default)))
            return text_type(utils.float_to_decimal(float(value)))
        except ValueError as ve:
            raise exception_class(ve)

    def _format(self, value):
        return self._validated(value, MarshallingError)

    def _deserialize(self, value):
        return self._validated(value, DeserializationError)


DATEFORMAT_SERIALIZATION_FUNCS = {
    "iso": utils.isoformat,
    "rfc": utils.rfcformat,
}

DATEFORMAT_DESERIALIZATION_FUNCS = {
    'rfc': utils.from_rfc,
    'iso': utils.from_iso,
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

    def __init__(self, format=None, default=None, attribute=None, **kwargs):
        super(DateTime, self).__init__(default=default, attribute=attribute, **kwargs)
        # Allow this to be None. It may be set later in the ``format`` method
        # This allows a Serializer to dynamically set the dateformat, e.g.
        # from a Meta option
        self.dateformat = format

    def _format(self, value):
        if value:
            self.dateformat = self.dateformat or 'rfc'
            format_func = DATEFORMAT_SERIALIZATION_FUNCS.get(self.dateformat, None)
            if format_func:
                return format_func(value, localtime=self.localtime)
            else:
                return value.strftime(self.dateformat)

    def _deserialize(self, value):
        self.dateformat = self.dateformat or 'rfc'
        func = DATEFORMAT_DESERIALIZATION_FUNCS.get(self.dateformat, None)
        if func:
            return func(value)
        else:
            raise DeserializationError(
                'Cannot deserialize {0!r} to a datetime'.format(value)
            )


class LocalDateTime(DateTime):
    """A formatted datetime string in localized time, relative to UTC.

        ex. ``"Sun, 10 Nov 2013 08:23:45 -0600"``

    Takes the same arguments as :class:`DateTime <marshmallow.fields.DateTime>`.
    """
    localtime = True


class Time(Raw):
    """ISO8601-formatted time string."""

    def _format(self, value):
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

    def _format(self, value):
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

    def _format(self, value):
        try:
            return total_seconds(value)
        except AttributeError:
            raise MarshallingError('{0} cannot be formatted as a timedelta.'
                                    .format(repr(value)))
        return value


ZERO = MyDecimal()


class Fixed(Number):
    """A fixed-precision number as a string.
    """

    def __init__(self, decimals=5, default=0, attribute=None, error=None,
                 *args, **kwargs):
        super(Fixed, self).__init__(default=default, attribute=attribute, error=error,
                            *args, **kwargs)
        self.precision = MyDecimal('0.' + '0' * (decimals - 1) + '1')

    # Override _format instead of _serialize so that default value also gets
    # formatted
    def _format(self, value):
        return self._validated(value, MarshallingError)

    def _deserialize(self, value):
        return self._validated(value, DeserializationError)

    def _validated(self, value, exception_class):
        if value is None:
            value = self.default
        try:
            dvalue = utils.float_to_decimal(float(value))
        except (TypeError, ValueError) as err:
            raise exception_class(err)
        if not dvalue.is_normal() and dvalue != ZERO:
            raise exception_class('Invalid Fixed precision number.')
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
    def __init__(self, default=None, attribute=None, relative=False, *args, **kwargs):
        super(Url, self).__init__(default=default, attribute=attribute,
                *args, **kwargs)
        self.relative = relative

    def _validated(self, value, exception_class):
        try:
            return validate.url(value, relative=self.relative)
        except ValueError as ve:
            raise exception_class(ve)

    def _format(self, value):
        if value:
            return self._validated(value, MarshallingError)

    def _deserialize(self, value):
        if value is None:
            return self.default
        return self._validated(value, DeserializationError)


class Email(Raw):
    """A validated email field.
    """

    def _validated(self, value, exception_class):
        try:
            return validate.email(value)
        except ValueError as ve:
            raise exception_class(ve)

    def _format(self, value):
        if value:
            return self._validated(value, MarshallingError)

    def _deserialize(self, value):
        return self._validated(value, DeserializationError)


def get_args(func):
    """Return a tuple of argument names for a function."""
    return inspect.getargspec(func).args


def _callable(obj):
    """Checks that an object is callable, else raises a ``MarshallingError``.
    """
    if not callable(obj):
        raise MarshallingError('Object {0!r} is not callable.'.format(obj))
    return obj


class Method(Raw):
    """A field that takes the value returned by a Serializer method.

    :param str method_name: The name of the Serializer method from which
        to retrieve the value. The method must take a single argument ``obj``
        (in addition to self) that is the object to be serialized.
    """
    _CHECK_REQUIRED = False

    def __init__(self, method_name, **kwargs):
        self.method_name = method_name
        super(Method, self).__init__(**kwargs)

    def _serialize(self, value, key, obj):
        try:
            method = _callable(getattr(self.parent, self.method_name, None))
            if len(get_args(method)) > 2:
                if self.parent.context is None:
                    msg = 'No context available for Method field {0!r}'.format(key)
                    raise MarshallingError(msg)
                return method(obj, self.parent.context)
            else:
                return method(obj)
        except AttributeError:
            pass


class Function(Raw):
    """A field that takes the value returned by a function.

    :param function func: A callable function from which to retrieve the value.
        The function must take a single argument ``obj`` which is the object
        to be serialized.
    """
    _CHECK_REQUIRED = False

    def __init__(self, func, **kwargs):
        super(Function, self).__init__(**kwargs)
        self.func = _callable(func)

    def _serialize(self, value, key, obj):
        try:
            if len(get_args(self.func)) > 1:
                if self.parent.context is None:
                    msg = 'No context available for Function field {0!r}'.format(key)
                    raise MarshallingError(msg)
                return self.func(obj, self.parent.context)
            else:
                return self.func(obj)
        except TypeError as te:  # Function is not callable
            raise MarshallingError(te)
        except AttributeError:  # the object is not expected to have the attribute
            pass


class Select(Raw):
    """A field that provides a set of values which an attribute must be
    contrained to.

    :param choices: A list of valid values.
    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        ``None``, assumes the attribute has the same name as the field.
    :param str error: Error message stored upon validation failure.

    :raises: MarshallingError if attribute's value is not one of the given choices.
    """
    def __init__(self, choices, default=None, attribute=None, error=None, **kwargs):
        self.choices = choices
        return super(Select, self).__init__(default, attribute, error, **kwargs)

    def _validated(self, value, exception_class, *args, **kwargs):
        if value not in self.choices:
            raise exception_class("{0!r} is not a valid choice for this field.".format(value))
        return value

    def _format(self, value):
        return self._validated(value, MarshallingError)

    def _deserialize(self, value):
        return self._validated(value, DeserializationError)

Enum = Select
