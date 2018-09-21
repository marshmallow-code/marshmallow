# -*- coding: utf-8 -*-
"""Field classes for various types of data."""

from __future__ import absolute_import, unicode_literals

import collections
import copy
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
from marshmallow.validate import Validator

__all__ = [
    'Field',
    'Raw',
    'Nested',
    'Dict',
    'List',
    'String',
    'UUID',
    'Number',
    'Integer',
    'Decimal',
    'Boolean',
    'FormattedString',
    'Float',
    'DateTime',
    'LocalDateTime',
    'Time',
    'Date',
    'TimeDelta',
    'Url',
    'URL',
    'Email',
    'Method',
    'Function',
    'Str',
    'Bool',
    'Int',
    'Constant',
]

MISSING_ERROR_MESSAGE = (
    'ValidationError raised by `{class_name}`, but error key `{key}` does '
    'not exist in the `error_messages` dictionary.'
)
_RECURSIVE_NESTED = 'self'


class Field(FieldABC):
    """Basic field from which other fields should extend. It applies no
    formatting by default, and should only be used in cases where
    data does not need to be formatted before being serialized or deserialized.
    On error, the name of the field will be returned.

    :param default: If set, this value will be used during serialization if the input value
        is missing. If not set, the field will be excluded from the serialized output if the
        input value is missing. May be a value or a callable.
    :param str attribute: The name of the attribute to get the value from. If
        `None`, assumes the attribute has the same name as the field.
    :param str load_from: Additional key to look for when deserializing. Will only
        be checked if the field's name is not found on the input dictionary. If checked,
        it will return this parameter on error.
    :param str dump_to: Field name to use as a key when serializing.
    :param callable validate: Validator or collection of validators that are called
        during deserialization. Validator takes a field's input value as
        its only parameter and returns a boolean.
        If it returns `False`, an :exc:`ValidationError` is raised.
    :param required: Raise a :exc:`ValidationError` if the field value
        is not supplied during deserialization.
    :param allow_none: Set this to `True` if `None` should be considered a valid value during
        validation/deserialization. If ``missing=None`` and ``allow_none`` is unset,
        will default to ``True``. Otherwise, the default is ``False``.
    :param bool load_only: If `True` skip this field during serialization, otherwise
        its value will be present in the serialized data.
    :param bool dump_only: If `True` skip this field during deserialization, otherwise
        its value will be present in the deserialized object. In the context of an
        HTTP API, this effectively marks the field as "read-only".
    :param missing: Default deserialization value for the field if the field is not
        found in the input data. May be a value or a callable.
    :param dict error_messages: Overrides for `Field.default_error_messages`.
    :param metadata: Extra arguments to be stored as metadata.

    .. versionchanged:: 2.0.0
        Removed `error` parameter. Use ``error_messages`` instead.

    .. versionchanged:: 2.0.0
        Added `allow_none` parameter, which makes validation/deserialization of `None`
        consistent across fields.

    .. versionchanged:: 2.0.0
        Added `load_only` and `dump_only` parameters, which allow field skipping
        during the (de)serialization process.

    .. versionchanged:: 2.0.0
        Added `missing` parameter, which indicates the value for a field if the field
        is not found during deserialization.

    .. versionchanged:: 2.0.0
        ``default`` value is only used if explicitly set. Otherwise, missing values
        inputs are excluded from serialized output.
    """
    # Some fields, such as Method fields and Function fields, are not expected
    #  to exists as attributes on the objects to serialize. Set this to False
    #  for those fields
    _CHECK_ATTRIBUTE = True
    _creation_index = 0  # Used for sorting

    #: Default error messages for various kinds of errors. The keys in this dictionary
    #: are passed to `Field.fail`. The values are error messages passed to
    #: :exc:`marshmallow.ValidationError`.
    default_error_messages = {
        'required': 'Missing data for required field.',
        'type': 'Invalid input type.', # used by Unmarshaller
        'null': 'Field may not be null.',
        'validator_failed': 'Invalid value.'
    }

    def __init__(self, default=missing_, attribute=None, load_from=None, dump_to=None,
                 error=None, validate=None, required=False, allow_none=None, load_only=False,
                 dump_only=False, missing=missing_, error_messages=None, **metadata):
        self.default = default
        self.attribute = attribute
        self.load_from = load_from  # this flag is used by Unmarshaller
        self.dump_to = dump_to  # this flag is used by Marshaller
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
        # If missing=None, None should be considered valid by default
        if allow_none is None:
            if missing is None:
                self.allow_none = True
            else:
                self.allow_none = False
        else:
            self.allow_none = allow_none
        self.load_only = load_only
        self.dump_only = dump_only
        self.missing = missing
        self.metadata = metadata
        self._creation_index = Field._creation_index
        Field._creation_index += 1

        # Collect default error message from self and parent classes
        messages = {}
        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

    def __repr__(self):
        return ('<fields.{ClassName}(default={self.default!r}, '
                'attribute={self.attribute!r}, '
                'validate={self.validate}, required={self.required}, '
                'load_only={self.load_only}, dump_only={self.dump_only}, '
                'missing={self.missing}, allow_none={self.allow_none}, '
                'error_messages={self.error_messages})>'
                .format(ClassName=self.__class__.__name__, self=self))

    def get_value(self, attr, obj, accessor=None, default=missing_):
        """Return the value for a given key from an object."""
        # NOTE: Use getattr instead of direct attribute access here so that
        # subclasses aren't required to define `attribute` member
        attribute = getattr(self, 'attribute', None)
        accessor_func = accessor or utils.get_value
        check_key = attr if attribute is None else attribute
        return accessor_func(check_key, obj, default)

    def _validate(self, value):
        """Perform validation on ``value``. Raise a :exc:`ValidationError` if validation
        does not succeed.
        """
        errors = []
        kwargs = {}
        for validator in self.validators:
            try:
                r = validator(value)
                if not isinstance(validator, Validator) and r is False:
                    self.fail('validator_failed')
            except ValidationError as err:
                kwargs.update(err.kwargs)
                if isinstance(err.messages, dict):
                    errors.append(err.messages)
                else:
                    errors.extend(err.messages)
        if errors:
            raise ValidationError(errors, **kwargs)

    # Hat tip to django-rest-framework.
    def fail(self, key, **kwargs):
        """A helper method that simply raises a `ValidationError`.
        """
        try:
            msg = self.error_messages[key]
        except KeyError:
            class_name = self.__class__.__name__
            msg = MISSING_ERROR_MESSAGE.format(class_name=class_name, key=key)
            raise AssertionError(msg)
        if isinstance(msg, basestring):
            msg = msg.format(**kwargs)
        raise ValidationError(msg)

    def _validate_missing(self, value):
        """Validate missing values. Raise a :exc:`ValidationError` if
        `value` should be considered missing.
        """
        if value is missing_:
            if hasattr(self, 'required') and self.required:
                self.fail('required')
        if value is None:
            if hasattr(self, 'allow_none') and self.allow_none is not True:
                self.fail('null')

    def serialize(self, attr, obj, accessor=None):
        """Pulls the value for the given key from the object, applies the
        field's formatting and returns the result.

        :param str attr: The attibute or key to get from the object.
        :param str obj: The object to pull the key from.
        :param callable accessor: Function used to pull values from ``obj``.
        :raise ValidationError: In case of formatting problem
        """
        if self._CHECK_ATTRIBUTE:
            value = self.get_value(attr, obj, accessor=accessor)
            if value is missing_:
                if hasattr(self, 'default'):
                    if callable(self.default):
                        return self.default()
                    else:
                        return self.default
        else:
            value = None
        return self._serialize(value, attr, obj)

    def deserialize(self, value, attr=None, data=None):
        """Deserialize ``value``.

        :raise ValidationError: If an invalid value is passed or if a required value
            is missing.
        """
        # Validate required fields, deserialize, then validate
        # deserialized value
        self._validate_missing(value)
        if getattr(self, 'allow_none', False) is True and value is None:
            return None
        output = self._deserialize(value, attr, data)
        self._validate(output)
        return output

    # Methods for concrete classes to override.

    def _add_to_schema(self, field_name, schema):
        """Update field with values from its parent schema. Called by
            :meth:`__set_field_attrs <marshmallow.Schema.__set_field_attrs>`.

        :param str field_name: Field name set in schema.
        :param Schema schema: Parent schema.
        """
        self.parent = self.parent or schema
        self.name = self.name or field_name

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
        :return: The serialized value
        """
        return value

    def _deserialize(self, value, attr, data):
        """Deserialize value. Concrete :class:`Field` classes should implement this method.

        :param value: The value to be deserialized.
        :param str attr: The attribute/key in `data` to be deserialized.
        :param dict data: The raw input data passed to the `Schema.load`.
        :raise ValidationError: In case of formatting or validation failure.
        :return: The deserialized value.

        .. versionchanged:: 2.0.0
            Added ``attr`` and ``data`` parameters.
        """
        return value

    # Properties

    @property
    def context(self):
        """The context dictionary for the parent :class:`Schema`."""
        return self.parent.context

    @property
    def root(self):
        """Reference to the `Schema` that this field belongs to even if it is buried in a `List`.
        Return `None` for unbound fields.
        """
        ret = self
        while hasattr(ret, 'parent') and ret.parent:
            ret = ret.parent
        return ret if isinstance(ret, SchemaABC) else None

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

    When passing a `Schema <marshmallow.Schema>` instance as the first argument,
    the instance's ``exclude``, ``only``, and ``many`` attributes will be respected.

    Therefore, when passing the ``exclude``, ``only``, or ``many`` arguments to `fields.Nested`,
    you should pass a `Schema <marshmallow.Schema>` class (not an instance) as the first argument.

    ::

        # Yes
        author = fields.Nested(UserSchema, only=('id', 'name'))

        # No
        author = fields.Nested(UserSchema(), only=('id', 'name'))

    :param Schema nested: The Schema class or class name (string)
        to nest, or ``"self"`` to nest the :class:`Schema` within itself.
    :param tuple exclude: A list or tuple of fields to exclude.
    :param required: Raise an :exc:`ValidationError` during deserialization
        if the field, *and* any required field values specified
        in the `nested` schema, are not found in the data. If not a `bool`
        (e.g. a `str`), the provided value will be used as the message of the
        :exc:`ValidationError` instead of the default message.
    :param only: A tuple or string of the field(s) to marshal. If `None`, all fields
        will be marshalled. If a field name (string) is given, only a single
        value will be returned as output instead of a dictionary.
        This parameter takes precedence over ``exclude``.
    :param bool many: Whether the field is a collection of objects.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    default_error_messages = {
        'type': 'Invalid type.',
    }

    def __init__(self, nested, default=missing_, exclude=tuple(), only=None, **kwargs):
        self.nested = nested
        self.only = only
        self.exclude = exclude
        self.many = kwargs.get('many', False)
        self.__schema = None  # Cached Schema instance
        self.__updated_fields = False
        super(Nested, self).__init__(default=default, **kwargs)

    @property
    def schema(self):
        """The nested Schema object.

        .. versionchanged:: 1.0.0
            Renamed from `serializer` to `schema`
        """
        if not self.__schema:
            # Ensure that only parameter is a tuple
            if isinstance(self.only, basestring):
                only = (self.only,)
            else:
                only = self.only

            # Inherit context from parent.
            context = getattr(self.parent, 'context', {})
            if isinstance(self.nested, SchemaABC):
                self.__schema = self.nested
                self.__schema.context.update(context)
            elif isinstance(self.nested, type) and \
                    issubclass(self.nested, SchemaABC):
                self.__schema = self.nested(many=self.many,
                        only=only, exclude=self.exclude, context=context,
                        load_only=self._nested_normalized_option('load_only'),
                        dump_only=self._nested_normalized_option('dump_only'))
            elif isinstance(self.nested, basestring):
                if self.nested == _RECURSIVE_NESTED:
                    parent_class = self.parent.__class__
                    self.__schema = parent_class(many=self.many, only=only,
                            exclude=self.exclude, context=context,
                            load_only=self._nested_normalized_option('load_only'),
                            dump_only=self._nested_normalized_option('dump_only'))
                else:
                    schema_class = class_registry.get_class(self.nested)
                    self.__schema = schema_class(many=self.many,
                            only=only, exclude=self.exclude, context=context,
                            load_only=self._nested_normalized_option('load_only'),
                            dump_only=self._nested_normalized_option('dump_only'))
            else:
                raise ValueError('Nested fields must be passed a '
                                 'Schema, not {0}.'.format(self.nested.__class__))
            self.__schema.ordered = getattr(self.parent, 'ordered', False)
        return self.__schema

    def _nested_normalized_option(self, option_name):
        nested_field = '%s.' % self.name
        return [field.split(nested_field, 1)[1]
                for field in getattr(self.root, option_name, set())
                if field.startswith(nested_field)]

    def _serialize(self, nested_obj, attr, obj):
        # Load up the schema first. This allows a RegistryError to be raised
        # if an invalid schema name was passed
        schema = self.schema
        if nested_obj is None:
            return None
        if not self.__updated_fields:
            schema._update_fields(obj=nested_obj, many=self.many)
            self.__updated_fields = True
        ret, errors = schema.dump(nested_obj, many=self.many,
                update_fields=not self.__updated_fields)
        if isinstance(self.only, basestring):  # self.only is a field name
            only_field = self.schema.fields[self.only]
            key = ''.join([self.schema.prefix or '', only_field.dump_to or self.only])
            if self.many:
                return utils.pluck(ret, key=key)
            else:
                return ret[key]
        if errors:
            raise ValidationError(errors, data=ret)
        return ret

    def _deserialize(self, value, attr, data):
        if self.many and not utils.is_collection(value):
            self.fail('type', input=value, type=value.__class__.__name__)

        data, errors = self.schema.load(value)
        if errors:
            raise ValidationError(errors, data=data)
        return data

    def _validate_missing(self, value):
        """Validate missing values. Raise a :exc:`ValidationError` if
        `value` should be considered missing.
        """
        if value is missing_ and hasattr(self, 'required'):
            if self.nested == _RECURSIVE_NESTED:
                self.fail('required')
            errors = self._check_required()
            if errors:
                raise ValidationError(errors)
        else:
            super(Nested, self)._validate_missing(value)

    def _check_required(self):
        errors = {}
        if self.required:
            for field_name, field in self.schema.fields.items():
                if not field.required:
                    continue
                error_field_name = field.load_from or field_name
                if (
                    isinstance(field, Nested) and
                    self.nested != _RECURSIVE_NESTED and
                    field.nested != _RECURSIVE_NESTED
                ):
                    errors[error_field_name] = field._check_required()
                else:
                    try:
                        field._validate_missing(field.missing)
                    except ValidationError as ve:
                        errors[error_field_name] = ve.messages
            if self.many and errors:
                errors = {0: errors}
            # No inner errors; just raise required error like normal
            if not errors:
                self.fail('required')
        return errors


class List(Field):
    """A list field, composed with another `Field` class or
    instance.

    Example: ::

        numbers = fields.List(fields.Float())

    :param Field cls_or_instance: A field class or instance.
    :param bool default: Default value for serialization.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionchanged:: 2.0.0
        The ``allow_none`` parameter now applies to deserialization and
        has the same semantics as the other fields.
    """
    default_error_messages = {
        'invalid': 'Not a valid list.',
    }

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

    def get_value(self, attr, obj, accessor=None):
        """Return the value for a given key from an object."""
        value = super(List, self).get_value(attr, obj, accessor=accessor)
        if self.container.attribute:
            if utils.is_collection(value):
                return [
                    self.container.get_value(self.container.attribute, each)
                    for each in value
                ]
            return self.container.get_value(self.container.attribute, value)
        return value

    def _add_to_schema(self, field_name, schema):
        super(List, self)._add_to_schema(field_name, schema)
        self.container = copy.deepcopy(self.container)
        self.container.parent = self
        self.container.name = field_name

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        if utils.is_collection(value):
            return [self.container._serialize(each, attr, obj) for each in value]
        return [self.container._serialize(value, attr, obj)]

    def _deserialize(self, value, attr, data):
        if not utils.is_collection(value):
            self.fail('invalid')

        result = []
        errors = {}
        for idx, each in enumerate(value):
            try:
                result.append(self.container.deserialize(each))
            except ValidationError as e:
                result.append(e.data)
                errors.update({idx: e.messages})

        if errors:
            raise ValidationError(errors, data=result)

        return result

class String(Field):
    """A string field.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    default_error_messages = {
        'invalid': 'Not a valid string.',
        'invalid_utf8': 'Not a valid utf-8 string.'
    }

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        return utils.ensure_text_type(value)

    def _deserialize(self, value, attr, data):
        if not isinstance(value, basestring):
            self.fail('invalid')
        try:
            return utils.ensure_text_type(value)
        except UnicodeDecodeError:
            self.fail('invalid_utf8')


