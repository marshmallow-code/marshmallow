# -*- coding: utf-8 -*-
"""Field classes for various types of data."""

from __future__ import absolute_import, unicode_literals

import datetime as dt
import uuid
import warnings
import decimal
from operator import attrgetter

from marshmallow import validate, utils, class_registry
from marshmallow.base import FieldABC, SchemaABC
from marshmallow.utils import missing as missing_
from marshmallow.compat import text_type, basestring
from marshmallow.exceptions import ValidationError

__all__ = [
    'Field',
    'Raw',
    'Nested',
    'List',
    'String',
    'UUID',
    'Number',
    'Integer',
    'Decimal',
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
    'Price',
    'Url',
    'URL',
    'Email',
    'Method',
    'Function',
    'Select',
    'QuerySelect',
    'QuerySelectList',
    'Enum',
    'Str',
    'Bool',
    'Int',
]


class Field(FieldABC):
    """Basic field from which other fields should extend. It applies no
    formatting by default, and should only be used in cases where
    data does not need to be formatted before being serialized or deserialized.

    :param default: Default serialization value for the field if the attribute is
        `None`. May be a value or a callable.
    :param str attribute: The name of the attribute to get the value from. If
        `None`, assumes the attribute has the same name as the field.
    :param str load_from: Additional key to look for when deserializing. Will only
        be checked if the field's name is not found on the input dictionary.
    :param str error: Error message stored upon validation failure.
    :param callable validate: Validator or collection of validators that are called
        during deserialization. Validator takes a field's input value as
        its only parameter and returns a boolean.
        If it returns `False`, an :exc:`ValidationError` is raised.
    :param required: Raise an :exc:`ValidationError` if the field value
        is not supplied during deserialization. If not a `bool`(e.g. a `str`),
        the provided value will be used as the message of the
        :exc:`ValidationError` instead of the default message.
    :param allow_none: Set to `True` if `None` should be considered a valid value during
        validation/deserialization. If not a `bool` (e.g. a `str`), the provided
        value will be used as the message of the :exc:`ValidationError` instead
        of the default message.
    :param bool load_only: If `True` skip this field during serialization, otherwise
        its value will be present in the serialized data.
    :param bool dump_only: If `True` skip this field during deserialization, otherwise
        its value will be present in the deserialized object. In the context of an
        HTTP API, this effectively marks the field as "read-only".
    :param missing: Default deserialization value for the field if the field is not
        found in the input data. May be a value or a callable.
    :param metadata: Extra arguments to be stored as metadata.

    .. versionchanged:: 1.0.0
        Deprecated `error` parameter. Raise a :exc:`marshmallow.ValidationError` instead.

    .. versionchanged:: 2.0.0
        Added `allow_none` parameter, which makes validation/deserialization of `None`
        consistent across fields.

    .. versionchanged:: 2.0.0
        Added `load_only` and `dump_only` parameters, which allow field skipping
        during the (de)serialization process.

    .. versionchanged:: 2.0.0
        Added `missing` parameter, which indicates the value for a field if the field
        is not found during deserialization.
    """
    # Some fields, such as Method fields and Function fields, are not expected
    #  to exists as attributes on the objects to serialize. Set this to False
    #  for those fields
    _CHECK_ATTRIBUTE = True
    _creation_index = 0  # Used for sorting
    #: Values that are skipped by `Marshaller` if ``skip_missing=True``
    SKIPPABLE_VALUES = (None, )

    def __init__(self, default=missing_, attribute=None, load_from=None, error=None,
                 validate=None, required=False, allow_none=False, load_only=False,
                 dump_only=False, missing=missing_, **metadata):
        self.default = default
        self.attribute = attribute
        self.load_from = load_from  # this flag is used by Unmarshaller
        if error:
            warnings.warn('The error parameter is deprecated. Raise a '
                          'marshmallow.ValidationError in your validators '
                          'instead.', category=DeprecationWarning)
        self.error = error
        self.validate = validate
        if utils.is_iterable_but_not_string(validate):
            if not utils.is_generator(validate):
                self.validators = validate
            else:
                self.validators = list(validate)
        elif callable(validate):
            self.validators = [validate]
        elif validate is None:
            self.validators = []
        else:
            raise ValueError("The 'validate' parameter must be a callable "
                             "or a collection of callables.")

        self.required = required
        self.allow_none = allow_none
        self.load_only = load_only
        self.dump_only = dump_only
        self.missing = missing
        self.metadata = metadata
        self._creation_index = Field._creation_index
        Field._creation_index += 1
        self.parent = FieldABC.parent

    def __repr__(self):
        return ('<fields.{ClassName}(default={self.default!r}, '
                'attribute={self.attribute!r}, error={self.error!r}, '
                'validate={self.validate}, required={self.required}, '
                'load_only={self.load_only}, dump_only={self.dump_only}, '
                'missing={self.missing}, allow_none={self.allow_none})>'
                .format(ClassName=self.__class__.__name__, self=self))

    def get_value(self, attr, obj, accessor=None):
        """Return the value for a given key from an object."""
        # NOTE: Use getattr instead of direct attribute access here so that
        # subclasses aren't required to define `attribute` member
        attribute = getattr(self, 'attribute', None)
        accessor_func = accessor or utils.get_value
        check_key = attr if attribute is None else attribute
        return accessor_func(check_key, obj)

    def _validate(self, value):
        """Perform validation on ``value``. Raise a :exc:`ValidationError` if validation
        does not succeed.
        """
        errors = []
        for validator in self.validators:
            func_name = utils.get_func_name(validator)
            msg = 'Validator {0}({1}) is False'.format(
                func_name, value
            )
            try:
                if validator(value) is False:
                    raise ValidationError(getattr(self, 'error', None) or msg)
            except ValidationError as err:
                if isinstance(err.messages, dict):
                    errors.append(err.messages)
                else:
                    errors.extend(err.messages)
        if errors:
            raise ValidationError(errors)

    def _validate_missing(self, value):
        """Validate missing values. Raise a :exc:`ValidationError` if
        `value` should be considered missing.
        """
        if value is missing_:
            if hasattr(self, 'required') and self.required:
                default_message = 'Missing data for required field.'
                message = (default_message if isinstance(self.required, bool) else
                            self.required)
                raise ValidationError(message)
        if value is None:
            if hasattr(self, 'allow_none') and self.allow_none is not True:
                default_message = 'Field may not be null.'
                message = (default_message if isinstance(self.allow_none, bool) else
                            self.allow_none)
                raise ValidationError(message)

    def serialize(self, attr, obj, accessor=None):
        """Pulls the value for the given key from the object, applies the
        field's formatting and returns the result.

        :param str attr: The attibute or key to get from the object.
        :param str obj: The object to pull the key from.
        :param callable accessor: Function used to pull values from ``obj``.
        :raise ValidationError: In case of formatting problem
        """
        value = self.get_value(attr, obj, accessor=accessor)
        if value is missing_ and self._CHECK_ATTRIBUTE:
            if hasattr(self, 'default'):
                if callable(self.default):
                    return self.default()
                else:
                    return self.default
        return self._serialize(value, attr, obj)

    def deserialize(self, value):
        """Deserialize ``value``.

        :raise ValidationError: If an invalid value is passed or if a required value
            is missing.
        """
        # Validate required fields, deserialize, then validate
        # deserialized value
        self._validate_missing(value)
        if getattr(self, 'allow_none', False) is True and value is None:
            return None
        output = self._deserialize(value)
        self._validate(output)
        return output

    # Methods for concrete classes to override.

    def _serialize(self, value, attr, obj):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        Example: ::

            class TitleCase(Field):
                def _serialize(self, value, attr, obj):
                    if not value:
                        return ''
                    return unicode(value).title()

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :raise ValidationError: In case of formatting or validation failure.
        """
        return value

    def _deserialize(self, value):
        """Deserialize value. Concrete :class:`Field` classes should implement this method.

        :raise ValidationError: In case of formatting or validation failure.
        """
        return value

    @property
    def context(self):
        """The context dictionary for the parent :class:`Schema`."""
        return self.parent.context

class Raw(Field):
    """Field that applies no formatting or validation."""
    pass

class Nested(Field):
    """Allows you to nest a :class:`Schema <marshmallow.Schema>`
    inside a field.

    Examples: ::

        user = fields.Nested(UserSchema)
        user2 = fields.Nested('UserSchema')  # Equivalent to above
        collaborators = fields.Nested(UserSchema, many=True, only='id')
        parent = fields.Nested('self')

    :param Schema nested: The Schema class or class name (string)
        to nest, or ``"self"`` to nest the :class:`Schema` within itself.
    :param default: Default value to if attribute is missing or None
    :param tuple exclude: A list or tuple of fields to exclude.
    :param only: A tuple or string of the field(s) to marshal. If `None`, all fields
        will be marshalled. If a field name (string) is given, only a single
        value will be returned as output instead of a dictionary.
        This parameter takes precedence over ``exclude``.
    :param bool allow_null: Whether to return `None` instead of a dictionary
        with null keys, if a nested dictionary has all-null keys.
    :param bool many: Whether the field is a collection of objects.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    def __init__(self, nested, default=missing_, exclude=tuple(), only=None, allow_null=True,
                many=False, **kwargs):
        self.nested = nested
        self.allow_null = allow_null
        self.only = only
        self.exclude = exclude
        self.many = many
        self.__schema = None  # Cached Schema instance
        self.__updated_fields = False
        super(Nested, self).__init__(default=default, **kwargs)

    @property
    def schema(self):
        """The nested Schema object.

        .. versionchanged:: 1.0.0
            Renamed from `serializer` to `schema`
        """
        # Ensure that only parameter is a tuple
        if isinstance(self.only, basestring):
            only = (self.only, )
        else:
            only = self.only
        if not self.__schema:
            if isinstance(self.nested, SchemaABC):
                self.__schema = self.nested
            elif isinstance(self.nested, type) and \
                    issubclass(self.nested, SchemaABC):
                self.__schema = self.nested(many=self.many,
                        only=only, exclude=self.exclude)
            elif isinstance(self.nested, basestring):
                if self.nested == 'self':
                    parent_class = self.parent.__class__
                    self.__schema = parent_class(many=self.many, only=only,
                            exclude=self.exclude)
                else:
                    schema_class = class_registry.get_class(self.nested)
                    self.__schema = schema_class(many=self.many,
                            only=only, exclude=self.exclude)
            else:
                raise ValueError('Nested fields must be passed a '
                                 'Schema, not {0}.'.format(self.nested.__class__))
        self.__schema.ordered = getattr(self.parent, 'ordered', False)
        # Inherit context from parent
        self.__schema.context.update(getattr(self.parent, 'context', {}))
        return self.__schema

    def _serialize(self, nested_obj, attr, obj):
        # Load up the schema first. This allows a RegistryError to be raised
        # if an invalid schema name was passed
        schema = self.schema
        if nested_obj is None:
            if self.allow_null:
                return None
        if not self.__updated_fields:
            schema._update_fields(obj=nested_obj, many=self.many)
            self.__updated_fields = True
        try:
            ret = schema.dump(nested_obj, many=self.many,
                    update_fields=not self.__updated_fields).data
        except TypeError as err:
            raise TypeError('Could not marshal nested object due to error:\n"{0}"\n'
                            'If the nested object is a collection, you need to set '
                            '"many=True".'.format(err))
        if isinstance(self.only, basestring):  # self.only is a field name
            if self.many:
                return utils.pluck(ret, key=self.only)
            else:
                return ret[self.only]
        return ret

    def _deserialize(self, value):
        data, errors = self.schema.load(value)
        if errors:
            raise ValidationError(errors)
        return data


