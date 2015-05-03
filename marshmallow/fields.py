# -*- coding: utf-8 -*-
"""Field classes for various types of data.
"""
from __future__ import absolute_import, unicode_literals

import datetime as dt
import uuid
import warnings
import decimal
from operator import attrgetter

from marshmallow import validate, utils, class_registry
from marshmallow.base import FieldABC, SchemaABC
from marshmallow.compat import text_type, iteritems, total_seconds, basestring
from marshmallow.exceptions import (
    MarshallingError,
    UnmarshallingError,
    ForcedError,
    RegistryError,
    ValidationError,
)


__all__ = [
    'Marshaller',
    'Unmarshaller',
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
    'null',
    'missing',
]

class _Null(object):

    def __bool__(self):
        return False

    __nonzero__ = __bool__  # PY2 compat

    def __repr__(self):
        return '<marshmallow.fields.null>'

class _Missing(_Null):

    def __repr__(self):
        return '<marshmallow.fields.missing>'

# Singleton that represents an empty value. Used as the default for Nested
# fields so that `Field._call_with_validation` is invoked, even when the
# object to serialize has the nested attribute set to None. Therefore,
# `RegistryErrors` are properly raised.
null = _Null()

# Singleton value that indicates that a field's value is missing from input
# dict passed to :meth:`Schema.load`. If the field's value is not required,
# it's ``default`` value is used.
missing = _Missing()

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
    except RegistryError:
        raise
    except exception_class as err:  # Store errors
        if strict:
            err.field = field_obj
            err.field_name = field_name
            raise err
        # Warning: Mutation!
        if (hasattr(err, 'underlying_exception') and
                isinstance(err.underlying_exception, ValidationError)):
            validation_error = err.underlying_exception
            if isinstance(validation_error.messages, dict):
                errors_dict[field_name] = validation_error.messages
            else:
                errors_dict.setdefault(field_name, []).extend(validation_error.messages)
        else:
            errors_dict.setdefault(field_name, []).append(text_type(err))
        value = None
    except TypeError:
        # field declared as a class, not an instance
        if (isinstance(field_obj, type) and
                issubclass(field_obj, FieldABC)):
            msg = ('Field for "{0}" must be declared as a '
                            'Field instance, not a class. '
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
        #: True while serializing a collection
        self.__pending = False

    def serialize(self, obj, fields_dict, many=False, strict=False, skip_missing=False,
                  accessor=None, dict_class=None):
        """Takes raw data (a dict, list, or other object) and a dict of
        fields to output and serializes the data based on those fields.

        :param obj: The actual object(s) from which the fields are taken from
        :param dict fields_dict: Mapping of field names to :class:`Field` objects.
        :param bool many: Set to `True` if ``data`` should be serialized as
            a collection.
        :param bool strict: If `True`, raise errors if invalid data are passed in
            instead of failing silently and storing the errors.
        :param skip_missing: If `True`, skip key:value pairs when ``value`` is `None`.
        :param callable accessor: Function to use for getting values from ``obj``.
        :param type dict_class: Dictionary class used to construct the output.
        :return: A dictionary of the marshalled data

        .. versionchanged:: 1.0.0
            Renamed from ``marshal``.
        """
        dict_class = dict_class or dict
        # Reset errors dict if not serializing a collection
        if not self.__pending:
            self.errors = {}
        if many and obj is not None:
            self.__pending = True
            ret = [self.serialize(d, fields_dict, many=False, strict=strict,
                                    dict_class=dict_class, accessor=accessor,
                                    skip_missing=skip_missing)
                    for d in obj]
            self.__pending = False
            return ret
        items = []
        for attr_name, field_obj in iteritems(fields_dict):
            key = ''.join([self.prefix, attr_name])
            getter = lambda d: field_obj.serialize(attr_name, d, accessor=accessor)
            value = _call_and_store(
                getter_func=getter,
                data=obj,
                field_name=key,
                field_obj=field_obj,
                errors_dict=self.errors,
                exception_class=MarshallingError,
                strict=strict
            )
            if (value is missing) or (skip_missing and
                                      value in field_obj.SKIPPABLE_VALUES):
                continue
            items.append((key, value))
        return dict_class(items)

    # Make an instance callable
    __call__ = serialize


class Unmarshaller(object):
    """Callable class responsible for deserializing data and storing errors.

    .. versionadded:: 1.0.0
    """
    def __init__(self):
        #: Dictionary of errors stored during deserialization
        self.errors = {}
        #: True while deserializing a collection
        self.__pending = False

    def _validate(self, validators, output, fields_dict, strict=False):
        """Perform schema-level validation. Stores errors if ``strict`` is `False`.
        """
        for validator_func in validators:
            try:
                if validator_func(output) is False:
                    func_name = utils.get_callable_name(validator_func)
                    raise ValidationError('Schema validator {0}({1}) is False'.format(
                        func_name, dict(output)
                    ))
            except ValidationError as err:
                # Store or reraise errors
                if err.field:
                    field_name = err.field
                    field_obj = fields_dict[field_name]
                else:
                    field_name = '_schema'
                    field_obj = None
                if strict:
                    raise UnmarshallingError(err, field=field_obj, field_name=field_name)
                if isinstance(err.messages, (list, tuple)):
                    # self.errors[field_name] may be a dict if schemas are nested
                    if isinstance(self.errors.get(field_name), dict):
                        self.errors[field_name].setdefault(
                            '_schema', []
                        ).extend(err.messages)
                    else:
                        self.errors.setdefault(field_name, []).extend(err.messages)
                elif isinstance(err.messages, dict):
                    self.errors.setdefault(field_name, []).append(err.messages)
                else:
                    self.errors.setdefault(field_name, []).append(text_type(err))
        return output

    def deserialize(self, data, fields_dict, many=False, validators=None,
            preprocess=None, postprocess=None, strict=False, dict_class=None):
        """Deserialize ``data`` based on the schema defined by ``fields_dict``.

        :param dict data: The data to deserialize.
        :param dict fields_dict: Mapping of field names to :class:`Field` objects.
        :param bool many: Set to `True` if ``data`` should be deserialized as
            a collection.
        :param list validators: List of validation functions to apply to the
            deserialized dictionary.
        :param list preprocess: List of pre-processing functions.
        :param list postprocess: List of post-processing functions.
        :param bool strict: If `True`, raise errors if invalid data are passed in
            instead of failing silently and storing the errors.
        :param type dict_class: Dictionary class used to construct the output.
        :return: A dictionary of the deserialized data.
        """
        dict_class = dict_class or dict
        # Reset errors if not deserializing a collection
        if not self.__pending:
            self.errors = {}
        if many and data is not None:
            self.__pending = True
            ret = [self.deserialize(d, fields_dict, many=False,
                        validators=validators, preprocess=preprocess,
                        postprocess=postprocess, strict=strict, dict_class=dict_class)
                    for d in data]
            self.__pending = False
            return ret
        if data is not None:
            items = []
            for attr_name, field_obj in iteritems(fields_dict):
                if attr_name not in fields_dict:
                    continue
                key = fields_dict[attr_name].attribute or attr_name
                try:
                    raw_value = data.get(attr_name, missing)
                except AttributeError:
                    msg = 'Data must be a dict, got a {0}'.format(data.__class__.__name__)
                    raise ValidationError(msg, field=field_obj)
                if raw_value is missing and not field_obj.required:
                    continue
                value = _call_and_store(
                    getter_func=field_obj.deserialize,
                    data=raw_value,
                    field_name=key,
                    field_obj=field_obj,
                    errors_dict=self.errors,
                    exception_class=UnmarshallingError,
                    strict=strict
                )
                if raw_value is not missing:
                    items.append((key, value))
            ret = dict_class(items)
        else:
            ret = None

        if preprocess:
            for func in preprocess:
                ret = func(ret)
        if validators:
            ret = self._validate(validators, ret, fields_dict=fields_dict, strict=strict)
        if postprocess:
            for func in postprocess:
                ret = func(ret)
        return ret

    # Make an instance callable
    __call__ = deserialize


class Field(FieldABC):
    """Basic field from which other fields should extend. It applies no
    formatting by default, and should only be used in cases where
    data does not need to be formatted before being serialized or deserialized.

    :param default: Default serialization value for the field if the attribute is
        `None`. May be a value or a callable.
    :param str attribute: The name of the attribute to get the value from. If
        `None`, assumes the attribute has the same name as the field.
    :param str error: Error message stored upon validation failure.
    :param callable validate: Validator or collection of validators that are called
        during deserialization. Validator takes a field's input value as
        its only parameter and returns a boolean.
        If it returns `False`, an :exc:`UnmarshallingError` is raised.
    :param bool required: Raise an :exc:`UnmarshallingError` if the field value
        is not supplied during deserialization.
    :param metadata: Extra arguments to be stored as metadata.

    .. versionchanged:: 1.0.0
        Deprecated `error` parameter. Raise a :exc:`marshmallow.ValidationError` instead.
    """
    # Some fields, such as Method fields and Function fields, are not expected
    #  to exists as attributes on the objects to serialize. Set this to False
    #  for those fields
    _CHECK_ATTRIBUTE = True
    _creation_index = 0
    #: Values that are skipped by `Marshaller` if ``skip_missing=True``
    SKIPPABLE_VALUES = (None, )

    def __init__(self, default=None, attribute=None, error=None,
                 validate=None, required=False, **metadata):
        self.default = default
        self.attribute = attribute
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
                self.validators = [i for i in validate()]
        elif callable(validate):
            self.validators = [validate]
        elif validate is None:
            self.validators = []
        else:
            raise ValueError("The 'validate' parameter must be a callable "
                            'or a collection of callables.')
        self.required = required
        self.metadata = metadata
        self._creation_index = Field._creation_index
        Field._creation_index += 1
        self.parent = FieldABC.parent

    def __repr__(self):
        return ('<fields.{ClassName}(default={self.default!r}, '
                'attribute={self.attribute!r}, error={self.error!r}, '
                'validate={self.validate}, required={self.required})>'
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
            func_name = utils.get_callable_name(validator)
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

    def _call_and_reraise(self, func, exception_class):
        """Utility method to invoke a function and raise ``exception_class`` if an error
        occurs.

        :param callable func: Function to call. Must take no arguments.
        :param Exception exception_class: Type of exception to raise when an error occurs.
        """
        try:
            return func()
        # TypeErrors should be raised if fields are not declared as instances
        except TypeError:
            raise
        # Raise ForcedErrors
        except ForcedError as err:
            if err.underlying_exception:
                raise err.underlying_exception
            else:
                raise err
        except ValidationError as err:
            raise exception_class(err)
        # Reraise errors, wrapping with exception_class
        # except Exception as error:
        #     raise exception_class(getattr(self, 'error', None) or error)

    def serialize(self, attr, obj, accessor=None):
        """Pulls the value for the given key from the object, applies the
        field's formatting and returns the result.

        :param str attr: The attibute or key to get from the object.
        :param str obj: The object to pull the key from.
        :param callable accessor: Function used to pull values from ``obj``.
        :raise MarshallingError: In case of formatting problem
        """
        value = self.get_value(attr, obj, accessor=accessor)
        if value is None and self._CHECK_ATTRIBUTE:
            if hasattr(self, 'default') and self.default != null:
                if callable(self.default):
                    return self.default()
                else:
                    return self.default
        func = lambda: self._serialize(value, attr, obj)
        return self._call_and_reraise(func, MarshallingError)

    def deserialize(self, value):
        """Deserialize ``value``.

        :raise UnmarshallingError: If an invalid value is passed or if a required value
            is missing.
        """
        # Validate required fields, deserialize, then validate
        # deserialized value
        def do_deserialization():
            if value is missing:
                if hasattr(self, 'required') and self.required:
                    raise ValidationError('Missing data for required field.')
            output = self._deserialize(value)
            self._validate(output)
            return output
        return self._call_and_reraise(do_deserialization, UnmarshallingError)

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
        :raise MarshallingError: In case of formatting or validation failure.
        """
        return value

    def _deserialize(self, value):
        """Deserialize value. Concrete :class:`Field` classes should implement this method.

        :raise UnmarshallingError: In case of formatting or validation failure.
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
    :param bool allow_null: Whether to return None instead of a dictionary
        with null keys, if a nested dictionary has all-null keys
    :param bool many: Whether the field is a collection of objects.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    def __init__(self, nested, default=null, exclude=tuple(), only=None, allow_null=False,
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
                raise ForcedError(ValueError('Nested fields must be passed a '
                                    'Schema, not {0}.'
                                    .format(self.nested.__class__)))
        self.__schema.ordered = getattr(self.parent, 'ordered', False)
        # Inherit context from parent
        self.__schema.context.update(getattr(self.parent, 'context', {}))
        return self.__schema

    def _serialize(self, nested_obj, attr, obj):
        if nested_obj is None:
            if self.many:
                return []
            if self.allow_null:
                return None
        if not self.__updated_fields:
            self.schema._update_fields(obj=nested_obj, many=self.many)
            self.__updated_fields = True
        try:
            ret = self.schema.dump(nested_obj, many=self.many,
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
    """A list field.

    Example: ::

        numbers = fields.List(fields.Float)

    :param Field cls_or_instance: A field class or instance.
    :param bool default: Default value for serialization.
    :param bool allow_none: If `True`, `None` will be serialized to `None`.
        If `False`, `None` will serialize to an empty list.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """
    # Values that are skipped by `Marshaller` if ``skip_missing=True``
    SKIPPABLE_VALUES = (None, [], tuple())

    def __init__(self, cls_or_instance, default=None, allow_none=False, **kwargs):
        super(List, self).__init__(**kwargs)
        if not allow_none and default is None:
            self.default = []
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
        if utils.is_indexable_but_not_string(value) and not isinstance(value, dict):
            return [self.container.serialize(idx, value) for idx
                    in range(len(value))]
        if value is None:
            return self.default
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

    def __init__(self, default='', attribute=None, *args, **kwargs):
        return super(String, self).__init__(default, attribute, *args, **kwargs)

    def _serialize(self, value, attr, obj):
        return utils.ensure_text_type(value)

    def _deserialize(self, value):
        if value is None:
            return ''
        result = utils.ensure_text_type(value)
        return result


class UUID(String):
    """A UUID field."""

    def _deserialize(self, value):
        msg = 'Could not deserialize {0!r} to a UUID object.'.format(value)
        err = UnmarshallingError(getattr(self, 'error', None) or msg)
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError):
            raise err


class Number(Field):
    """Base class for number fields.

    :param bool as_string: If True, format the value as a string.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    num_type = float

    def __init__(self, default=0.0, attribute=None, as_string=False,
                error=None, **kwargs):
        self.as_string = as_string
        super(Number, self).__init__(default=default, attribute=attribute,
            error=error, **kwargs)

    def _format_num(self, value):
        """Return the number value for value, given this field's `num_type`."""
        return self.num_type(value)

    def _validated(self, value, exception_class):
        """Format the value or raise ``exception_class`` if an error occurs."""
        if value is None:
            return self.default
        try:
            return self._format_num(value)
        except (TypeError, ValueError) as err:
            raise exception_class(getattr(self, 'error', None) or err)

    def serialize(self, attr, obj, accessor=None):
        """Pulls the value for the given key from the object and returns the
        serialized number representation. Return a string if `self.as_string=True`,
        othewise return this field's `num_type`. Receives the same `args` and `kwargs`
        as `Field`.
        """
        ret = Field.serialize(self, attr, obj, accessor=accessor)
        return str(ret) if self.as_string else ret

    def _serialize(self, value, attr, obj):
        return self._validated(value, MarshallingError)

    def _deserialize(self, value):
        return self._validated(value, UnmarshallingError)


class Integer(Number):
    """An integer field.

    :param kwargs: The same keyword arguments that :class:`Number` receives.
    """

    num_type = int

    def __init__(self, default=0, *args, **kwargs):
        super(Integer, self).__init__(default=default, *args, **kwargs)


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

    def __init__(self, places=None, rounding=None, default=decimal.Decimal(),
                 as_string=False, **kwargs):
        self.places = decimal.Decimal((0, (1,), -places)) if places is not None else None
        self.rounding = rounding
        super(Decimal, self).__init__(default=default, as_string=as_string, **kwargs)

    # override Number
    def _format_num(self, value):
        num = decimal.Decimal(value)
        if self.places is not None:
            num = num.quantize(self.places, rounding=self.rounding)
        return num

    # override Number
    def _validated(self, value, exception_class):
        try:
            return super(Decimal, self)._validated(value, exception_class)
        except decimal.InvalidOperation:
            raise exception_class(
                getattr(self, 'error', None) or 'Invalid decimal value.'
            )


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
            msg = getattr(self, 'error', None) or text_type(error)
            raise UnmarshallingError(error)
        if value_str in self.falsy:
            return False
        elif self.truthy:
            if value_str in self.truthy:
                return True
            else:
                default_message = '{0!r} is not in {1} nor {2}'.format(
                    value_str, self.truthy, self.falsy
                )
                msg = getattr(self, 'error', None) or default_message
                raise UnmarshallingError(msg)
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
            raise MarshallingError(getattr(self, 'error', None) or error)


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

    .. deprecated:: 1.2.0
        Use `Decimal` instead.
    """
    # No as_string param
    def __init__(self, default='0', attribute=None, **kwargs):
        warnings.warn(
            'The Arbitrary field is deprecated. Use the Decimal field instead.',
            category=DeprecationWarning
        )
        super(Arbitrary, self).__init__(default=default, attribute=attribute, **kwargs)

    def _validated(self, value, exception_class):
        """Format ``value`` or raise ``exception_class`` if an error occurs."""
        try:
            if value is None:
                return self.default
            return text_type(utils.float_to_decimal(float(value)))
        except ValueError as ve:
            raise exception_class(ve)

    def _serialize(self, value, attr, obj):
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

    Example: ``'2014-12-22T03:12:58.019077+00:00'``

    :param str format: Either ``"rfc"`` (for RFC822), ``"iso"`` (for ISO8601),
        or a date format string. If `None`, defaults to "iso".
    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        `None`, assumes the attribute has the same name as the field.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    """
    DEFAULT_FORMAT = 'iso'

    localtime = False

    def __init__(self, format=None, default=None, attribute=None, **kwargs):
        super(DateTime, self).__init__(default=default, attribute=attribute, **kwargs)
        # Allow this to be None. It may be set later in the ``_serialize``
        # or ``_desrialize`` methods This allows a Schema to dynamically set the
        # dateformat, e.g. from a Meta option
        self.dateformat = format

    def _serialize(self, value, attr, obj):
        if value:
            self.dateformat = self.dateformat or self.DEFAULT_FORMAT
            format_func = DATEFORMAT_SERIALIZATION_FUNCS.get(self.dateformat, None)
            if format_func:
                try:
                    return format_func(value, localtime=self.localtime)
                except (AttributeError, ValueError) as err:
                    raise MarshallingError(getattr(self, 'error', None) or err)
            else:
                return value.strftime(self.dateformat)

    def _deserialize(self, value):
        msg = 'Could not deserialize {0!r} to a datetime object.'.format(value)
        err = UnmarshallingError(getattr(self, 'error', None) or msg)
        if not value:  # Falsy values, e.g. '', None, [] are not valid
            raise err
        self.dateformat = self.dateformat or self.DEFAULT_FORMAT
        func = DATEFORMAT_DESERIALIZATION_FUNCS.get(self.dateformat)
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
            raise MarshallingError(getattr(self, 'error', None) or msg)
        if value.microsecond:
            return ret[:12]
        return ret

    def _deserialize(self, value):
        """Deserialize an ISO8601-formatted time to a :class:`datetime.time` object."""
        msg = 'Could not deserialize {0!r} to a time object.'.format(value)
        err = UnmarshallingError(getattr(self, 'error', None) or msg)
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
            raise MarshallingError(getattr(self, 'error', None) or msg)
        return value

    def _deserialize(self, value):
        """Deserialize an ISO8601-formatted date string to a
        :class:`datetime.date` object.
        """
        msg = 'Could not deserialize {0!r} to a date object.'.format(value)
        err = UnmarshallingError(getattr(self, 'error', None) or msg)
        if not value:  # falsy values are invalid
            raise err
        try:
            return utils.from_iso_date(value)
        except (AttributeError, TypeError, ValueError):
            raise err


class TimeDelta(Field):
    """Formats time delta objects, returning the total number of seconds
    as a float.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    def _serialize(self, value, attr, obj):
        try:
            return total_seconds(value)
        except AttributeError:
            msg = '{0} cannot be formatted as a timedelta.'.format(repr(value))
            raise MarshallingError(getattr(self, 'error', None) or msg)
        return value

    def _deserialize(self, value):
        """Deserialize a value in seconds to a :class:`datetime.timedelta`
        object.
        """
        try:
            return dt.timedelta(seconds=float(value))
        except (TypeError, AttributeError, ValueError):
            msg = 'Could not deserialize {0!r} to a timedelta object.'.format(value)
            raise UnmarshallingError(getattr(self, 'error', None) or msg)


class Fixed(Number):
    """A fixed-precision number as a string.

    :param kwargs: The same keyword arguments that :class:`Number` receives.

    .. deprecated:: 1.2.0
        Use `Decimal` instead.
    """

    def __init__(self, decimals=5, default='0.000', attribute=None, error=None,
                 *args, **kwargs):
        warnings.warn(
            'The Fixed field is deprecated. Use the Decimal field instead.',
            category=DeprecationWarning
        )
        super(Fixed, self).__init__(default=default, attribute=attribute, error=error,
                            *args, **kwargs)
        self.precision = decimal.Decimal('0.' + '0' * (decimals - 1) + '1')

    def _serialize(self, value, attr, obj):
        return self._validated(value, MarshallingError)

    def _deserialize(self, value):
        return self._validated(value, UnmarshallingError)

    def _validated(self, value, exception_class):
        if value is None:
            value = self.default
        try:
            dvalue = utils.float_to_decimal(float(value))
        except (TypeError, ValueError) as err:
            raise exception_class(getattr(self, 'error', None) or err)
        if not dvalue.is_normal() and dvalue != utils.ZERO_DECIMAL:
            raise exception_class(
                getattr(self, 'error', None) or 'Invalid Fixed precision number.'
            )
        return utils.decimal_to_fixed(dvalue, self.precision)


class Price(Fixed):
    """A Price field with fixed precision.

    :param kwargs: The same keyword arguments that :class:`Fixed` receives.

    .. deprecated:: 1.2.0
        Use `Decimal` instead.
    """
    def __init__(self, decimals=2, default='0.00', **kwargs):
        warnings.warn(
            'The Price field is deprecated. Use the Decimal field for dealing with '
            'money values.',
            category=DeprecationWarning
        )
        super(Price, self).__init__(decimals=decimals, default=default, **kwargs)

class ValidatedField(Field):
    """A field that validates input on serialization."""

    def _validated(self, value):
        raise NotImplementedError('Must implement _validate method')

    def _serialize(self, value, *args, **kwargs):
        ret = super(ValidatedField, self)._serialize(value, *args, **kwargs)
        return self._validated(ret)

class Url(ValidatedField):
    """A validated URL field.

    :param default: Default value for the field if the attribute is not set.
    :param str attribute: The name of the attribute to get the value from. If
        `None`, assumes the attribute has the same name as the field.
    :param bool relative: Allow relative URLs.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    def __init__(self, default=None, attribute=None, relative=False, *args, **kwargs):
        super(Url, self).__init__(default=default, attribute=attribute,
                *args, **kwargs)
        self.relative = relative
        # Insert validation into self.validators so that multiple errors can be
        # stored.
        self.validators.insert(0, validate.URL(relative=self.relative,
            error=getattr(self, 'error')))

    def _validated(self, value):
        return validate.URL(relative=self.relative, error=getattr(self, 'error'))(value)

URL = Url

class Email(ValidatedField):
    """A validated email field.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """
    def __init__(self, *args, **kwargs):
        super(Email, self).__init__(*args, **kwargs)
        # Insert validation into self.validators so that multiple errors can be
        # stored.
        self.validators.insert(0, validate.Email(error=getattr(self, 'error')))

    def _validated(self, value):
        return validate.Email(error=getattr(self, 'error'))(value)


class Method(Field):
    """A field that takes the value returned by a Schema method.

    :param str method_name: The name of the Schema method from which
        to retrieve the value. The method must take an argument ``obj``
        (in addition to self) that is the object to be serialized. The method
        can also take a ``context`` argument which is a dictionary context
        passed to a Schema.
    :param str deserialize: Optional name of the Schema method for deserializing
        a value The method must take a single argument ``value``, which is the
        value to deserialize.
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
        try:
            method = utils.callable_or_raise(getattr(self.parent, self.method_name, None))
            if len(utils.get_func_args(method)) > 2:
                if self.parent.context is None:
                    msg = 'No context available for Method field {0!r}'.format(attr)
                    raise MarshallingError(msg)
                return method(obj, self.parent.context)
            else:
                return method(obj)
        except AttributeError:
            pass

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
        `None`, assumes the attribute has the same name as the field.
    :param str error: Error message stored upon validation failure.
    :param kwargs: The same keyword arguments that :class:`Fixed` receives.

    :raise: MarshallingError if attribute's value is not one of the given choices.
    """
    def __init__(self, choices, default=None, attribute=None, error=None, **kwargs):
        self.choices = choices
        return super(Select, self).__init__(default, attribute, error, **kwargs)

    def _validated(self, value, exception_class):
        if value not in self.choices:
            raise exception_class(
                getattr(self, 'error', None) or
                "{0!r} is not a valid choice for this field.".format(value)
            )
        return value

    def _serialize(self, value, attr, obj):
        return self._validated(value, MarshallingError)

    def _deserialize(self, value):
        return self._validated(value, UnmarshallingError)


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
    def __init__(self, query, keygetter, error=None, **kwargs):
        self.query = query
        self.keygetter = keygetter if callable(keygetter) else attrgetter(keygetter)
        super(QuerySelect, self).__init__(error=error, **kwargs)

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
        raise MarshallingError(error)

    def _deserialize(self, value):
        for key, result in self.pairs():
            if key == value:
                return result

        error = getattr(self, 'error', None) or 'Invalid key.'
        raise UnmarshallingError(error)


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
                raise MarshallingError(error)

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
                raise UnmarshallingError(error)
            else:
                del keys[index]
                items.append(results.pop(index))

        return items

# Aliases
Enum = Select
Str = String
Bool = Boolean
Int = Integer