class UUID(String):
    """A UUID field."""
    default_error_messages = {
        'invalid_uuid': 'Not a valid UUID.',
        'invalid_guid': 'Not a valid UUID.'  # TODO: Remove this in marshmallow 3.0
    }

    def _validated(self, value):
        """Format the value or raise a :exc:`ValidationError` if an error occurs."""
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError):
            self.fail('invalid_uuid')

    def _serialize(self, value, attr, obj):
        validated = str(self._validated(value)) if value is not None else None
        return super(String, self)._serialize(validated, attr, obj)

    def _deserialize(self, value, attr, data):
        return self._validated(value)


class Number(Field):
    """Base class for number fields.

    :param bool as_string: If True, format the serialized value as a string.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    num_type = float
    default_error_messages = {
        'invalid': 'Not a valid number.'
    }

    def __init__(self, as_string=False, **kwargs):
        self.as_string = as_string
        super(Number, self).__init__(**kwargs)

    def _format_num(self, value):
        """Return the number value for value, given this field's `num_type`."""
        if value is None:
            return None
        return self.num_type(value)

    def _validated(self, value):
        """Format the value or raise a :exc:`ValidationError` if an error occurs."""
        try:
            return self._format_num(value)
        except (TypeError, ValueError) as err:
            self.fail('invalid')

    def _to_string(self, value):
        return str(value)

    def _serialize(self, value, attr, obj):
        """Return a string if `self.as_string=True`, otherwise return this field's `num_type`."""
        ret = self._validated(value)
        return self._to_string(ret) if (self.as_string and ret not in (None, missing_)) else ret

    def _deserialize(self, value, attr, data):
        return self._validated(value)