class List(Field):
    """A list field, composed with another `Field` class or
    instance.

    Example: ::

        numbers = fields.List(fields.Float)

    :param Field cls_or_instance: A field class or instance.
    :param bool default: Default value for serialization.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionchanged:: 2.0.0
        The ``allow_none`` parameter now applies to deserialization and
        has the same semantics as the other fields.
    """
    # Values that are skipped by `Marshaller` if ``skip_missing=True``
    SKIPPABLE_VALUES = (None, [], tuple())

    def __init__(self, cls_or_instance, **kwargs):
        super(List, self).__init__(**kwargs)
        if isinstance(cls_or_instance, type):
            if not issubclass(cls_or_instance, FieldABC):
                raise ValueError('The type of the list elements '
                                           'must be a subclass of '
                                           'marshmallow.base.FieldABC')
            self.container = cls_or_instance()
        else:
            if not isinstance(cls_or_instance, FieldABC):
                raise ValueError('The instances of the list '
                                           'elements must be of type '
                                           'marshmallow.base.FieldABC')
            self.container = cls_or_instance

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        if utils.is_collection(value):
            return [self.container._serialize(each, attr, obj) for each in value]
        return [self.container.serialize(attr, obj)]

    def _deserialize(self, value):
        if utils.is_indexable_but_not_string(value) and not isinstance(value, dict):
            # Convert all instances in typed list to container type
            return [self.container.deserialize(each) for each in value]
        if value is None:
            return []
        return [self.container.deserialize(value)]


