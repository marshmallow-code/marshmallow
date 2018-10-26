# -*- coding: utf-8 -*-
"""Exception classes for marshmallow-related errors."""


# Key used for schema-level validation errors
SCHEMA = '_schema'


class MarshmallowError(Exception):
    """Base class for all marshmallow-related errors."""


class ValidationError(MarshmallowError):
    """Raised when validation fails on a field. Validators and custom fields should
    raise this exception.

    :param message: An error message, list of error messages, or dict of
        error messages.
    :param list field_name: Field name to store the error on.
        If `None`, the error is stored as schema-level error.
    :param list fields: `Field` objects to which the error applies.
    """
    def __init__(self, message, field_name=None, data=None, valid_data=None, **kwargs):
        if not isinstance(message, dict) and not isinstance(message, list):
            messages = [message]
        else:
            messages = message
        #: String, list, or dictionary of error messages.
        #: If a `dict`, the keys will be field names and the values will be lists of
        #: messages.
        self.messages = messages
        self.field_name = field_name or SCHEMA
        #: The raw input data.
        self.data = data
        #: The valid, (de)serialized data.
        self.valid_data = valid_data
        self.kwargs = kwargs
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
    """Raised when a string is passed while a list of strings is expected."""
