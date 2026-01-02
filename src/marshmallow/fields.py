# ruff: noqa: SLF001
from __future__ import annotations

import abc
import collections
import copy
import datetime as dt
import decimal
import email.utils
import ipaddress
import math
import numbers
import typing
import uuid
from collections.abc import Mapping as _Mapping
from enum import Enum as EnumType

try:
    from typing import Unpack
except ImportError:  # Remove when dropping Python 3.10
    from typing_extensions import Unpack

# Remove when dropping Python 3.10
try:
    from backports.datetime_fromisoformat import MonkeyPatch
except ImportError:
    pass
else:
    MonkeyPatch.patch_fromisoformat()

from marshmallow import class_registry, types, utils, validate
from marshmallow.constants import missing as missing_
from marshmallow.exceptions import (
    StringNotCollectionError,
    ValidationError,
    _FieldInstanceResolutionError,
)
from marshmallow.validate import And, Length

if typing.TYPE_CHECKING:
    from marshmallow.schema import Schema, SchemaMeta


__all__ = [
    "IP",
    "URL",
    "UUID",
    "AwareDateTime",
    "Bool",
    "Boolean",
    "Constant",
    "Date",
    "DateTime",
    "Decimal",
    "Dict",
    "Email",
    "Enum",
    "Field",
    "Float",
    "Function",
    "IPInterface",
    "IPv4",
    "IPv4Interface",
    "IPv6",
    "IPv6Interface",
    "Int",
    "Integer",
    "List",
    "Mapping",
    "Method",
    "NaiveDateTime",
    "Nested",
    "Number",
    "Pluck",
    "Raw",
    "Str",
    "String",
    "Time",
    "TimeDelta",
    "Tuple",
    "Url",
]

_InternalT = typing.TypeVar("_InternalT")


class _BaseFieldKwargs(typing.TypedDict, total=False):
    load_default: typing.Any
    dump_default: typing.Any
    data_key: str | None
    attribute: str | None
    validate: types.Validator | typing.Iterable[types.Validator] | None
    required: bool
    allow_none: bool | None
    load_only: bool
    dump_only: bool
    error_messages: dict[str, str] | None
    metadata: typing.Mapping[str, typing.Any] | None


def _resolve_field_instance(cls_or_instance: Field | type[Field]) -> Field:
    """Return a Field instance from a Field class or instance.

    :param cls_or_instance: Field class or instance.
    """
    if isinstance(cls_or_instance, type):
        if not issubclass(cls_or_instance, Field):
            raise _FieldInstanceResolutionError
        return cls_or_instance()
    if not isinstance(cls_or_instance, Field):
        raise _FieldInstanceResolutionError
    return cls_or_instance