class String(Field):
    """A string field.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """
    # Values that are skipped by `Marshaller` if ``skip_missing=True``
    SKIPPABLE_VALUES = (None, '')

    def __init__(self, *args, **kwargs):
        return super(String, self).__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        return utils.ensure_text_type(value)

    def _deserialize(self, value):
        result = utils.ensure_text_type(value)
        return result


class UUID(String):
    """A UUID field."""

    def _deserialize(self, value):
        msg = 'Could not deserialize {0!r} to a UUID object.'.format(value)
        err = ValidationError(getattr(self, 'error', None) or msg)
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError):
            raise err


class Number(Field):
    """Base class for number fields.

    :param bool as_string: If True, format the serialized value as a string.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    num_type = float

    def __init__(self, as_string=False, **kwargs):
        self.as_string = as_string
        super(Number, self).__init__(**kwargs)

    def _format_num(self, value):
        """Return the number value for value, given this field's `num_type`."""
        if value is None:
            return None
        return self.num_type(value)

    def _validated(self, value):
        """Format the value or raise ``exception_class`` if an error occurs."""
        try:
            return self._format_num(value)
        except (TypeError, ValueError, decimal.InvalidOperation) as err:
            raise ValidationError(getattr(self, 'error', None) or text_type(err))

    def serialize(self, attr, obj, accessor=None):
        """Pulls the value for the given key from the object and returns the
        serialized number representation. Return a string if `self.as_string=True`,
        othewise return this field's `num_type`. Receives the same `args` and `kwargs`
        as `Field`.
        """
        ret = Field.serialize(self, attr, obj, accessor=accessor)
        return str(ret) if (self.as_string and ret is not None) else ret

    def _serialize(self, value, attr, obj):
        return self._validated(value)

    def _deserialize(self, value):
        return self._validated(value)