class Integer(Number):
    """An integer field.

    :param kwargs: The same keyword arguments that :class:`Number` receives.
    """

    num_type = int
    default_error_messages = {
        'invalid': 'Not a valid integer.'
    }


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

    .. warning::

        If a JSON `float` value is passed to this field for deserialization it will
        first be cast to its corresponding `string` value before being deserialized
        to a `decimal.Decimal` object. The default `__str__` implementation of the
        built-in Python `float` type may apply a destructive transformation upon
        its input data and therefore cannot be relied upon to preserve precision.
        To avoid this, you can instead pass a JSON `string` to be deserialized
        directly.

    :param int places: How many decimal places to quantize the value. If `None`, does
        not quantize the value.
    :param rounding: How to round the value during quantize, for example
        `decimal.ROUND_UP`. If None, uses the rounding value from
        the current thread's context.
    :param bool allow_nan: If `True`, `NaN`, `Infinity` and `-Infinity` are allowed,
        even though they are illegal according to the JSON specification.
    :param bool as_string: If True, serialize to a string instead of a Python
        `decimal.Decimal` type.
    :param kwargs: The same keyword arguments that :class:`Number` receives.

    .. versionadded:: 1.2.0
    """

    num_type = decimal.Decimal

    default_error_messages = {
        'special': 'Special numeric values are not permitted.',
    }

    def __init__(self, places=None, rounding=None, allow_nan=False, as_string=False, **kwargs):
        self.places = decimal.Decimal((0, (1,), -places)) if places is not None else None
        self.rounding = rounding
        self.allow_nan = allow_nan
        super(Decimal, self).__init__(as_string=as_string, **kwargs)

    # override Number
    def _format_num(self, value):
        if value is None:
            return None

        num = decimal.Decimal(str(value))

        if self.allow_nan:
            if num.is_nan():
                return decimal.Decimal('NaN')  # avoid sNaN, -sNaN and -NaN
        else:
            if num.is_nan() or num.is_infinite():
                self.fail('special')

        if self.places is not None and num.is_finite():
            num = num.quantize(self.places, rounding=self.rounding)

        return num

    # override Number
    def _validated(self, value):
        try:
            return super(Decimal, self)._validated(value)
        except decimal.InvalidOperation:
            self.fail('invalid')

    # override Number
    def _to_string(self, value):
        return format(value, 'f')


class Boolean(Field):
    """A boolean field.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """
    #: Values that will (de)serialize to `True`. If an empty set, any non-falsy
    #  value will deserialize to `True`.
    truthy = set(('t', 'T', 'true', 'True', 'TRUE', '1', 1, True))
    #: Values that will (de)serialize to `False`.
    falsy = set(('f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False))

    default_error_messages = {
        'invalid': 'Not a valid boolean.'
    }

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        elif value in self.truthy:
            return True
        elif value in self.falsy:
            return False

        return bool(value)

    def _deserialize(self, value, attr, data):
        if not self.truthy:
            return bool(value)
        else:
            try:
                if value in self.truthy:
                    return True
                elif value in self.falsy:
                    return False
            except TypeError:
                pass
        self.fail('invalid')

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
    default_error_messages = {
        'format': 'Cannot format string with given data.'
    }
    _CHECK_ATTRIBUTE = False

    def __init__(self, src_str, *args, **kwargs):
        Field.__init__(self, *args, **kwargs)
        self.src_str = text_type(src_str)

    def _serialize(self, value, attr, obj):
        try:
            data = utils.to_marshallable_type(obj)
            return self.src_str.format(**data)
        except (TypeError, IndexError) as error:
            self.fail('format')


class Float(Number):
    """
    A double as IEEE-754 double precision string.

    :param bool as_string: If True, format the value as a string.
    :param kwargs: The same keyword arguments that :class:`Number` receives.
    """

    num_type = float


class DateTime(Field):
    """A formatted datetime string in UTC.

    Example: ``'2014-12-22T03:12:58.019077+00:00'``

    Timezone-naive `datetime` objects are converted to
    UTC (+00:00) by :meth:`Schema.dump <marshmallow.Schema.dump>`.
    :meth:`Schema.load <marshmallow.Schema.load>` returns `datetime`
    objects that are timezone-aware.

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
    default_error_messages = {
        'invalid': 'Not a valid datetime.',
        'format': '"{input}" cannot be formatted as a datetime.',
    }

    def __init__(self, format=None, **kwargs):
        super(DateTime, self).__init__(**kwargs)
        # Allow this to be None. It may be set later in the ``_serialize``
        # or ``_desrialize`` methods This allows a Schema to dynamically set the
        # dateformat, e.g. from a Meta option
        self.dateformat = format

    def _add_to_schema(self, field_name, schema):
        super(DateTime, self)._add_to_schema(field_name, schema)
        self.dateformat = self.dateformat or schema.opts.dateformat

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        self.dateformat = self.dateformat or self.DEFAULT_FORMAT
        format_func = self.DATEFORMAT_SERIALIZATION_FUNCS.get(self.dateformat, None)
        if format_func:
            try:
                return format_func(value, localtime=self.localtime)
            except (AttributeError, ValueError) as err:
                self.fail('format', input=value)
        else:
            return value.strftime(self.dateformat)

    def _deserialize(self, value, attr, data):
        if not value:  # Falsy values, e.g. '', None, [] are not valid
            raise self.fail('invalid')
        self.dateformat = self.dateformat or self.DEFAULT_FORMAT
        func = self.DATEFORMAT_DESERIALIZATION_FUNCS.get(self.dateformat)
        if func:
            try:
                return func(value)
            except (TypeError, AttributeError, ValueError):
                raise self.fail('invalid')
        elif self.dateformat:
            try:
                return dt.datetime.strptime(value, self.dateformat)
            except (TypeError, AttributeError, ValueError):
                raise self.fail('invalid')
        elif utils.dateutil_available:
            try:
                return utils.from_datestring(value)
            except TypeError:
                raise self.fail('invalid')
        else:
            warnings.warn('It is recommended that you install python-dateutil '
                          'for improved datetime deserialization.')
            raise self.fail('invalid')


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
    default_error_messages = {
        'invalid': 'Not a valid time.',
        'format': '"{input}" cannot be formatted as a time.',
    }

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        try:
            ret = value.isoformat()
        except AttributeError:
            self.fail('format', input=value)
        if value.microsecond:
            return ret[:15]
        return ret

    def _deserialize(self, value, attr, data):
        """Deserialize an ISO8601-formatted time to a :class:`datetime.time` object."""
        if not value:   # falsy values are invalid
            self.fail('invalid')
            raise err
        try:
            return utils.from_iso_time(value)
        except (AttributeError, TypeError, ValueError):
            self.fail('invalid')