class Field(typing.Generic[_InternalT]):
    """Base field from which all other fields inherit.
    This class should not be used directly within Schemas.

    :param dump_default: If set, this value will be used during serialization if the
        input value is missing. If not set, the field will be excluded from the
        serialized output if the input value is missing. May be a value or a callable.
    :param load_default: Default deserialization value for the field if the field is not
        found in the input data. May be a value or a callable.
    :param data_key: The name of the dict key in the external representation, i.e.
        the input of `load` and the output of `dump`.
        If `None`, the key will match the name of the field.
    :param attribute: The name of the key/attribute in the internal representation, i.e.
        the output of `load` and the input of `dump`.
        If `None`, the key/attribute will match the name of the field.
        Note: This should only be used for very specific use cases such as
        outputting multiple fields for a single attribute, or using keys/attributes
        that are invalid variable names, unsuitable for field names. In most cases,
        you should use ``data_key`` instead.
    :param validate: Validator or collection of validators that are called
        during deserialization. Validator takes a field's input value as
        its only parameter and returns a boolean.
        If it returns `False`, an :exc:`ValidationError` is raised.
    :param required: Raise a :exc:`ValidationError` if the field value
        is not supplied during deserialization.
    :param allow_none: Set this to `True` if `None` should be considered a valid value during
        validation/deserialization. If set to `False` (the default), `None` is considered invalid input.
        If ``load_default`` is explicitly set to `None` and ``allow_none`` is unset,
        `allow_none` is implicitly set to ``True``.
    :param load_only: If `True` skip this field during serialization, otherwise
        its value will be present in the serialized data.
    :param dump_only: If `True` skip this field during deserialization, otherwise
        its value will be present in the deserialized object. In the context of an
        HTTP API, this effectively marks the field as "read-only".
    :param error_messages: Overrides for `Field.default_error_messages`.
    :param metadata: Extra information to be stored as field metadata.

    .. versionchanged:: 3.0.0b8
        Add ``data_key`` parameter for the specifying the key in the input and
        output data. This parameter replaced both ``load_from`` and ``dump_to``.
    .. versionchanged:: 3.13.0
        Replace ``missing`` and ``default`` parameters with ``load_default`` and ``dump_default``.
    .. versionchanged:: 3.24.0
        `Field <marshmallow.fields.Field>` should no longer be used as a field within a `Schema <marshmallow.Schema>`.
        Use `Raw <marshmallow.fields.Raw>` or another `Field <marshmallow.fields.Field>` subclass instead.
    .. versionchanged:: 4.0.0
        Remove ``context`` property.
    """

    # Some fields, such as Method fields and Function fields, are not expected
    #  to exist as attributes on the objects to serialize. Set this to False
    #  for those fields
    _CHECK_ATTRIBUTE = True

    #: Default error messages for various kinds of errors. The keys in this dictionary
    #: are passed to `Field.make_error`. The values are error messages passed to
    #: :exc:`marshmallow.exceptions.ValidationError`.
    default_error_messages: dict[str, str] = {
        "required": "Missing data for required field.",
        "null": "Field may not be null.",
        "validator_failed": "Invalid value.",
    }

    def __init__(
        self,
        *,
        load_default: typing.Any = missing_,
        dump_default: typing.Any = missing_,
        data_key: str | None = None,
        attribute: str | None = None,
        validate: types.Validator | typing.Iterable[types.Validator] | None = None,
        required: bool = False,
        allow_none: bool | None = None,
        load_only: bool = False,
        dump_only: bool = False,
        error_messages: dict[str, str] | None = None,
        metadata: typing.Mapping[str, typing.Any] | None = None,
    ) -> None:
        self.dump_default = dump_default
        self.load_default = load_default

        self.attribute = attribute
        self.data_key = data_key
        self.validate = validate
        if validate is None:
            self.validators = []
        elif callable(validate):
            self.validators = [validate]
        elif utils.is_iterable_but_not_string(validate):
            self.validators = list(validate)
        else:
            raise ValueError(
                "The 'validate' parameter must be a callable "
                "or a collection of callables."
            )

        # If allow_none is None and load_default is None
        # None should be considered valid by default
        self.allow_none = load_default is None if allow_none is None else allow_none
        self.load_only = load_only
        self.dump_only = dump_only
        if required is True and load_default is not missing_:
            raise ValueError("'load_default' must not be set for required fields.")
        self.required = required

        metadata = metadata or {}
        self.metadata = metadata
        # Collect default error message from self and parent classes
        messages: dict[str, str] = {}
        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, "default_error_messages", {}))
        messages.update(error_messages or {})
        self.error_messages = messages

        self.parent: Field | Schema | None = None
        self.name: str | None = None
        self.root: Schema | None = None

    def __repr__(self) -> str:
        return (
            f"<fields.{self.__class__.__name__}(dump_default={self.dump_default!r}, "
            f"attribute={self.attribute!r}, "
            f"validate={self.validate}, required={self.required}, "
            f"load_only={self.load_only}, dump_only={self.dump_only}, "
            f"load_default={self.load_default}, allow_none={self.allow_none}, "
            f"error_messages={self.error_messages})>"
        )

    def __deepcopy__(self, memo):
        return copy.copy(self)

    def get_value(
        self,
        obj: typing.Any,
        attr: str,
        accessor: (
            typing.Callable[[typing.Any, str, typing.Any], typing.Any] | None
        ) = None,
        default: typing.Any = missing_,
    ) -> _InternalT:
        """Return the value for a given key from an object.

        :param obj: The object to get the value from.
        :param attr: The attribute/key in `obj` to get the value from.
        :param accessor: A callable used to retrieve the value of `attr` from
            the object `obj`. Defaults to `marshmallow.utils.get_value`.
        """
        accessor_func = accessor or utils.get_value
        check_key = attr if self.attribute is None else self.attribute
        return accessor_func(obj, check_key, default)

    def _validate(self, value: typing.Any) -> None:
        """Perform validation on ``value``. Raise a :exc:`ValidationError` if validation
        does not succeed.
        """
        self._validate_all(value)

    @property
    def _validate_all(self) -> typing.Callable[[typing.Any], None]:
        return And(*self.validators)

    def make_error(self, key: str, **kwargs) -> ValidationError:
        """Helper method to make a `ValidationError` with an error message
        from ``self.error_messages``.
        """
        try:
            msg = self.error_messages[key]
        except KeyError as error:
            class_name = self.__class__.__name__
            message = (
                f"ValidationError raised by `{class_name}`, but error key `{key}` does "
                "not exist in the `error_messages` dictionary."
            )
            raise AssertionError(message) from error
        if isinstance(msg, (str, bytes)):
            msg = msg.format(**kwargs)
        return ValidationError(msg)

    def _validate_missing(self, value: typing.Any) -> None:
        """Validate missing values. Raise a :exc:`ValidationError` if
        `value` should be considered missing.
        """
        if value is missing_ and self.required:
            raise self.make_error("required")
        if value is None and not self.allow_none:
            raise self.make_error("null")

    def serialize(
        self,
        attr: str,
        obj: typing.Any,
        accessor: (
            typing.Callable[[typing.Any, str, typing.Any], typing.Any] | None
        ) = None,
        **kwargs,
    ):
        """Pulls the value for the given key from the object, applies the
        field's formatting and returns the result.

        :param attr: The attribute/key to get from the object.
        :param obj: The object to access the attribute/key from.
        :param accessor: Function used to access values from ``obj``.
        :param kwargs: Field-specific keyword arguments.
        """
        if self._CHECK_ATTRIBUTE:
            value = self.get_value(obj, attr, accessor=accessor)
            if value is missing_:
                default = self.dump_default
                value = default() if callable(default) else default
            if value is missing_:
                return value
        else:
            value = None
        return self._serialize(value, attr, obj, **kwargs)

    # If value is None, None may be returned
    @typing.overload
    def deserialize(
        self,
        value: None,
        attr: str | None = None,
        data: typing.Mapping[str, typing.Any] | None = None,
        **kwargs,
    ) -> None | _InternalT: ...

    # If value is not None, internal type is returned
    @typing.overload
    def deserialize(
        self,
        value: typing.Any,
        attr: str | None = None,
        data: typing.Mapping[str, typing.Any] | None = None,
        **kwargs,
    ) -> _InternalT: ...

    def deserialize(
        self,
        value: typing.Any,
        attr: str | None = None,
        data: typing.Mapping[str, typing.Any] | None = None,
        **kwargs,
    ) -> _InternalT | None:
        """Deserialize ``value``.

        :param value: The value to deserialize.
        :param attr: The attribute/key in `data` to deserialize.
        :param data: The raw input data passed to `Schema.load <marshmallow.Schema.load>`.
        :param kwargs: Field-specific keyword arguments.
        :raise ValidationError: If an invalid value is passed or if a required value
            is missing.
        """
        # Validate required fields, deserialize, then validate
        # deserialized value
        self._validate_missing(value)
        if value is missing_:
            _miss = self.load_default
            return _miss() if callable(_miss) else _miss
        if self.allow_none and value is None:
            return None
        output = self._deserialize(value, attr, data, **kwargs)
        self._validate(output)
        return output

    # Methods for concrete classes to override.

    def _bind_to_schema(self, field_name: str, parent: Schema | Field) -> None:
        """Update field with values from its parent schema. Called by
                `Schema._bind_field <marshmallow.Schema._bind_field>`.

        :param field_name: Field name set in schema.
        :param parent: Parent object.
        """
        self.parent = self.parent or parent
        self.name = self.name or field_name
        self.root = self.root or (
            self.parent.root if isinstance(self.parent, Field) else self.parent
        )

    def _serialize(
        self, value: _InternalT | None, attr: str | None, obj: typing.Any, **kwargs
    ) -> typing.Any:
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        Example: ::

            class TitleCase(Field):
                def _serialize(self, value, attr, obj, **kwargs):
                    if not value:
                        return ""
                    return str(value).title()

        :param value: The value to be serialized.
        :param attr: The attribute or key on the object to be serialized.
        :param obj: The object the value was pulled from.
        :param kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """
        return value

    def _deserialize(
        self,
        value: typing.Any,
        attr: str | None,
        data: typing.Mapping[str, typing.Any] | None,
        **kwargs,
    ) -> _InternalT:
        """Deserialize value. Concrete :class:`Field` classes should implement this method.

        :param value: The value to be deserialized.
        :param attr: The attribute/key in `data` to be deserialized.
        :param data: The raw input data passed to the `Schema.load <marshmallow.Schema.load>`.
        :param kwargs: Field-specific keyword arguments.
        :raise ValidationError: In case of formatting or validation failure.
        :return: The deserialized value.

        .. versionchanged:: 3.0.0
            Added ``**kwargs`` to signature.
        """
        return value


class Raw(Field[typing.Any]):
    """Field that applies no formatting."""


class Nested(Field):
    """Allows you to nest a :class:`Schema <marshmallow.Schema>`
    inside a field.

    Examples: ::

        class ChildSchema(Schema):
            id = fields.Str()
            name = fields.Str()
            # Use lambda functions when you need two-way nesting or self-nesting
            parent = fields.Nested(lambda: ParentSchema(only=("id",)), dump_only=True)
            siblings = fields.List(
                fields.Nested(lambda: ChildSchema(only=("id", "name")))
            )


        class ParentSchema(Schema):
            id = fields.Str()
            children = fields.List(
                fields.Nested(ChildSchema(only=("id", "parent", "siblings")))
            )
            spouse = fields.Nested(lambda: ParentSchema(only=("id",)))

    When passing a `Schema <marshmallow.Schema>` instance as the first argument,
    the instance's ``exclude``, ``only``, and ``many`` attributes will be respected.

    Therefore, when passing the ``exclude``, ``only``, or ``many`` arguments to `fields.Nested`,
    you should pass a `Schema <marshmallow.Schema>` class (not an instance) as the first argument.

    ::

        # Yes
        author = fields.Nested(UserSchema, only=("id", "name"))

        # No
        author = fields.Nested(UserSchema(), only=("id", "name"))

    :param nested: `Schema <marshmallow.Schema>` instance, class, class name (string), dictionary, or callable that
        returns a `Schema <marshmallow.Schema>` or dictionary.
        Dictionaries are converted with `Schema.from_dict <marshmallow.Schema.from_dict>`.
    :param exclude: A list or tuple of fields to exclude.
    :param only: A list or tuple of fields to marshal. If `None`, all fields are marshalled.
        This parameter takes precedence over ``exclude``.
    :param many: Whether the field is a collection of objects.
        If `None` (default), and nested `Schema` instance is provided, ``many`` is not overridden.
        If `None` (default), and `Schema` subclass is provided, schema instance sets ``many`` as False.
        If `True | False` nested `[nested_field].schema.many` is overridden.
    :param unknown: Whether to exclude, include, or raise an error for unknown
        fields in the data. Use `EXCLUDE`, `INCLUDE` or `RAISE`.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    #: Default error messages.
    default_error_messages = {"type": "Invalid type."}

    def __init__(
        self,
        nested: (
            Schema
            | SchemaMeta
            | str
            | dict[str, Field]
            | typing.Callable[[], Schema | SchemaMeta | dict[str, Field]]
        ),
        *,
        only: types.StrSequenceOrSet | None = None,
        exclude: types.StrSequenceOrSet = (),
        many: bool | None = None,
        unknown: types.UnknownOption | None = None,
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        # Raise error if only or exclude is passed as string, not list of strings
        if only is not None and not utils.is_sequence_but_not_string(only):
            raise StringNotCollectionError('"only" should be a collection of strings.')
        if not utils.is_sequence_but_not_string(exclude):
            raise StringNotCollectionError(
                '"exclude" should be a collection of strings.'
            )
        self.nested = nested
        self.only = only
        self.exclude = exclude
        self.many = many
        self.unknown = unknown
        self._schema: Schema | None = None  # Cached Schema instance
        super().__init__(**kwargs)

    @property
    def schema(self) -> Schema:
        """The nested Schema object."""
        if not self._schema:
            if callable(self.nested) and not isinstance(self.nested, type):
                nested = self.nested()
            else:
                nested = typing.cast("Schema", self.nested)
            # defer the import of `marshmallow.schema` to avoid circular imports
            from marshmallow.schema import Schema  # noqa: PLC0415

            if isinstance(nested, dict):
                nested = Schema.from_dict(nested)

            if isinstance(nested, Schema):
                self._schema = copy.copy(nested)
                # Respect only and exclude and many passed from parent and re-initialize fields
                set_class = typing.cast("type[set]", self._schema.set_class)
                if self.only is not None:
                    if self._schema.only is not None:
                        original = self._schema.only
                    else:  # only=None -> all fields
                        original = self._schema.fields.keys()
                    self._schema.only = set_class(self.only) & set_class(original)
                if self.exclude:
                    original = self._schema.exclude
                    self._schema.exclude = set_class(self.exclude) | set_class(original)
                if self.many is not None:
                    self._schema.many = self.many
                self._schema._init_fields()
            else:
                if isinstance(nested, type) and issubclass(nested, Schema):
                    schema_class: type[Schema] = nested
                elif not isinstance(nested, (str, bytes)):
                    raise ValueError(
                        "`Nested` fields must be passed a "
                        f"`Schema`, not {nested.__class__}."
                    )
                else:
                    schema_class = class_registry.get_class(nested, all=False)
                self._schema = schema_class(
                    many=bool(self.many),
                    only=self.only,
                    exclude=self.exclude,
                    load_only=self._nested_normalized_option("load_only"),
                    dump_only=self._nested_normalized_option("dump_only"),
                )
        return self._schema

    def _nested_normalized_option(self, option_name: str) -> list[str]:
        nested_field = f"{self.name}."
        return [
            field.split(nested_field, 1)[1]
            for field in getattr(self.root, option_name, set())
            if field.startswith(nested_field)
        ]

    def _serialize(self, nested_obj, attr, obj, **kwargs):
        # Load up the schema first. This allows a RegistryError to be raised
        # if an invalid schema name was passed
        schema = self.schema
        if nested_obj is None:
            return None
        many = schema.many or self.many
        return schema.dump(nested_obj, many=many)

    def _test_collection(self, value: typing.Any) -> None:
        many = self.schema.many or self.many
        if many and not utils.is_collection(value):
            raise self.make_error("type", input=value, type=value.__class__.__name__)

    def _load(
        self,
        value: typing.Any,
        partial: bool | types.StrSequenceOrSet | None = None,  # noqa: FBT001
    ):
        try:
            valid_data = self.schema.load(value, unknown=self.unknown, partial=partial)
        except ValidationError as error:
            raise ValidationError(
                error.messages, valid_data=error.valid_data
            ) from error
        return valid_data

    def _deserialize(
        self,
        value: typing.Any,
        attr: str | None,
        data: typing.Mapping[str, typing.Any] | None,
        partial: bool | types.StrSequenceOrSet | None = None,  # noqa: FBT001
        **kwargs,
    ):
        """Same as :meth:`Field._deserialize` with additional ``partial`` argument.

        :param partial: For nested schemas, the ``partial``
            parameter passed to `marshmallow.Schema.load`.

        .. versionchanged:: 3.0.0
            Add ``partial`` parameter.
        """
        self._test_collection(value)
        return self._load(value, partial=partial)


class Pluck(Nested):
    """Allows you to replace nested data with one of the data's fields.

    Example: ::

        from marshmallow import Schema, fields


        class ArtistSchema(Schema):
            id = fields.Int()
            name = fields.Str()


        class AlbumSchema(Schema):
            artist = fields.Pluck(ArtistSchema, "id")


        in_data = {"artist": 42}
        loaded = AlbumSchema().load(in_data)  # => {'artist': {'id': 42}}
        dumped = AlbumSchema().dump(loaded)  # => {'artist': 42}

    :param nested: The Schema class or class name (string) to nest
    :param str field_name: The key to pluck a value from.
    :param kwargs: The same keyword arguments that :class:`Nested` receives.
    """

    def __init__(
        self,
        nested: Schema | SchemaMeta | str | typing.Callable[[], Schema],
        field_name: str,
        *,
        many: bool = False,
        unknown: types.UnknownOption | None = None,
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        super().__init__(
            nested, only=(field_name,), many=many, unknown=unknown, **kwargs
        )
        self.field_name = field_name

    @property
    def _field_data_key(self) -> str:
        only_field = self.schema.fields[self.field_name]
        return only_field.data_key or self.field_name

    def _serialize(self, nested_obj, attr, obj, **kwargs):
        ret = super()._serialize(nested_obj, attr, obj, **kwargs)
        if ret is None:
            return None
        if self.many:
            return utils.pluck(ret, key=self._field_data_key)
        return ret[self._field_data_key]

    def _deserialize(self, value, attr, data, partial=None, **kwargs):
        self._test_collection(value)
        if self.many:
            value = [{self._field_data_key: v} for v in value]
        else:
            value = {self._field_data_key: value}
        return self._load(value, partial=partial)


class List(Field[list[_InternalT | None]]):
    """A list field, composed with another `Field` class or
    instance.

    Example: ::

        numbers = fields.List(fields.Float())

    :param cls_or_instance: A field class or instance.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionchanged:: 3.0.0rc9
        Does not serialize scalar values to single-item lists.
    """

    #: Default error messages.
    default_error_messages = {"invalid": "Not a valid list."}

    def __init__(
        self,
        cls_or_instance: Field[_InternalT] | type[Field[_InternalT]],
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        super().__init__(**kwargs)
        try:
            self.inner: Field[_InternalT] = _resolve_field_instance(cls_or_instance)
        except _FieldInstanceResolutionError as error:
            raise ValueError(
                "The list elements must be a subclass or instance of "
                "marshmallow.fields.Field."
            ) from error
        if isinstance(self.inner, Nested):
            self.only = self.inner.only
            self.exclude = self.inner.exclude

    def _bind_to_schema(self, field_name: str, parent: Schema | Field) -> None:
        super()._bind_to_schema(field_name, parent)
        self.inner = copy.deepcopy(self.inner)
        self.inner._bind_to_schema(field_name, self)
        if isinstance(self.inner, Nested):
            self.inner.only = self.only
            self.inner.exclude = self.exclude

    def _serialize(self, value, attr, obj, **kwargs) -> list[_InternalT] | None:
        if value is None:
            return None
        return [self.inner._serialize(each, attr, obj, **kwargs) for each in value]

    def _deserialize(self, value, attr, data, **kwargs) -> list[_InternalT | None]:
        if not utils.is_collection(value):
            raise self.make_error("invalid")

        result = []
        errors = {}
        for idx, each in enumerate(value):
            try:
                result.append(self.inner.deserialize(each, **kwargs))
            except ValidationError as error:
                if error.valid_data is not None:
                    result.append(typing.cast("_InternalT", error.valid_data))
                errors.update({idx: error.messages})
        if errors:
            raise ValidationError(errors, valid_data=result)
        return result


class Tuple(Field[tuple]):
    """A tuple field, composed of a fixed number of other `Field` classes or
    instances

    Example: ::

        row = Tuple((fields.String(), fields.Integer(), fields.Float()))

    .. note::
        Because of the structured nature of `collections.namedtuple` and
        `typing.NamedTuple`, using a Schema within a Nested field for them is
        more appropriate than using a `Tuple` field.

    :param tuple_fields: An iterable of field classes or
        instances.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionadded:: 3.0.0rc4
    """

    #: Default error messages.
    default_error_messages = {"invalid": "Not a valid tuple."}

    def __init__(
        self,
        tuple_fields: typing.Iterable[Field] | typing.Iterable[type[Field]],
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        super().__init__(**kwargs)
        if not utils.is_collection(tuple_fields):
            raise ValueError(
                "tuple_fields must be an iterable of Field classes or instances."
            )

        try:
            self.tuple_fields = [
                _resolve_field_instance(cls_or_instance)
                for cls_or_instance in tuple_fields
            ]
        except _FieldInstanceResolutionError as error:
            raise ValueError(
                'Elements of "tuple_fields" must be subclasses or '
                "instances of marshmallow.fields.Field."
            ) from error

        self.validate_length = Length(equal=len(self.tuple_fields))

    def _bind_to_schema(self, field_name: str, parent: Schema | Field) -> None:
        super()._bind_to_schema(field_name, parent)
        new_tuple_fields = []
        for field in self.tuple_fields:
            new_field = copy.deepcopy(field)
            new_field._bind_to_schema(field_name, self)
            new_tuple_fields.append(new_field)

        self.tuple_fields = new_tuple_fields

    def _serialize(
        self, value: tuple | None, attr: str | None, obj: typing.Any, **kwargs
    ) -> tuple | None:
        if value is None:
            return None

        return tuple(
            field._serialize(each, attr, obj, **kwargs)
            for field, each in zip(self.tuple_fields, value, strict=True)
        )

    def _deserialize(
        self,
        value: typing.Any,
        attr: str | None,
        data: typing.Mapping[str, typing.Any] | None,
        **kwargs,
    ) -> tuple:
        if not utils.is_sequence_but_not_string(value):
            raise self.make_error("invalid")

        self.validate_length(value)

        result = []
        errors = {}

        for idx, (field, each) in enumerate(zip(self.tuple_fields, value, strict=True)):
            try:
                result.append(field.deserialize(each, **kwargs))
            except ValidationError as error:
                if error.valid_data is not None:
                    result.append(error.valid_data)
                errors.update({idx: error.messages})
        if errors:
            raise ValidationError(errors, valid_data=result)

        return tuple(result)


class String(Field[str]):
    """A string field.

    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    #: Default error messages.
    default_error_messages = {
        "invalid": "Not a valid string.",
        "invalid_utf8": "Not a valid utf-8 string.",
    }

    def _serialize(self, value, attr, obj, **kwargs) -> str | None:
        if value is None:
            return None
        return utils.ensure_text_type(value)

    def _deserialize(self, value, attr, data, **kwargs) -> str:
        if not isinstance(value, (str, bytes)):
            raise self.make_error("invalid")
        try:
            return utils.ensure_text_type(value)
        except UnicodeDecodeError as error:
            raise self.make_error("invalid_utf8") from error


class UUID(Field[uuid.UUID]):
    """A UUID field."""

    #: Default error messages.
    default_error_messages = {"invalid_uuid": "Not a valid UUID."}

    def _validated(self, value) -> uuid.UUID:
        """Format the value or raise a :exc:`ValidationError` if an error occurs."""
        if isinstance(value, uuid.UUID):
            return value
        try:
            if isinstance(value, bytes) and len(value) == 16:
                return uuid.UUID(bytes=value)
            return uuid.UUID(value)
        except (ValueError, AttributeError, TypeError) as error:
            raise self.make_error("invalid_uuid") from error

    def _serialize(self, value, attr, obj, **kwargs) -> str | None:
        if value is None:
            return None
        return str(value)

    def _deserialize(self, value, attr, data, **kwargs) -> uuid.UUID:
        return self._validated(value)


_NumT = typing.TypeVar("_NumT")


class Number(Field[_NumT]):
    """Base class for number fields. This class should not be used within schemas.

    :param as_string: If `True`, format the serialized value as a string.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionchanged:: 3.24.0
        `Number <marshmallow.fields.Number>` should no longer be used as a field within a `Schema <marshmallow.Schema>`.
        Use `Integer <marshmallow.fields.Integer>`, `Float <marshmallow.fields.Float>`, or `Decimal <marshmallow.fields.Decimal>` instead.
    """

    num_type: type[_NumT]

    #: Default error messages.
    default_error_messages = {
        "invalid": "Not a valid number.",
        "too_large": "Number too large.",
    }

    def __init__(self, *, as_string: bool = False, **kwargs: Unpack[_BaseFieldKwargs]):
        self.as_string = as_string
        super().__init__(**kwargs)

    def _format_num(self, value) -> _NumT:
        """Return the number value for value, given this field's `num_type`."""
        return self.num_type(value)  # type: ignore[call-arg]

    def _validated(self, value: typing.Any) -> _NumT:
        """Format the value or raise a :exc:`ValidationError` if an error occurs."""
        # (value is True or value is False) is ~5x faster than isinstance(value, bool)
        if value is True or value is False:
            raise self.make_error("invalid", input=value)
        try:
            return self._format_num(value)
        except (TypeError, ValueError) as error:
            raise self.make_error("invalid", input=value) from error
        except OverflowError as error:
            raise self.make_error("too_large", input=value) from error

    def _to_string(self, value: _NumT) -> str:
        return str(value)

    def _serialize(self, value, attr, obj, **kwargs) -> str | _NumT | None:
        """Return a string if `self.as_string=True`, otherwise return this field's `num_type`."""
        if value is None:
            return None
        ret: _NumT = self._format_num(value)
        return self._to_string(ret) if self.as_string else ret

    def _deserialize(self, value, attr, data, **kwargs) -> _NumT:
        return self._validated(value)


class Integer(Number[int]):
    """An integer field.

    :param strict: If `True`, only integer types are valid.
        Otherwise, any value castable to `int` is valid.
    :param kwargs: The same keyword arguments that :class:`Number` receives.
    """

    num_type = int

    #: Default error messages.
    default_error_messages = {"invalid": "Not a valid integer."}

    def __init__(
        self,
        *,
        strict: bool = False,
        as_string: bool = False,
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        self.strict = strict
        super().__init__(as_string=as_string, **kwargs)

    # override Number
    def _validated(self, value: typing.Any) -> int:
        if self.strict and not isinstance(value, numbers.Integral):
            raise self.make_error("invalid", input=value)
        return super()._validated(value)


class Float(Number[float]):
    """A double as an IEEE-754 double precision string.

    :param allow_nan: If `True`, `NaN`, `Infinity` and `-Infinity` are allowed,
        even though they are illegal according to the JSON specification.
    :param as_string: If `True`, format the value as a string.
    :param kwargs: The same keyword arguments that :class:`Number` receives.
    """

    num_type = float

    #: Default error messages.
    default_error_messages = {
        "special": "Special numeric values (nan or infinity) are not permitted."
    }

    def __init__(
        self,
        *,
        allow_nan: bool = False,
        as_string: bool = False,
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        self.allow_nan = allow_nan
        super().__init__(as_string=as_string, **kwargs)

    def _validated(self, value: typing.Any) -> float:
        num = super()._validated(value)
        if self.allow_nan is False:
            if math.isnan(num) or num == float("inf") or num == float("-inf"):
                raise self.make_error("special")
        return num


class Decimal(Number[decimal.Decimal]):
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

    :param places: How many decimal places to quantize the value. If `None`, does
        not quantize the value.
    :param rounding: How to round the value during quantize, for example
        `decimal.ROUND_UP`. If `None`, uses the rounding value from
        the current thread's context.
    :param allow_nan: If `True`, `NaN`, `Infinity` and `-Infinity` are allowed,
        even though they are illegal according to the JSON specification.
    :param as_string: If `True`, serialize to a string instead of a Python
        `decimal.Decimal` type.
    :param kwargs: The same keyword arguments that :class:`Number` receives.
    """

    num_type = decimal.Decimal

    #: Default error messages.
    default_error_messages = {
        "special": "Special numeric values (nan or infinity) are not permitted."
    }

    def __init__(
        self,
        places: int | None = None,
        rounding: str | None = None,
        *,
        allow_nan: bool = False,
        as_string: bool = False,
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        self.places = (
            decimal.Decimal((0, (1,), -places)) if places is not None else None
        )
        self.rounding = rounding
        self.allow_nan = allow_nan
        super().__init__(as_string=as_string, **kwargs)

    # override Number
    def _format_num(self, value):
        num = decimal.Decimal(str(value))
        if self.allow_nan:
            if num.is_nan():
                return decimal.Decimal("NaN")  # avoid sNaN, -sNaN and -NaN
        if self.places is not None and num.is_finite():
            num = num.quantize(self.places, rounding=self.rounding)
        return num

    # override Number
    def _validated(self, value: typing.Any) -> decimal.Decimal:
        try:
            num = super()._validated(value)
        except decimal.InvalidOperation as error:
            raise self.make_error("invalid") from error
        if not self.allow_nan and (num.is_nan() or num.is_infinite()):
            raise self.make_error("special")
        return num

    # override Number
    def _to_string(self, value: decimal.Decimal) -> str:
        return format(value, "f")


class Boolean(Field[bool]):
    """A boolean field.

    :param truthy: Values that will (de)serialize to `True`. If an empty
        set, any non-falsy value will deserialize to `True`. If `None`,
        `marshmallow.fields.Boolean.truthy` will be used.
    :param falsy: Values that will (de)serialize to `False`. If `None`,
        `marshmallow.fields.Boolean.falsy` will be used.
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    #: Default truthy values.
    truthy = {
        "t",
        "T",
        "true",
        "True",
        "TRUE",
        "on",
        "On",
        "ON",
        "y",
        "Y",
        "yes",
        "Yes",
        "YES",
        "1",
        1,
        # Equal to 1
        # True,
    }
    #: Default falsy values.
    falsy = {
        "f",
        "F",
        "false",
        "False",
        "FALSE",
        "off",
        "Off",
        "OFF",
        "n",
        "N",
        "no",
        "No",
        "NO",
        "0",
        0,
        # Equal to 0
        # 0.0,
        # False,
    }

    #: Default error messages.
    default_error_messages = {"invalid": "Not a valid boolean."}

    def __init__(
        self,
        *,
        truthy: typing.Iterable | None = None,
        falsy: typing.Iterable | None = None,
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        super().__init__(**kwargs)

        if truthy is not None:
            self.truthy = set(truthy)
        if falsy is not None:
            self.falsy = set(falsy)

    def _deserialize(
        self,
        value: typing.Any,
        attr: str | None,
        data: typing.Mapping[str, typing.Any] | None,
        **kwargs,
    ) -> bool:
        if not self.truthy:
            return bool(value)
        try:
            if value in self.truthy:
                return True
            if value in self.falsy:
                return False
        except TypeError as error:
            raise self.make_error("invalid", input=value) from error
        raise self.make_error("invalid", input=value)


_D = typing.TypeVar("_D", dt.datetime, dt.date, dt.time)


class _TemporalField(Field[_D], metaclass=abc.ABCMeta):
    """Base field for date and time related fields including common (de)serialization logic."""

    # Subclasses should define each of these class constants
    SERIALIZATION_FUNCS: dict[str, typing.Callable[[_D], str | float]]
    DESERIALIZATION_FUNCS: dict[str, typing.Callable[[str], _D]]
    DEFAULT_FORMAT: str
    OBJ_TYPE: str
    SCHEMA_OPTS_VAR_NAME: str

    default_error_messages = {
        "invalid": "Not a valid {obj_type}.",
        "invalid_awareness": "Not a valid {awareness} {obj_type}.",
        "format": '"{input}" cannot be formatted as a {obj_type}.',
    }

    def __init__(
        self,
        format: str | None = None,  # noqa: A002
        **kwargs: Unpack[_BaseFieldKwargs],
    ) -> None:
        super().__init__(**kwargs)
        # Allow this to be None. It may be set later in the ``_serialize``
        # or ``_deserialize`` methods. This allows a Schema to dynamically set the
        # format, e.g. from a Meta option
        self.format = format

    def _bind_to_schema(self, field_name, parent):
        super()._bind_to_schema(field_name, parent)
        self.format = (
            self.format
            or getattr(self.root.opts, self.SCHEMA_OPTS_VAR_NAME)
            or self.DEFAULT_FORMAT
        )

    def _serialize(self, value: _D | None, attr, obj, **kwargs) -> str | float | None:
        if value is None:
            return None
        data_format = self.format or self.DEFAULT_FORMAT
        format_func = self.SERIALIZATION_FUNCS.get(data_format)
        if format_func:
            return format_func(value)
        return value.strftime(data_format)

    def _deserialize(self, value, attr, data, **kwargs) -> _D:
        internal_type: type[_D] = getattr(dt, self.OBJ_TYPE)
        if isinstance(value, internal_type):
            return value
        data_format = self.format or self.DEFAULT_FORMAT
        func = self.DESERIALIZATION_FUNCS.get(data_format)
        try:
            if func:
                return func(value)
            return self._make_object_from_format(value, data_format)
        except (TypeError, AttributeError, ValueError) as error:
            raise self.make_error(
                "invalid", input=value, obj_type=self.OBJ_TYPE
            ) from error

    @staticmethod
    @abc.abstractmethod
    def _make_object_from_format(value: typing.Any, data_format: str) -> _D: ...


class DateTime(_TemporalField[dt.datetime]):
    """A formatted datetime string.

    Example: ``'2014-12-22T03:12:58.019077+00:00'``

    :param format: Either ``"rfc"`` (for RFC822), ``"iso"`` (for ISO8601),
        ``"timestamp"``, ``"timestamp_ms"`` (for a POSIX timestamp) or a date format string.
        If `None`, defaults to "iso".
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionchanged:: 3.0.0rc9
        Does not modify timezone information on (de)serialization.
    .. versionchanged:: 3.19
        Add timestamp as a format.
    """

    SERIALIZATION_FUNCS: dict[str, typing.Callable[[dt.datetime], str | float]] = {
        "iso": dt.datetime.isoformat,
        "iso8601": dt.datetime.isoformat,
        "rfc": email.utils.format_datetime,
        "rfc822": email.utils.format_datetime,
        "timestamp": utils.timestamp,
        "timestamp_ms": utils.timestamp_ms,
    }

    DESERIALIZATION_FUNCS: dict[str, typing.Callable[[str], dt.datetime]] = {
        "iso": dt.datetime.fromisoformat,
        "iso8601": dt.datetime.fromisoformat,
        "rfc": email.utils.parsedate_to_datetime,
        "rfc822": email.utils.parsedate_to_datetime,
        "timestamp": utils.from_timestamp,
        "timestamp_ms": utils.from_timestamp_ms,
    }

    DEFAULT_FORMAT = "iso"

    OBJ_TYPE = "datetime"

    SCHEMA_OPTS_VAR_NAME = "datetimeformat"

    @staticmethod
    def _make_object_from_format(value, data_format) -> dt.datetime:
        return dt.datetime.strptime(value, data_format)


class NaiveDateTime(DateTime):
    """A formatted naive datetime string.

    :param format: See :class:`DateTime`.
    :param timezone: Used on deserialization. If `None`,
        aware datetimes are rejected. If not `None`, aware datetimes are
        converted to this timezone before their timezone information is
        removed.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionadded:: 3.0.0rc9
    """

    AWARENESS = "naive"

    def __init__(
        self,
        format: str | None = None,  # noqa: A002
        *,
        timezone: dt.timezone | None = None,
        **kwargs: Unpack[_BaseFieldKwargs],
    ) -> None:
        super().__init__(format=format, **kwargs)
        self.timezone = timezone

    def _deserialize(self, value, attr, data, **kwargs) -> dt.datetime:
        ret = super()._deserialize(value, attr, data, **kwargs)
        if utils.is_aware(ret):
            if self.timezone is None:
                raise self.make_error(
                    "invalid_awareness",
                    awareness=self.AWARENESS,
                    obj_type=self.OBJ_TYPE,
                )
            ret = ret.astimezone(self.timezone).replace(tzinfo=None)
        return ret


class AwareDateTime(DateTime):
    """A formatted aware datetime string.

    :param format: See :class:`DateTime`.
    :param default_timezone: Used on deserialization. If `None`, naive
        datetimes are rejected. If not `None`, naive datetimes are set this
        timezone.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. versionadded:: 3.0.0rc9
    """

    AWARENESS = "aware"

    def __init__(
        self,
        format: str | None = None,  # noqa: A002
        *,
        default_timezone: dt.tzinfo | None = None,
        **kwargs: Unpack[_BaseFieldKwargs],
    ) -> None:
        super().__init__(format=format, **kwargs)
        self.default_timezone = default_timezone

    def _deserialize(self, value, attr, data, **kwargs) -> dt.datetime:
        ret = super()._deserialize(value, attr, data, **kwargs)
        if not utils.is_aware(ret):
            if self.default_timezone is None:
                raise self.make_error(
                    "invalid_awareness",
                    awareness=self.AWARENESS,
                    obj_type=self.OBJ_TYPE,
                )
            ret = ret.replace(tzinfo=self.default_timezone)
        return ret


class Time(_TemporalField[dt.time]):
    """A formatted time string.

    Example: ``'03:12:58.019077'``

    :param format: Either ``"iso"`` (for ISO8601) or a date format string.
        If `None`, defaults to "iso".
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    SERIALIZATION_FUNCS = {
        "iso": dt.time.isoformat,
        "iso8601": dt.time.isoformat,
    }

    DESERIALIZATION_FUNCS = {
        "iso": dt.time.fromisoformat,
        "iso8601": dt.time.fromisoformat,
    }

    DEFAULT_FORMAT = "iso"

    OBJ_TYPE = "time"

    SCHEMA_OPTS_VAR_NAME = "timeformat"

    @staticmethod
    def _make_object_from_format(value, data_format):
        return dt.datetime.strptime(value, data_format).time()


class Date(_TemporalField[dt.date]):
    """ISO8601-formatted date string.

    :param format: Either ``"iso"`` (for ISO8601) or a date format string.
        If `None`, defaults to "iso".
    :param kwargs: The same keyword arguments that :class:`Field` receives.
    """

    #: Default error messages.
    default_error_messages = {
        "invalid": "Not a valid date.",
        "format": '"{input}" cannot be formatted as a date.',
    }

    SERIALIZATION_FUNCS = {
        "iso": dt.date.isoformat,
        "iso8601": dt.date.isoformat,
    }

    DESERIALIZATION_FUNCS = {
        "iso": dt.date.fromisoformat,
        "iso8601": dt.date.fromisoformat,
    }

    DEFAULT_FORMAT = "iso"

    OBJ_TYPE = "date"

    SCHEMA_OPTS_VAR_NAME = "dateformat"

    @staticmethod
    def _make_object_from_format(value, data_format):
        return dt.datetime.strptime(value, data_format).date()


class TimeDelta(Field[dt.timedelta]):
    """A field that (de)serializes a :class:`datetime.timedelta` object to a `float`.
    The `float` can represent any time unit that the :class:`datetime.timedelta` constructor
    supports.

    :param precision: The time unit used for (de)serialization. Must be one of 'weeks',
        'days', 'hours', 'minutes', 'seconds', 'milliseconds' or 'microseconds'.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    Float Caveats
    -------------
    Precision loss may occur when serializing a highly precise :class:`datetime.timedelta`
    object using a big ``precision`` unit due to floating point arithmetics.

    When necessary, the :class:`datetime.timedelta` constructor rounds `float` inputs
    to whole microseconds during initialization of the object. As a result, deserializing
    a `float` might be subject to rounding, regardless of `precision`. For example,
    ``TimeDelta().deserialize("1.1234567") == timedelta(seconds=1, microseconds=123457)``.

    .. versionchanged:: 3.17.0
        Allow serialization to `float` through use of a new `serialization_type` parameter.
        Defaults to `int` for backwards compatibility. Also affects deserialization.
    .. versionchanged:: 4.0.0
        Remove `serialization_type` parameter and always serialize to float.
        Value is cast to a `float` upon deserialization.
    """

    WEEKS = "weeks"
    DAYS = "days"
    HOURS = "hours"
    MINUTES = "minutes"
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    MICROSECONDS = "microseconds"

    # cache this mapping on class level for performance
    _unit_to_microseconds_mapping = {
        WEEKS: 1000000 * 60 * 60 * 24 * 7,
        DAYS: 1000000 * 60 * 60 * 24,
        HOURS: 1000000 * 60 * 60,
        MINUTES: 1000000 * 60,
        SECONDS: 1000000,
        MILLISECONDS: 1000,
        MICROSECONDS: 1,
    }

    #: Default error messages.
    default_error_messages = {
        "invalid": "Not a valid period of time.",
        "format": "{input!r} cannot be formatted as a timedelta.",
    }

    def __init__(
        self,
        precision: str = SECONDS,
        **kwargs: Unpack[_BaseFieldKwargs],
    ) -> None:
        precision = precision.lower()

        if precision not in self._unit_to_microseconds_mapping:
            units = ", ".join(self._unit_to_microseconds_mapping)
            msg = f"The precision must be one of: {units}."
            raise ValueError(msg)

        self.precision = precision
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs) -> float | None:
        if value is None:
            return None

        # limit float arithmetics to a single division to minimize precision loss
        microseconds: int = utils.timedelta_to_microseconds(value)
        microseconds_per_unit: int = self._unit_to_microseconds_mapping[self.precision]
        return microseconds / microseconds_per_unit

    def _deserialize(self, value, attr, data, **kwargs) -> dt.timedelta:
        if isinstance(value, dt.timedelta):
            return value
        try:
            value = float(value)
        except (TypeError, ValueError) as error:
            raise self.make_error("invalid") from error

        kwargs = {self.precision: value}

        try:
            return dt.timedelta(**kwargs)
        except OverflowError as error:
            raise self.make_error("invalid") from error


_MappingT = typing.TypeVar("_MappingT", bound=_Mapping)


class Mapping(Field[_MappingT]):
    """An abstract class for objects with key-value pairs. This class should not be used within schemas.

    :param keys: A field class or instance for dict keys.
    :param values: A field class or instance for dict values.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. note::
        When the structure of nested data is not known, you may omit the
        `keys` and `values` arguments to prevent content validation.

    .. versionadded:: 3.0.0rc4
    .. versionchanged:: 3.24.0
        `Mapping <marshmallow.fields.Mapping>` should no longer be used as a field within a `Schema <marshmallow.Schema>`.
        Use `Dict <marshmallow.fields.Dict>` instead.
    """

    mapping_type: type[_MappingT]

    #: Default error messages.
    default_error_messages = {"invalid": "Not a valid mapping type."}

    def __init__(
        self,
        keys: Field | type[Field] | None = None,
        values: Field | type[Field] | None = None,
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        super().__init__(**kwargs)
        if keys is None:
            self.key_field = None
        else:
            try:
                self.key_field = _resolve_field_instance(keys)
            except _FieldInstanceResolutionError as error:
                raise ValueError(
                    '"keys" must be a subclass or instance of marshmallow.fields.Field.'
                ) from error

        if values is None:
            self.value_field = None
        else:
            try:
                self.value_field = _resolve_field_instance(values)
            except _FieldInstanceResolutionError as error:
                raise ValueError(
                    '"values" must be a subclass or instance of '
                    "marshmallow.fields.Field."
                ) from error
            if isinstance(self.value_field, Nested):
                self.only = self.value_field.only
                self.exclude = self.value_field.exclude

    def _bind_to_schema(self, field_name, parent):
        super()._bind_to_schema(field_name, parent)
        if self.value_field:
            self.value_field = copy.deepcopy(self.value_field)
            self.value_field._bind_to_schema(field_name, self)
        if isinstance(self.value_field, Nested):
            self.value_field.only = self.only
            self.value_field.exclude = self.exclude
        if self.key_field:
            self.key_field = copy.deepcopy(self.key_field)
            self.key_field._bind_to_schema(field_name, self)

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        if not self.value_field and not self.key_field:
            return self.mapping_type(value)

        # Serialize keys
        if self.key_field is None:
            keys = {k: k for k in value}
        else:
            keys = {
                k: self.key_field._serialize(k, None, None, **kwargs) for k in value
            }

        # Serialize values
        result = self.mapping_type()
        if self.value_field is None:
            for k, v in value.items():
                if k in keys:
                    result[keys[k]] = v
        else:
            for k, v in value.items():
                result[keys[k]] = self.value_field._serialize(v, None, None, **kwargs)

        return result

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, _Mapping):
            raise self.make_error("invalid")
        if not self.value_field and not self.key_field:
            return self.mapping_type(value)

        errors = collections.defaultdict(dict)

        # Deserialize keys
        if self.key_field is None:
            keys = {k: k for k in value}
        else:
            keys = {}
            for key in value:
                try:
                    keys[key] = self.key_field.deserialize(key, **kwargs)
                except ValidationError as error:
                    errors[key]["key"] = error.messages

        # Deserialize values
        result = self.mapping_type()
        if self.value_field is None:
            for k, v in value.items():
                if k in keys:
                    result[keys[k]] = v
        else:
            for key, val in value.items():
                try:
                    deser_val = self.value_field.deserialize(val, **kwargs)
                except ValidationError as error:
                    errors[key]["value"] = error.messages
                    if error.valid_data is not None and key in keys:
                        result[keys[key]] = error.valid_data
                else:
                    if key in keys:
                        result[keys[key]] = deser_val

        if errors:
            raise ValidationError(errors, valid_data=result)

        return result


class Dict(Mapping[dict]):
    """A dict field. Supports dicts and dict-like objects

    Example: ::

        numbers = fields.Dict(keys=fields.Str(), values=fields.Float())

    :param kwargs: The same keyword arguments that :class:`Mapping` receives.

    .. versionadded:: 2.1.0
    """

    mapping_type = dict


class Url(String):
    """An URL field.

    :param default: Default value for the field if the attribute is not set.
    :param relative: Whether to allow relative URLs.
    :param absolute: Whether to allow absolute URLs.
    :param require_tld: Whether to reject non-FQDN hostnames.
    :param schemes: Valid schemes. By default, ``http``, ``https``,
        ``ftp``, and ``ftps`` are allowed.
    :param kwargs: The same keyword arguments that :class:`String` receives.
    """

    #: Default error messages.
    default_error_messages = {"invalid": "Not a valid URL."}

    def __init__(
        self,
        *,
        relative: bool = False,
        absolute: bool = True,
        schemes: types.StrSequenceOrSet | None = None,
        require_tld: bool = True,
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        super().__init__(**kwargs)

        self.relative = relative
        self.absolute = absolute
        self.require_tld = require_tld
        # Insert validation into self.validators so that multiple errors can be stored.
        validator = validate.URL(
            relative=self.relative,
            absolute=self.absolute,
            schemes=schemes,
            require_tld=self.require_tld,
            error=self.error_messages["invalid"],
        )
        self.validators.insert(0, validator)


class Email(String):
    """An email field.

    :param args: The same positional arguments that :class:`String` receives.
    :param kwargs: The same keyword arguments that :class:`String` receives.
    """

    #: Default error messages.
    default_error_messages = {"invalid": "Not a valid email address."}

    def __init__(self, **kwargs: Unpack[_BaseFieldKwargs]) -> None:
        super().__init__(**kwargs)
        # Insert validation into self.validators so that multiple errors can be stored.
        validator = validate.Email(error=self.error_messages["invalid"])
        self.validators.insert(0, validator)


class IP(Field[ipaddress.IPv4Address | ipaddress.IPv6Address]):
    """A IP address field.

    :param exploded: If `True`, serialize ipv6 address in long form, ie. with groups
        consisting entirely of zeros included.

    .. versionadded:: 3.8.0
    """

    default_error_messages = {"invalid_ip": "Not a valid IP address."}

    DESERIALIZATION_CLASS: type | None = None

    def __init__(self, *, exploded: bool = False, **kwargs: Unpack[_BaseFieldKwargs]):
        super().__init__(**kwargs)
        self.exploded = exploded

    def _serialize(self, value, attr, obj, **kwargs) -> str | None:
        if value is None:
            return None
        if self.exploded:
            return value.exploded
        return value.compressed

    def _deserialize(
        self, value, attr, data, **kwargs
    ) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        try:
            return (self.DESERIALIZATION_CLASS or ipaddress.ip_address)(
                utils.ensure_text_type(value)
            )
        except (ValueError, TypeError) as error:
            raise self.make_error("invalid_ip") from error


class IPv4(IP):
    """A IPv4 address field.

    .. versionadded:: 3.8.0
    """

    default_error_messages = {"invalid_ip": "Not a valid IPv4 address."}

    DESERIALIZATION_CLASS = ipaddress.IPv4Address


class IPv6(IP):
    """A IPv6 address field.

    .. versionadded:: 3.8.0
    """

    default_error_messages = {"invalid_ip": "Not a valid IPv6 address."}

    DESERIALIZATION_CLASS = ipaddress.IPv6Address


class IPInterface(Field[ipaddress.IPv4Interface | ipaddress.IPv6Interface]):
    """A IPInterface field.

    IP interface is the non-strict form of the IPNetwork type where arbitrary host
    addresses are always accepted.

    IPAddress and mask e.g. '192.168.0.2/24' or '192.168.0.2/255.255.255.0'

    see https://python.readthedocs.io/en/latest/library/ipaddress.html#interface-objects

    :param exploded: If `True`, serialize ipv6 interface in long form, ie. with groups
        consisting entirely of zeros included.
    """

    default_error_messages = {"invalid_ip_interface": "Not a valid IP interface."}

    DESERIALIZATION_CLASS: type | None = None

    def __init__(self, *, exploded: bool = False, **kwargs: Unpack[_BaseFieldKwargs]):
        super().__init__(**kwargs)
        self.exploded = exploded

    def _serialize(self, value, attr, obj, **kwargs) -> str | None:
        if value is None:
            return None
        if self.exploded:
            return value.exploded
        return value.compressed

    def _deserialize(
        self, value, attr, data, **kwargs
    ) -> ipaddress.IPv4Interface | ipaddress.IPv6Interface:
        try:
            return (self.DESERIALIZATION_CLASS or ipaddress.ip_interface)(
                utils.ensure_text_type(value)
            )
        except (ValueError, TypeError) as error:
            raise self.make_error("invalid_ip_interface") from error


class IPv4Interface(IPInterface):
    """A IPv4 Network Interface field."""

    default_error_messages = {"invalid_ip_interface": "Not a valid IPv4 interface."}

    DESERIALIZATION_CLASS = ipaddress.IPv4Interface


class IPv6Interface(IPInterface):
    """A IPv6 Network Interface field."""

    default_error_messages = {"invalid_ip_interface": "Not a valid IPv6 interface."}

    DESERIALIZATION_CLASS = ipaddress.IPv6Interface


_EnumT = typing.TypeVar("_EnumT", bound=EnumType)


class Enum(Field[_EnumT]):
    """An Enum field (de)serializing enum members by symbol (name) or by value.

    :param enum: Enum class
    :param by_value: Whether to (de)serialize by value or by name,
        or Field class or instance to use to (de)serialize by value. Defaults to False.

    If `by_value` is `False` (default), enum members are (de)serialized by symbol (name).
    If it is `True`, they are (de)serialized by value using `marshmallow.fields.Raw`.
    If it is a field instance or class, they are (de)serialized by value using this field.

    .. versionadded:: 3.18.0
    """

    default_error_messages = {
        "unknown": "Must be one of: {choices}.",
    }

    def __init__(
        self,
        enum: type[_EnumT],
        *,
        by_value: bool | Field | type[Field] = False,
        **kwargs: Unpack[_BaseFieldKwargs],
    ):
        super().__init__(**kwargs)
        self.enum = enum
        self.by_value = by_value

        # Serialization by name
        if by_value is False:
            self.field: Field = String()
            self.choices_text = ", ".join(
                str(self.field._serialize(m, None, None)) for m in enum.__members__
            )
        # Serialization by value
        else:
            if by_value is True:
                self.field = Raw()
            else:
                try:
                    self.field = _resolve_field_instance(by_value)
                except _FieldInstanceResolutionError as error:
                    raise ValueError(
                        '"by_value" must be either a bool or a subclass or instance of '
                        "marshmallow.fields.Field."
                    ) from error
            self.choices_text = ", ".join(
                str(self.field._serialize(m.value, None, None)) for m in enum
            )

    def _serialize(
        self, value: _EnumT | None, attr: str | None, obj: typing.Any, **kwargs
    ) -> typing.Any | None:
        if value is None:
            return None
        if self.by_value:
            val = value.value
        else:
            val = value.name
        return self.field._serialize(val, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs) -> _EnumT:
        if isinstance(value, self.enum):
            return value
        val = self.field._deserialize(value, attr, data, **kwargs)
        if self.by_value:
            try:
                return self.enum(val)
            except ValueError as error:
                raise self.make_error("unknown", choices=self.choices_text) from error
        try:
            return getattr(self.enum, val)
        except AttributeError as error:
            raise self.make_error("unknown", choices=self.choices_text) from error


class Method(Field):
    """A field that takes the value returned by a `Schema <marshmallow.Schema>` method.

    :param serialize: The name of the Schema method from which
        to retrieve the value. The method must take an argument ``obj``
        (in addition to self) that is the object to be serialized.
    :param deserialize: Optional name of the Schema method for deserializing
        a value The method must take a single argument ``value``, which is the
        value to deserialize.

    .. versionchanged:: 3.0.0
        Removed ``method_name`` parameter.
    """

    _CHECK_ATTRIBUTE = False

    def __init__(
        self,
        serialize: str | None = None,
        deserialize: str | None = None,
        **kwargs: Unpack[_BaseFieldKwargs],  # FIXME: Omit dump_only and load_only
    ):
        # Set dump_only and load_only based on arguments
        kwargs["dump_only"] = bool(serialize) and not bool(deserialize)
        kwargs["load_only"] = bool(deserialize) and not bool(serialize)
        super().__init__(**kwargs)
        self.serialize_method_name = serialize
        self.deserialize_method_name = deserialize
        self._serialize_method = None
        self._deserialize_method = None

    def _bind_to_schema(self, field_name, parent):
        if self.serialize_method_name:
            self._serialize_method = utils.callable_or_raise(
                getattr(parent, self.serialize_method_name)
            )

        if self.deserialize_method_name:
            self._deserialize_method = utils.callable_or_raise(
                getattr(parent, self.deserialize_method_name)
            )

        super()._bind_to_schema(field_name, parent)

    def _serialize(self, value, attr, obj, **kwargs):
        if self._serialize_method is not None:
            return self._serialize_method(obj)
        return missing_

    def _deserialize(self, value, attr, data, **kwargs):
        if self._deserialize_method is not None:
            return self._deserialize_method(value)
        return value


class Function(Field):
    """A field that takes the value returned by a function.

    :param serialize: A callable from which to retrieve the value.
        The function must take a single argument ``obj`` which is the object
        to be serialized.
        If no callable is provided then the ```load_only``` flag will be set
        to True.
    :param deserialize: A callable from which to retrieve the value.
        The function must take a single argument ``value`` which is the value
        to be deserialized.
        If no callable is provided then ```value``` will be passed through
        unchanged.

    .. versionchanged:: 3.0.0a1
        Removed ``func`` parameter.

    .. versionchanged:: 4.0.0
        Don't pass context to serialization and deserialization functions.
    """

    _CHECK_ATTRIBUTE = False

    def __init__(
        self,
        serialize: (
            typing.Callable[[typing.Any], typing.Any]
            | typing.Callable[[typing.Any, dict], typing.Any]
            | None
        ) = None,
        deserialize: (
            typing.Callable[[typing.Any], typing.Any]
            | typing.Callable[[typing.Any, dict], typing.Any]
            | None
        ) = None,
        **kwargs: Unpack[_BaseFieldKwargs],  # FIXME: Omit dump_only and load_only
    ):
        # Set dump_only and load_only based on arguments
        kwargs["dump_only"] = bool(serialize) and not bool(deserialize)
        kwargs["load_only"] = bool(deserialize) and not bool(serialize)
        super().__init__(**kwargs)
        self.serialize_func = serialize and utils.callable_or_raise(serialize)
        self.deserialize_func = deserialize and utils.callable_or_raise(deserialize)

    def _serialize(self, value, attr, obj, **kwargs):
        return self.serialize_func(obj)

    def _deserialize(self, value, attr, data, **kwargs):
        if self.deserialize_func:
            return self.deserialize_func(value)
        return value


_ContantT = typing.TypeVar("_ContantT")


class Constant(Field[_ContantT]):
    """A field that (de)serializes to a preset constant.  If you only want the
    constant added for serialization or deserialization, you should use
    ``dump_only=True`` or ``load_only=True`` respectively.

    :param constant: The constant to return for the field attribute.
    """

    _CHECK_ATTRIBUTE = False

    def __init__(self, constant: _ContantT, **kwargs: Unpack[_BaseFieldKwargs]):
        super().__init__(**kwargs)
        self.constant = constant
        self.load_default = constant
        self.dump_default = constant

    def _serialize(self, value, *args, **kwargs) -> _ContantT:
        return self.constant

    def _deserialize(self, value, *args, **kwargs) -> _ContantT:
        return self.constant


# Aliases
URL = Url

Str = String
Bool = Boolean
Int = Integer