class Integer(Number):
    """An integer field.

    :param kwargs: The same keyword arguments that :class:`Number` receives.
    """

    num_type = int


class Decimal(Number):
    """A field that (de)serializes to the Python ``decimal.Decimal`` type.
    It's safe to use when dealing with money values, percentages, ratios
    or other numbers where precision is critical.

    .. warning::

        This field serializes to a `decimal.Decimal` object by default. If you need
        to render your data as JSON, keep in mind that the `json` module from the
        standard library does not encode `decimal.Decimal`. Therefore, you must use
        a JSON library that can handle decimals, such as `simplejson`, or serialize
        to a string by passing ``as_string=True``.

    :param int places: How many decimal places to quantize the value. If `None`, does
        not quantize the value.
    :param rounding: How to round the value during quantize, for example
        `decimal.ROUND_UP`. If None, uses the rounding value from
        the current thread's context.
    :param default: The value this field defaults to. If not specified is the
        `decimal.Decimal` zero.
    :param bool as_string: If True, serialize to a string instead of a Python
        `decimal.Decimal` type.
    :param kwargs: The same keyword arguments that :class:`Number` receives.

    .. versionadded:: 1.2.0
    """

    num_type = decimal.Decimal

    def __init__(self, places=None, rounding=None, as_string=False, **kwargs):
        self.places = decimal.Decimal((0, (1,), -places)) if places is not None else None
        self.rounding = rounding
        super(Decimal, self).__init__(as_string=as_string, **kwargs)

    def _format_num(self, value):
        if value is None:
            return None
        num = decimal.Decimal(value)
        if self.places is not None:
            num = num.quantize(self.places, rounding=self.rounding)
        return num