class Date(Field):
    """ISO8601-formatted date string.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """
    default_error_messages = {
        'invalid': 'Not a valid date.',
        'format': '"{input}" cannot be formatted as a date.',
    }

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        try:
            return value.isoformat()
        except AttributeError:
            self.fail('format', input=value)
        return value

    def _deserialize(self, value, attr, data):
        """Deserialize an ISO8601-formatted date string to a
        :class:`datetime.date` object.
        """
        if not value:  # falsy values are invalid
            self.fail('invalid')
        try:
            return utils.from_iso_date(value)
        except (AttributeError, TypeError, ValueError):
            self.fail('invalid')


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

    default_error_messages = {
        'invalid': 'Not a valid period of time.',
        'format': '{input!r} cannot be formatted as a timedelta.'
    }

    def __init__(self, precision='seconds', error=None, **kwargs):
        precision = precision.lower()
        units = (self.DAYS, self.SECONDS, self.MICROSECONDS)

        if precision not in units:
            msg = 'The precision must be "{0}", "{1}" or "{2}".'.format(*units)
            raise ValueError(msg)

        self.precision = precision
        super(TimeDelta, self).__init__(error=error, **kwargs)

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
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
            self.fail('format', input=value)

    def _deserialize(self, value, attr, data):
        try:
            value = int(value)
        except (TypeError, ValueError):
            self.fail('invalid')

        kwargs = {self.precision: value}

        try:
            return dt.timedelta(**kwargs)
        except OverflowError:
            self.fail('invalid')


