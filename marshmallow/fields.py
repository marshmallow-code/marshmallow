# -*- coding: utf-8 -*-
"""Field classes for formatting and validating the serialized object.
"""
from __future__ import absolute_import

from decimal import Decimal as MyDecimal, ROUND_HALF_EVEN
from functools import partial
import datetime as dt
import inspect
import warnings

from marshmallow import validate, utils, class_registry
from marshmallow.base import FieldABC, SerializerABC
from marshmallow.compat import (text_type, OrderedDict, iteritems, total_seconds,
                                basestring, binary_type)
from marshmallow.exceptions import (
    MarshallingError,
    UnmarshallingError,
    ForcedError,
)

__all__ = [
    'Marshaller',
    'UnMarshaller',
    'Field',
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


def _call_and_store(getter_func, data, field_name, field_obj, errors_dict,
               exception_class, strict=False):
    """Helper method for DRYing up logic in the :meth:`Marshaller.serialize` and
    :meth:`UnMarshaller.deserialize` methods. Call ``getter_func`` with ``data`` as its
    argument, and store any errors of type ``exception_class`` in ``error_dict``.

    :param callable getter_func: Function for getting the serialized/deserialized
        value from ``data``.
    :param data: The data passed to ``getter_func``.
    :param str field_name: Field name.
    :param FieldABC field_obj: Field object that performs the
        serialization/deserialization behavior.
    :param dict errors_dict: Dictionary to store errors on.
    :param type exception_class: Exception class that will be caught during
        serialization/deserialization. Errors of this type will be stored
        in ``errors_dict``.
    """
    try:
        value = getter_func(data)
    except exception_class as err:  # Store errors
        if strict:
            raise err
        # Warning: Mutation!
        errors_dict[field_name] = text_type(err)
        value = None
    except TypeError:
        # field declared as a class, not an instance
        if (isinstance(field_obj, type) and
                issubclass(field_obj, FieldABC)):
            msg = ('Field for "{0}" must be declared as a '
                            "Field instance, not a class. "
                            'Did you mean "fields.{1}()"?'
                            .format(field_name, field_obj.__name__))
            raise TypeError(msg)
        raise
    return value

class Marshaller(object):
    """Callable class responsible for serializing data and storing errors.

    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.
    """
    def __init__(self, prefix=''):
        self.prefix = prefix
        #: Dictionary of errors stored during serialization
        self.errors = {}

    def serialize(self, obj, fields_dict, many=False, strict=False):
        """Takes raw data (a dict, list, or other object) and a dict of
        fields to output and serializes the data based on those fields.

        :param obj: The actual object(s) from which the fields are taken from
        :param dict fields_dict: Mapping of field names to :class:`Field` objects.
        :param bool many: Set to ``True`` if ``data`` should be serialized as
            a collection.
        :param bool strict: If ``True``, raise errors if invalid data are passed in
            instead of failing silently and storing the errors.
        :return: An OrderedDict of the marshalled data

        .. versionchanged:: 1.0.0
            Renamed from ``marshal``.
        """
        if many and obj is not None:
            return [self.serialize(d, fields_dict, many=False) for d in obj]
        items = []
        for attr_name, field_obj in iteritems(fields_dict):
            key = self.prefix + attr_name
            value = _call_and_store(
                getter_func=partial(field_obj.serialize, attr_name),
                data=obj,
                field_name=key,
                field_obj=field_obj,
                errors_dict=self.errors,
                exception_class=MarshallingError,
                strict=strict
            )
            items.append((key, value))
        return OrderedDict(items)

    # Make an instance callable
    __call__ = serialize


class UnMarshaller(object):
    """Callable class responsible for deserializing data and storing errors.

    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.

    .. versionadded:: 1.0.0
    """
    def __init__(self, prefix=''):
        #: Dictionary of errors stored during deserialization
        self.errors = {}

    def deserialize(self, data, fields_dict, many=False, postprocess=None, strict=False):
        """Deserialize ``data`` based on the schema defined by ``fields_dict``.

        :param dict data: The data to deserialize.
        :param dict fields_dict: Mapping of field names to :class:`Field` objects.
        :param bool many: Set to ``True`` if ``data`` should be deserialized as
            a collection.
        :param callable postprocess: Post-processing function that is passed the
            deserialized dictionary.
        :param bool strict: If ``True``, raise errors if invalid data are passed in
            instead of failing silently and storing the errors.
        :return: An OrderedDict of the deserialized data.
        """
        if many and data is not None:
            return [self.deserialize(d, fields_dict, many=False) for d in data]
        items = []
        for attr_name, value in iteritems(data):
            field_obj = fields_dict[attr_name]
            key = fields_dict[attr_name].attribute or attr_name
            value = _call_and_store(
                getter_func=field_obj.deserialize,
                data=data[attr_name],
                field_name=key,
                field_obj=field_obj,
                errors_dict=self.errors,
                exception_class=UnmarshallingError,
                strict=strict
            )
            items.append((key, value))
        ret = OrderedDict(items)
        if postprocess:
            return postprocess(ret)
        return ret

    # Make an instance callable
    __call__ = deserialize


# Singleton marshaller function for use in this module
marshal = Marshaller()


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


class Field(FieldABC):
    """Basic field from which other fields should extend. It applies no
    formatting by default, and should only be used in cases where
    data does not need to be formatted before being serialized or deserialized.

    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        ``None``, assumes the attribute has the same name as the field.
    :param str error: Error message stored upon validation failure.
    :param callable validate: Validation function that takes the output as its
        only parameter and returns a boolean. If it returns False, a
        MarshallingError is raised.
    :param bool required: Make a field required. If a field is ``None``,
        raise a :exc:`MarshallingError`.
    """
    _CHECK_REQUIRED = True

    def __init__(self, default=None, attribute=None, error=None,
                validate=None, required=False):
        self.attribute = attribute
        self.default = default
        self.error = error
        self.validate = validate
        self.required = required

    def get_value(self, attr, obj):
        """Return the value for a given key from an object."""
        check_key = attr if self.attribute is None else self.attribute
        return _get_value(check_key, obj)

    def _call_with_validation(self, method, exception_class, *args, **kwargs):
        """Utility method to invoke ``method`` and validate the output. Call ``self.validate`` when
        appropriate, and raise ``exception_class`` if a validation error
        occurs.

        :param str method: Name of the method to call.
        :param Exception exception_class: Type of exception to raise when an error occurs.
        :param args: Positional arguments to pass to the method.
        :param kwargs: Keyword arguments to pass to the method.
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

    def serialize(self, attr, obj):
        """Pulls the value for the given key from the object, applies the
        field's formatting and returns the result.

        :param str key: The attibute or key to get.
        :param str obj: The object to pull the key from.
        :raise MarshallingError: In case of validation or formatting problem
        """
        value = self.get_value(attr, obj)
        if value is None and self._CHECK_REQUIRED:
            if hasattr(self, 'required') and self.required:
                raise MarshallingError('Missing data for required field.')
            elif hasattr(self, 'default'):
                return self._format(self.default)
            else:
                return None
        return self._call_with_validation('_serialize', MarshallingError,
                                          value, attr, obj)

    def deserialize(self, value):
        """Deserialize ``value``.

        :raise UnmarshallingError: If an invalid value is passed.
        """
        return self._call_with_validation('_deserialize', UnmarshallingError, value)

    # Methods for concrete classes to override.

    def _format(self, value):
        """Formats a field's value. No-op by default. Concrete :class:`Field` should
        override this and apply the appropriate formatting.

        :param value: The value to format
        :raise MarshallingError: In case of formatting or validation failure.

        Ex::

            class TitleCase(Field):
                def _format(self, value):
                    if not value:
                        return ''
                    return unicode(value).title()
        """
        return value

    def _serialize(self, value, attr, obj):
        """Serializes ``value`` to a basic Python datatype. Concrete :class:`Field` classes
        should implement this method.

        :param value: The value to be serialized.
        :param str key: The attribute or key on the object to be serialized.
        :param obj: The object the value was pulled from.
        :raise MarshallingError: In case of formatting or validation failure.
        """
        return self._format(value)

    def _deserialize(self, value):
        """Deserialize value. Concrete :class:`Field` classes should implement this method.

        :raise UnmarshallingError: In case of formatting or validation failure.
        """
        return value

class Raw(Field):
    """Field that applies no formatting or validation."""

class Nested(Field):
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
    :param kwargs: The same keyword arguments that :class:`Field` receives.
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

    def _serialize(self, nested_obj, attr, obj):
        if self.allow_null and nested_obj is None:
            return None
        self.serializer.many = self.many
        self.serializer.obj = nested_obj
        if not self.__updated_fields:
            self.__updated_fields = True
            self.serializer._update_fields(nested_obj)
        fields = self.__get_fields_to_marshal(self.serializer.fields)
        try:
            # We call the protected `_marshal` method instead of `serialize`
            # because we need to pass the this fields ``many`` attribute as
            # an argument, which ``serialize`` would not allow
            ret = self.serializer._marshal(nested_obj, fields, many=self.many)
        except TypeError as err:
            raise TypeError('Could not marshal nested object due to error:\n"{0}"\n'
                            'If the nested object is a collection, you need to set '
                            '"many=True".'.format(err))
        # Parent should get any errors stored after marshalling
        if self.serializer.errors:
            self.parent.errors[attr] = self.serializer.errors
        if isinstance(self.only, basestring):  # self.only is a field name
            if self.many:
                return _flatten(ret, key=self.only)
            else:
                return ret[self.only]
        return ret

    def _deserialize(self, value):
        return self.serializer.load(value)[0]


def _flatten(dictlist, key):
    """Flattens a list of dicts into just a list of values.
    ::

        >>> d = [{'id': 1, 'name': 'foo'}, {'id': 2, 'name': 'bar'}]
        >>> _flatten(d, 'id')
        [1, 2]
    """
    return [d[key] for d in dictlist]


class List(Field):
    """A list field.

    Example: ::

        numbers = fields.List(fields.Float)

    :param cls_or_instance: A field class or instance.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
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
            return [self.container.serialize(idx, value) for idx
                    in range(len(value))]
        if value is None:
            return self.default

        return [marshal(value, self.container.nested, strict=True)]

    # Deserialization is identical to _format behavior
    _deserialize = _format

def _ensure_text_type(val):
    if isinstance(val, binary_type):
        val = val.decode('utf-8')
    return text_type(val)

class String(Field):
    """A string field.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    def __init__(self, default='', attribute=None, *args, **kwargs):
        return super(String, self).__init__(default, attribute, *args, **kwargs)

    def _format(self, value):
        return _ensure_text_type(value)

    def _deserialize(self, value):
        if value is None:
            return self.default
        result = _ensure_text_type(value)
        return result


class UUID(String):
    """A UUID field."""
    pass


class Number(Field):
    """Base class for number fields.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    num_type = float

    def __init__(self, default=0.0, attribute=None, as_string=False, error=None, **kwargs):
        self.as_string = as_string
        super(Number, self).__init__(default=default, attribute=attribute,
            error=error, **kwargs)

    def _format_num(self, value):
        """Return the correct value for a number, given the passed in
        arguments to __init__.
        """
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
        return self._validated(value, UnmarshallingError)


class Integer(Number):
    """An integer field.

    :param bool as_string: If True, format the value as a string.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    num_type = int

    def __init__(self, default=0, attribute=None, as_string=False, error=None, **kwargs):
        self.as_string = as_string
        super(Number, self).__init__(default=default, attribute=attribute,
            error=error, **kwargs)

class Boolean(Field):
    """A boolean field.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

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
            raise UnmarshallingError(error)
        if value_str in self.falsy:
            return False
        elif self.truthy:
            if value_str in self.truthy:
                return True
            else:
                raise UnmarshallingError(
                    '{0!r} is not in {1} nor {2}'.format(
                        value_str, self.truthy, self.falsy
                    ))
        return True

class FormattedString(Field):
    def __init__(self, src_str):
        super(FormattedString, self).__init__()
        self.src_str = text_type(src_str)

    def _serialize(self, value, attr, obj):
        try:
            data = utils.to_marshallable_type(obj)
            return self.src_str.format(**data)
        except (TypeError, IndexError) as error:
            raise MarshallingError(error)


class Float(Number):
    """
    A double as IEEE-754 double precision string.

    :param bool as_string: If True, format the value as a string.
    :param kwargs: The same keyword arguments that :class:`Number` receives.
    """

    num_type = float


class Arbitrary(Number):
    """A floating point number with an arbitrary precision,
    formatted as as string.
    ex: 634271127864378216478362784632784678324.23432

    :param kwargs: The same keyword arguments that :class:`Number` receives.
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
        return self._validated(value, UnmarshallingError)


DATEFORMAT_SERIALIZATION_FUNCS = {
    'iso': utils.isoformat,
    'iso8601': utils.isoformat,

    'rfc': utils.rfcformat,
    'rfc822': utils.rfcformat,
}

DATEFORMAT_DESERIALIZATION_FUNCS = {
    'iso': utils.from_iso,
    'iso8601': utils.from_iso,

    'rfc': utils.from_rfc,
    'rfc822': utils.from_rfc,
}

class DateTime(Field):
    """A formatted datetime string in UTC.
        ex. ``"Sun, 10 Nov 2013 07:23:45 -0000"``

    :param str format: Either ``"rfc"`` (for RFC822), ``"iso"`` (for ISO8601),
        or a date format string. If ``None``, defaults to "rfc".
    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        ``None``, assumes the attribute has the same name as the field.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    """
    DEFAULT_FORMAT = 'iso'

    localtime = False

    def __init__(self, format=None, default=None, attribute=None, **kwargs):
        super(DateTime, self).__init__(default=default, attribute=attribute, **kwargs)
        # Allow this to be None. It may be set later in the ``format`` method
        # This allows a Serializer to dynamically set the dateformat, e.g.
        # from a Meta option
        self.dateformat = format

    def _format(self, value):
        if value:
            self.dateformat = self.dateformat or self.DEFAULT_FORMAT
            format_func = DATEFORMAT_SERIALIZATION_FUNCS.get(self.dateformat, None)
            if format_func:
                return format_func(value, localtime=self.localtime)
            else:
                return value.strftime(self.dateformat)

    def _deserialize(self, value):
        err = UnmarshallingError(
            'Cannot deserialize {0!r} to a datetime'.format(value)
        )
        func = DATEFORMAT_DESERIALIZATION_FUNCS.get(self.dateformat, None)
        if func:
            try:
                return func(value)
            except TypeError:
                raise err
        elif utils.dateutil_available:
            try:
                return utils.from_datestring(value)
            except TypeError:
                raise err
        else:
            warnings.warn('It is recommended that you install python-dateutil '
                          'for improved datetime deserialization.')
            raise err


class LocalDateTime(DateTime):
    """A formatted datetime string in localized time, relative to UTC.

        ex. ``"Sun, 10 Nov 2013 08:23:45 -0600"``

    Takes the same arguments as :class:`DateTime <marshmallow.fields.DateTime>`.
    """
    localtime = True


class Time(Field):
    """ISO8601-formatted time string.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    def _format(self, value):
        try:
            ret = value.isoformat()
        except AttributeError:
            raise MarshallingError('{0} cannot be formatted as a time.'
                                    .format(repr(value)))
        if value.microsecond:
            return ret[:12]
        return ret

    def _deserialize(self, value):
        """Deserialize an ISO8601-formatted time to a :class:`datetime.time` object."""
        try:
            return utils.from_iso_time(value)
        except TypeError:
            raise UnmarshallingError(
                'Could not deserialize {0!r} to a time object.'.format(value)
            )

class Date(Field):
    """ISO8601-formatted date string.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    def _format(self, value):
        try:
            return value.isoformat()
        except AttributeError:
            raise MarshallingError('{0} cannot be formatted as a date.'
                                    .format(repr(value)))
        return value

    def _deserialize(self, value):
        """Deserialize an ISO8601-formatted date string to a
        :class:`datetime.date` object.
        """
        try:
            return utils.from_iso_date(value)
        except TypeError:
            raise UnmarshallingError(
                'Could not deserialize {0!r} to a date object.'.format(value)
            )


class TimeDelta(Field):
    """Formats time delta objects, returning the total number of seconds
    as a float.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    def _format(self, value):
        try:
            return total_seconds(value)
        except AttributeError:
            raise MarshallingError('{0} cannot be formatted as a timedelta.'
                                    .format(repr(value)))
        return value

    def _deserialize(self, value):
        """Deserialize a value in seconds to a :class:`datetime.timedelta`
        object.
        """
        return dt.timedelta(seconds=float(value))


ZERO = MyDecimal()


class Fixed(Number):
    """A fixed-precision number as a string.

    :param kwargs: The same keyword arguments that :class:`Number` receives.
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
        return self._validated(value, UnmarshallingError)

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
    """A Price field with fixed precision.

    :param kwargs: The same keyword arguments that :class:`Fixed` receives.
    """
    def __init__(self, decimals=2, **kwargs):
        super(Price, self).__init__(decimals=decimals, **kwargs)


class Url(Field):
    """A validated URL field.

    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        ``None``, assumes the attribute has the same name as the field.
    :param bool relative: Allow relative URLs.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
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
        return self._validated(value, UnmarshallingError)


class Email(Field):
    """A validated email field.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
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
        return self._validated(value, UnmarshallingError)


def _get_args(func):
    """Return a tuple of argument names for a function."""
    return inspect.getargspec(func).args


def _callable(obj):
    """Check that an object is callable, else raise a :exc:`ValueError`.
    """
    if not callable(obj):
        raise ValueError('Object {0!r} is not callable.'.format(obj))
    return obj


class Method(Field):
    """A field that takes the value returned by a Serializer method.

    :param str method_name: The name of the Serializer method from which
        to retrieve the value. The method must take an argument ``obj``
        (in addition to self) that is the object to be serialized. The method
        can also take a ``context`` argument which is a dictionary context
        passed to a Serializer.
    :param str deserialize: Optional name of the Serializer method for deserializing
        a value The method must take a single argument ``value``, which is the
        value to deserialize.
    """
    _CHECK_REQUIRED = False

    def __init__(self, method_name, deserialize=None, **kwargs):
        self.method_name = method_name
        if deserialize:
            self.deserialize_method_name = deserialize
        else:
            self.deserialize_method_name = None
        super(Method, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        try:
            method = _callable(getattr(self.parent, self.method_name, None))
            if len(_get_args(method)) > 2:
                if self.parent.context is None:
                    msg = 'No context available for Method field {0!r}'.format(key)
                    raise MarshallingError(msg)
                return method(obj, self.parent.context)
            else:
                return method(obj)
        except AttributeError:
            pass

    def _deserialize(self, value):
        if self.deserialize_method_name:
            try:
                method = _callable(getattr(self.parent, self.deserialize_method_name, None))
                return method(value)
            except AttributeError:
                pass
        return value


class Function(Field):
    """A field that takes the value returned by a function.

    :param callable func: A callable from which to retrieve the value.
        The function must take a single argument ``obj`` which is the object
        to be serialized. It can also optionally take a ``context`` argument,
        which is a dictionary of context variables passed to the serializer.
    :param callable deserialize: Deserialization function that takes the value
        to be deserialized as its only argument.
    """
    _CHECK_REQUIRED = False

    def __init__(self, func, deserialize=None, **kwargs):
        super(Function, self).__init__(**kwargs)
        self.func = _callable(func)
        if deserialize:
            self.deserialize_func = _callable(deserialize)
        else:
            self.deserialize_func = None

    def _serialize(self, value, attr, obj):
        try:
            if len(_get_args(self.func)) > 1:
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

    def _deserialize(self, value):
        if self.deserialize_func:
            return self.deserialize_func(value)
        return value


class Select(Field):
    """A field that provides a set of values which an attribute must be
    contrained to.

    :param choices: A list of valid values.
    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        ``None``, assumes the attribute has the same name as the field.
    :param str error: Error message stored upon validation failure.
    :param kwargs: The same keyword arguments that :class:`Fixed` receives.

    :raise: MarshallingError if attribute's value is not one of the given choices.
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
        return self._validated(value, UnmarshallingError)

Enum = Select