class Boolean(Field):
    """A boolean field.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    #: Values that will deserialize to `True`. If an empty set, any non-falsy
    #  value will deserialize to `True`.
    truthy = set()
    #: Values that will deserialize to `False`.
    falsy = set(['False', 'false', '0', 'null', 'None'])

    def _serialize(self, value, attr, obj):
        return bool(value)

    def _deserialize(self, value):
        if not value:
            return False
        try:
            value_str = text_type(value)
        except TypeError as error:
            raise ValidationError(text_type(error))
        if value_str in self.falsy:
            return False
        elif self.truthy:
            if value_str in self.truthy:
                return True
            else:
                raise ValidationError(
                    '{0!r} is not in {1} nor {2}'.format(
                        value_str, self.truthy, self.falsy
                    ))
        return True

class FormattedString(Field):
    """Interpolate other values from the object into this field. The syntax for
    the source string is the same as the string `str.format` method
    from the python stdlib.
    ::

        class UserSchema(Schema):
            name = fields.String()
            greeting = fields.FormattedString('Hello {name}')

        ser = UserSchema()
        res = ser.dump(user)
        res.data  # => {'name': 'Monty', 'greeting': 'Hello Monty'}
    """
    # Values that are skipped by `Marshaller` if ``skip_missing=True``
    SKIPPABLE_VALUES = (None, '')

    def __init__(self, src_str, *args, **kwargs):
        Field.__init__(self, *args, **kwargs)
        self.src_str = text_type(src_str)

    def _serialize(self, value, attr, obj):
        try:
            data = utils.to_marshallable_type(obj)
            return self.src_str.format(**data)
        except (TypeError, IndexError) as error:
            raise ValidationError(getattr(self, 'error', None) or error)


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

    :param args: The same positional arguments that :class:`Number` receives.
    :param kwargs: The same keyword arguments that :class:`Number` receives.

    .. deprecated:: 1.2.0
        Use `Decimal` instead.
    """
    # No as_string param
    def __init__(self, *args, **kwargs):
        warnings.warn(
            'The Arbitrary field is deprecated. Use the Decimal field instead.',
            category=DeprecationWarning
        )
        super(Arbitrary, self).__init__(*args, **kwargs)

    def _validated(self, value):
        """Format ``value`` or raise ``exception_class`` if an error occurs."""
        try:
            if value is None:
                return self.default
            return text_type(utils.float_to_decimal(float(value)))
        except ValueError as ve:
            raise ValidationError(text_type(ve))

    def _serialize(self, value, attr, obj):
        return self._validated(value)

    def _deserialize(self, value):
        return self._validated(value)


class DateTime(Field):
    """A formatted datetime string in UTC.

    Example: ``'2014-12-22T03:12:58.019077+00:00'``

    :param str format: Either ``"rfc"`` (for RFC822), ``"iso"`` (for ISO8601),
        or a date format string. If `None`, defaults to "iso".
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    """

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

    DEFAULT_FORMAT = 'iso'

    localtime = False

    def __init__(self, format=None, **kwargs):
        super(DateTime, self).__init__(**kwargs)
        # Allow this to be None. It may be set later in the ``_serialize``
        # or ``_desrialize`` methods This allows a Schema to dynamically set the
        # dateformat, e.g. from a Meta option
        self.dateformat = format

    def _serialize(self, value, attr, obj):
        if value:
            self.dateformat = self.dateformat or self.DEFAULT_FORMAT
            format_func = self.DATEFORMAT_SERIALIZATION_FUNCS.get(self.dateformat, None)
            if format_func:
                try:
                    return format_func(value, localtime=self.localtime)
                except (AttributeError, ValueError) as err:
                    raise ValidationError(getattr(self, 'error', None) or text_type(err))
            else:
                return value.strftime(self.dateformat)

    def _deserialize(self, value):
        msg = 'Could not deserialize {0!r} to a datetime object.'.format(value)
        err = ValidationError(getattr(self, 'error', None) or msg)
        if not value:  # Falsy values, e.g. '', None, [] are not valid
            raise err
        self.dateformat = self.dateformat or self.DEFAULT_FORMAT
        func = self.DATEFORMAT_DESERIALIZATION_FUNCS.get(self.dateformat)
        if func:
            try:
                return func(value)
            except (TypeError, AttributeError, ValueError):
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

    def _serialize(self, value, attr, obj):
        try:
            ret = value.isoformat()
        except AttributeError:
            msg = '{0!r} cannot be formatted as a time.'.format(value)
            raise ValidationError(getattr(self, 'error', None) or msg)
        if value.microsecond:
            return ret[:12]
        return ret

    def _deserialize(self, value):
        """Deserialize an ISO8601-formatted time to a :class:`datetime.time` object."""
        msg = 'Could not deserialize {0!r} to a time object.'.format(value)
        err = ValidationError(getattr(self, 'error', None) or msg)
        if not value:   # falsy values are invalid
            raise err
        try:
            return utils.from_iso_time(value)
        except (AttributeError, TypeError, ValueError):
            raise err

