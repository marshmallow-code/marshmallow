"""Exception classes for marshmallow-related errors."""
import typing


# Key used for schema-level validation errors
SCHEMA = "_schema"


class MarshmallowError(Exception):
    """Base class for all marshmallow-related errors."""


class ValidationError(MarshmallowError):
    """Raised when validation fails on a field or schema.

    Validators and custom fields should raise this exception.

    :param str|list|dict message: An error message, list of error messages, or dict of
        error messages. If a dict, the keys are subitems and the values are error messages.
    :param str field_name: Field name to store the error on.
        If `None`, the error is stored as schema-level error.
    :param dict data: Raw input data.
    :param dict valid_data: Valid (de)serialized data.
    """

    def __init__(
        self,
        message: typing.Union[str, typing.List, typing.Dict],
        field_name: str = SCHEMA,
        data: typing.Dict[str, typing.Any] = None,
        valid_data: typing.Dict[str, typing.Any] = None,
        **kwargs
    ):
        self.messages: typing.Union[typing.List, typing.Dict] = [message] if isinstance(
            message, (str, bytes)
        ) else message
        self.field_name: str = field_name
        self.data: typing.Dict[str, typing.Any] = data
        self.valid_data: typing.Dict[str, typing.Any] = valid_data
        self.kwargs: typing.Dict[str, typing.Any] = kwargs
        MarshmallowError.__init__(self, message)

    def normalized_messages(self):
        if self.field_name == SCHEMA and isinstance(self.messages, dict):
            return self.messages
        return {self.field_name: self.messages}


class RegistryError(NameError):
    """Raised when an invalid operation is performed on the serializer
    class registry.
    """


class StringNotCollectionError(MarshmallowError, TypeError):
    """Raised when a string is passed when a list of strings is expected."""


class FieldInstanceResolutionError(MarshmallowError, TypeError):
    """Raised when schema to instantiate is neither a Schema class nor an instance."""