class Dict(Field):
    """A dict field. Supports dicts and dict-like objects.

    .. note::
        This field is only appropriate when the structure of
        nested data is not known. For structured data, use
        `Nested`.

    .. versionadded:: 2.1.0
    """

    default_error_messages = {
        'invalid': 'Not a valid mapping type.'
    }

    def _deserialize(self, value, attr, data):
        if isinstance(value, collections.Mapping):
            return value
        else:
            self.fail('invalid')


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
    default_error_messages = {'invalid': 'Not a valid URL.'}

    def __init__(self, relative=False, schemes=None, **kwargs):
        String.__init__(self, **kwargs)

        self.relative = relative
        # Insert validation into self.validators so that multiple errors can be
        # stored.
        self.validators.insert(0, validate.URL(
            relative=self.relative,
            schemes=schemes,
            error=self.error_messages['invalid']
        ))

    def _validated(self, value):
        if value is None:
            return None
        return validate.URL(
            relative=self.relative,
            error=self.error_messages['invalid']
        )(value)


class Email(ValidatedField, String):
    """A validated email field. Validation occurs during both serialization and
    deserialization.

    :param args: The same positional arguments that :class:`String` receives.
    :param kwargs: The same keyword arguments that :class:`String` receives.
    """
    default_error_messages = {'invalid': 'Not a valid email address.'}
    def __init__(self, *args, **kwargs):
        String.__init__(self, *args, **kwargs)
        # Insert validation into self.validators so that multiple errors can be
        # stored.
        self.validators.insert(0, validate.Email(error=self.error_messages['invalid']))

    def _validated(self, value):
        if value is None:
            return None
        return validate.Email(
            error=self.error_messages['invalid']
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
        Removed optional ``context`` parameter on methods. Use ``self.context`` instead.
    .. versionchanged:: 2.3.0
        Deprecated ``method_name`` parameter in favor of ``serialize`` and allow
        ``serialize`` to not be passed at all.
    """
    _CHECK_ATTRIBUTE = False

    def __init__(self, serialize=None, deserialize=None, method_name=None, **kwargs):
        if method_name is not None:
            warnings.warn('"method_name" argument of fields.Method is deprecated. '
                          'Use the "serialize" argument instead.', DeprecationWarning)

        self.serialize_method_name = self.method_name = serialize or method_name
        self.deserialize_method_name = deserialize
        super(Method, self).__init__(**kwargs)

    def _serialize(self, value, attr, obj):
        if not self.serialize_method_name:
            return missing_

        method = utils.callable_or_raise(
            getattr(self.parent, self.serialize_method_name, None)
        )
        try:
            return method(obj)
        except AttributeError:
            pass
        return missing_

    def _deserialize(self, value, attr, data):
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

    :param callable serialize: A callable from which to retrieve the value.
        The function must take a single argument ``obj`` which is the object
        to be serialized. It can also optionally take a ``context`` argument,
        which is a dictionary of context variables passed to the serializer.
        If no callable is provided then the ```load_only``` flag will be set
        to True.
    :param callable deserialize: A callable from which to retrieve the value.
        The function must take a single argument ``value`` which is the value
        to be deserialized. It can also optionally take a ``context`` argument,
        which is a dictionary of context variables passed to the deserializer.
        If no callable is provided then ```value``` will be passed through
        unchanged.
    :param callable func: This argument is to be deprecated. It exists for
        backwards compatiblity. Use serialize instead.

    .. versionchanged:: 2.3.0
        Deprecated ``func`` parameter in favor of ``serialize``.
    """
    _CHECK_ATTRIBUTE = False

    def __init__(self, serialize=None, deserialize=None, func=None, **kwargs):
        if func:
            warnings.warn('"func" argument of fields.Function is deprecated. '
                          'Use the "serialize" argument instead.', DeprecationWarning)
            serialize = func
        super(Function, self).__init__(**kwargs)
        self.serialize_func = self.func = serialize and utils.callable_or_raise(serialize)
        self.deserialize_func = deserialize and utils.callable_or_raise(deserialize)

    def _serialize(self, value, attr, obj):
        try:
            return self._call_or_raise(self.serialize_func, obj, attr)
        except AttributeError:  # the object is not expected to have the attribute
            pass
        return missing_

    def _deserialize(self, value, attr, data):
        if self.deserialize_func:
            return self._call_or_raise(self.deserialize_func, value, attr)
        return value

    def _call_or_raise(self, func, value, attr):
        if len(utils.get_func_args(func)) > 1:
            if self.parent.context is None:
                msg = 'No context available for Function field {0!r}'.format(attr)
                raise ValidationError(msg)
            return func(value, self.parent.context)
        else:
            return func(value)



class Constant(Field):
    """A field that (de)serializes to a preset constant.  If you only want the
    constant added for serialization or deserialization, you should use
    ``dump_only=True`` or ``load_only=True`` respectively.

    :param constant: The constant to return for the field attribute.

    .. versionadded:: 2.0.0
    """
    _CHECK_ATTRIBUTE = False

    def __init__(self, constant, **kwargs):
        super(Constant, self).__init__(**kwargs)
        self.constant = constant
        self.missing = constant
        self.default = constant

    def _serialize(self, value, *args, **kwargs):
        return self.constant

    def _deserialize(self, value, *args, **kwargs):
        return self.constant


# Aliases
URL = Url
Str = String
Bool = Boolean
Int = Integer