class Date(Field):
    """ISO8601-formatted date string.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    def _serialize(self, value, attr, obj):
        try:
            return value.isoformat()
        except AttributeError:
            msg = '{0} cannot be formatted as a date.'.format(repr(value))
            raise ValidationError(getattr(self, 'error', None) or msg)
        return value

    def _deserialize(self, value):
        """Deserialize an ISO8601-formatted date string to a
        :class:`datetime.date` object.
        """
        msg = 'Could not deserialize {0!r} to a date object.'.format(value)
        err = ValidationError(getattr(self, 'error', None) or msg)
        if not value:  # falsy values are invalid
            raise err
        try:
            return utils.from_iso_date(value)
        except (AttributeError, TypeError, ValueError):
            raise err


class TimeDelta(Field):
    """A field that (de)serializes a :class:`datetime.timedelta` object to an
    integer and vice versa. The integer can represent the number of days,
    seconds or microseconds.

    :param str precision: Influences how the integer is interpreted during
        (de)serialization. Must be 'days', 'seconds' or 'microseconds'.
    :param str error: Error message stored upon validation failure.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionchanged:: 2.0.0
        Always serializes to an integer value to avoid rounding errors.
        Add `precision` parameter.
    """

    DAYS = 'days'
    SECONDS = 'seconds'
    MICROSECONDS = 'microseconds'

    def __init__(self, precision='seconds', error=None, **kwargs):
        precision = precision.lower()
        units = (self.DAYS, self.SECONDS, self.MICROSECONDS)

        if precision not in units:
            msg = 'The precision must be "{0}", "{1}" or "{2}".'.format(*units)
            raise ValueError(msg)

        self.precision = precision
        super(TimeDelta, self).__init__(error=error, **kwargs)

    def _serialize(self, value, attr, obj):
        try:
            days = value.days
            if self.precision == self.DAYS:
                return days
            else:
                seconds = days * 86400 + value.seconds
                if self.precision == self.SECONDS:
                    return seconds
                else:  # microseconds
                    return seconds * 10**6 + value.microseconds  # flake8: noqa
        except AttributeError:
            msg = '{0!r} cannot be formatted as a timedelta.'.format(value)
            raise ValidationError(getattr(self, 'error', None) or msg)

    def _deserialize(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            msg = '{0!r} cannot be interpreted as a valid period of time.'.format(value)
            raise ValidationError(getattr(self, 'error', None) or msg)

        kwargs = {self.precision: value}

        try:
            return dt.timedelta(**kwargs)
        except OverflowError:
            msg = '{0!r} cannot be interpreted as a valid period of time.'.format(value)
            raise ValidationError(getattr(self, 'error', None) or msg)


class Fixed(Number):
    """A fixed-precision number as a string.

    :param kwargs: The same keyword arguments that :class:`Number` receives.

    .. deprecated:: 1.2.0
        Use `Decimal` instead.
    """

    def __init__(self, decimals=5, *args, **kwargs):
        warnings.warn(
            'The Fixed field is deprecated. Use the Decimal field instead.',
            category=DeprecationWarning
        )
        super(Fixed, self).__init__(*args, **kwargs)
        self.precision = decimal.Decimal('0.' + '0' * (decimals - 1) + '1')

    def _validated(self, value):
        if value is None:
            return None
        try:
            dvalue = utils.float_to_decimal(float(value))
        except (TypeError, ValueError) as err:
            raise ValidationError(getattr(self, 'error', None) or text_type(err))
        if not dvalue.is_normal() and dvalue != utils.ZERO_DECIMAL:
            raise ValidationError(
                getattr(self, 'error', None) or 'Invalid Fixed precision number.'
            )
        return utils.decimal_to_fixed(dvalue, self.precision)


class Price(Fixed):
    """A Price field with fixed precision.

    :param kwargs: The same keyword arguments that :class:`Fixed` receives.

    .. deprecated:: 1.2.0
        Use `Decimal` instead.
    """
    def __init__(self, decimals=2, **kwargs):
        warnings.warn(
            'The Price field is deprecated. Use the Decimal field for dealing with '
            'money values.',
            category=DeprecationWarning
        )
        super(Price, self).__init__(decimals=decimals, **kwargs)

class ValidatedField(Field):
    """A field that validates input on serialization."""

    def _validated(self, value):
        raise NotImplementedError('Must implement _validate method')

    def _serialize(self, value, *args, **kwargs):
        ret = super(ValidatedField, self)._serialize(value, *args, **kwargs)
        return self._validated(ret)

class Url(ValidatedField, String):
    """A validated URL field. Validation occurs during both serialization and
    deserialization.

    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        `None`, assumes the attribute has the same name as the field.
    :param bool relative: Allow relative URLs.
    :param kwargs: The same keyword arguments that :class:`String` receives.
    """

    def __init__(self, relative=False, **kwargs):
        String.__init__(self, **kwargs)
        self.relative = relative
        # Insert validation into self.validators so that multiple errors can be
        # stored.
        self.validators.insert(0, validate.URL(
            relative=self.relative,
            error=getattr(self, 'error')
        ))

    def _validated(self, value):
        if value is None:
            return None
        return validate.URL(
            relative=self.relative,
            error=getattr(self, 'error')
        )(value)


class Email(ValidatedField, String):
    """A validated email field. Validation occurs during both serialization and
    deserialization.

    :param args: The same positional arguments that :class:`String` receives.
    :param kwargs: The same keyword arguments that :class:`String` receives.
    """
    def __init__(self, *args, **kwargs):
        String.__init__(self, *args, **kwargs)
        # Insert validation into self.validators so that multiple errors can be
        # stored.
        self.validators.insert(0, validate.Email(error=getattr(self, 'error')))

    def _validated(self, value):
        return validate.Email(
            error=getattr(self, 'error')
        )(value)


class Method(Field):
    """A field that takes the value returned by a `Schema` method.

    :param str method_name: The name of the Schema method from which
        to retrieve the value. The method must take an argument ``obj``
        (in addition to self) that is the object to be serialized.
    :param str deserialize: Optional name of the Schema method for deserializing
        a value The method must take a single argument ``value``, which is the
        value to deserialize.

    .. versionchanged:: 2.0.0
        Deprecated ``context`` parameter on methods. Use ``self.context`` instead.
    """
    _CHECK_ATTRIBUTE = False

    def __init__(self, method_name, deserialize=None, **kwargs):
        self.method_name = method_name
        if deserialize:
            self.deserialize_method_name = deserialize
        else:
            self.deserialize_method_name = None
        super(Method, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        method = utils.callable_or_raise(getattr(self.parent, self.method_name, None))
        if len(utils.get_func_args(method)) > 2:
            warnings.warn(
                'The context parameter of Method fields is deprecated. Use self.context '
                'in the method instead.', category=DeprecationWarning
            )
            if self.parent.context is None:
                msg = 'No context available for Method field {0!r}'.format(attr)
                raise ValidationError(msg)
            args = (obj, self.parent.context)
        else:
            args = (obj, )
        try:
            return method(*args)
        except AttributeError:
            pass
        return missing_

    def _deserialize(self, value):
        if self.deserialize_method_name:
            try:
                method = utils.callable_or_raise(
                    getattr(self.parent, self.deserialize_method_name, None)
                )
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
    _CHECK_ATTRIBUTE = False

    def __init__(self, func, deserialize=None, **kwargs):
        super(Function, self).__init__(**kwargs)
        self.func = utils.callable_or_raise(func)
        if deserialize:
            self.deserialize_func = utils.callable_or_raise(deserialize)
        else:
            self.deserialize_func = None

    def _serialize(self, value, attr, obj):
        try:
            if len(utils.get_func_args(self.func)) > 1:
                if self.parent.context is None:
                    msg = 'No context available for Function field {0!r}'.format(attr)
                    raise ValidationError(msg)
                return self.func(obj, self.parent.context)
            else:
                return self.func(obj)
        except AttributeError:  # the object is not expected to have the attribute
            pass
        return missing_

    def _deserialize(self, value):
        if self.deserialize_func:
            return self.deserialize_func(value)
        return value


class Select(Field):
    """A field that provides a set of values which an attribute must be
    contrained to.

    :param choices: A list of valid values.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    :raise: ValidationError if attribute's value is not one of the given choices.
    """
    def __init__(self, choices, **kwargs):
        warnings.warn(
            'The Select field is deprecated. Use the '
            'marshmallow.validate.OneOf validator '
            'instead.', category=DeprecationWarning
        )
        self.choices = choices
        return super(Select, self).__init__(**kwargs)

    def _validated(self, value):
        if value not in self.choices:
            raise ValidationError(
                getattr(self, 'error', None) or
                "{0!r} is not a valid choice for this field.".format(value)
            )
        return value

    def _serialize(self, value, attr, obj):
        return self._validated(value)

    def _deserialize(self, value):
        return self._validated(value)


class QuerySelect(Field):
    """A field that (de)serializes an ORM-mapped object to its primary
    (or otherwise unique) key and vice versa. A nonexistent key will
    result in a validation error. This field is ORM-agnostic.

    Example: ::

        query = session.query(User).order_by(User.id).all
        keygetter = 'id'
        field = fields.QuerySelect(query, keygetter)

    :param callable query: The query which will be executed at each
        (de)serialization to find the list of valid objects and keys.
    :param keygetter: Can be a callable or a string. In the former case, it must
        be a one-argument callable which returns a unique comparable
        key. In the latter case, the string specifies the name of
        an attribute of the ORM-mapped object.
    :param str error: Error message stored upon validation failure.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionadded:: 1.2.0
    """
    def __init__(self, query, keygetter, **kwargs):
        self.query = query
        self.keygetter = keygetter if callable(keygetter) else attrgetter(keygetter)
        super(QuerySelect, self).__init__(**kwargs)

    def keys(self):
        """Return a generator over the valid keys."""
        return (self.keygetter(item) for item in self.query())

    def results(self):
        """Return a generator over the query results."""
        return (item for item in self.query())

    def pairs(self):
        """Return a generator over the (key, result) pairs."""
        return ((self.keygetter(item), item) for item in self.query())

    def labels(self, labelgetter=text_type):
        """Return a generator over the (key, label) pairs, where
        label is a string associated with each query result. This
        convenience method is useful to populate, for instance,
        a form select field.

        :param labelgetter: Can be a callable or a string. In the former case,
            it must be a one-argument callable which returns the label text. In the
            latter case, the string specifies the name of an attribute of
            the ORM-mapped object. If not provided the ORM-mapped object's
            `__str__` or `__unicode__` method will be used.
        """
        labelgetter = labelgetter if callable(labelgetter) else attrgetter(labelgetter)
        return ((self.keygetter(item), labelgetter(item)) for item in self.query())

    def _serialize(self, value, attr, obj):
        value = self.keygetter(value)

        for key in self.keys():
            if key == value:
                return value

        error = getattr(self, 'error', None) or 'Invalid object.'
        raise ValidationError(error)

    def _deserialize(self, value):
        for key, result in self.pairs():
            if key == value:
                return result

        error = getattr(self, 'error', None) or 'Invalid key.'
        raise ValidationError(error)


class QuerySelectList(QuerySelect):
    """A field that (de)serializes a list of ORM-mapped objects to
    a list of their primary (or otherwise unique) keys and vice
    versa. If any of the items in the list cannot be found in the
    query, this will result in a validation error. This field
    is ORM-agnostic.

    :param callable query: Same as :class:`QuerySelect`.
    :param keygetter: Same as :class:`QuerySelect`.
    :param str error: Error message stored upon validation failure.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionadded:: 1.2.0
    """
    def _serialize(self, value, attr, obj):
        items = [self.keygetter(v) for v in value]

        if not items:
            return []

        keys = list(self.keys())

        for item in items:
            try:
                keys.remove(item)
            except ValueError:
                error = getattr(self, 'error', None) or 'Invalid objects.'
                raise ValidationError(error)

        return items

    def _deserialize(self, value):
        if not value:
            return []

        keys, results = (list(t) for t in zip(*self.pairs()))
        items = []

        for val in value:
            try:
                index = keys.index(val)
            except ValueError:
                error = getattr(self, 'error', None) or 'Invalid keys.'
                raise ValidationError(error)
            else:
                del keys[index]
                items.append(results.pop(index))

        return items

# Aliases
URL = Url
Enum = Select
Str = String
Bool = Boolean
Int = Integer
