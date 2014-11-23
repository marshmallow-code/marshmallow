# -*- coding: utf-8 -*-
"""Exception classes for marshmallow-related errors."""
from marshmallow.compat import text_type

class MarshmallowError(Exception):
    """Base class for all marshmallow-related errors."""
    pass


class _WrappingException(MarshmallowError):
    """Exception that wraps a different, underlying exception. Used so that
    an error in serialization or deserialization can be reraised as a
    :exc:`MarshmallowError <MarshmallowError>`.
    """

    def __init__(self, underlying_exception, field=None, field_name=None):
        if isinstance(underlying_exception, Exception):
            self.underlying_exception = underlying_exception
        else:
            self.underlying_exception = None
        self.field = field
        self.field_name = field_name
        super(_WrappingException, self).__init__(
            text_type(underlying_exception)
        )


class ForcedError(_WrappingException):
    """Error that always gets raised, even during serialization.
    Field classes should raise this error if the error should not be stored in
    the Marshaller's error dictionary and should instead be raised.

    Must be instantiated with an underlying exception.

    Example: ::

        def _serialize(self, value, key, obj):
            if not isinstace(value, dict):
                raise ForcedError(ValueError('Value must be a dict.'))
    """
    pass


class ValidationError(MarshmallowError):
    """Raised when validation fails on a field.

    :param message: An error message, list of error messages, or dict of
        error messages.
    :param str field: Name of the field to store the error on. If None,
        the error is stored in its default location.
    """

    def __init__(self, message, field=None):
        if not isinstance(message, dict) and not isinstance(message, list):
            messages = [message]
        else:
            messages = message
        self.messages = messages
        self.field = field
        MarshmallowError.__init__(self, message)


class RegistryError(ForcedError, NameError):
    """Raised when an invalid operation is performed on the serializer
    class registry.
    """
    pass


class MarshallingError(_WrappingException):
    """Raised in case of a marshalling error. If raised during serialization,
    the error is caught and the error message is stored in an ``errors``
    dictionary (unless ``strict`` mode is turned on).
    """
    pass


class UnmarshallingError(_WrappingException):
    """Raised when invalid data are passed to a deserialization function. If
    raised during deserialization, the error is caught and the error message
    is stored in an ``errors`` dictionary.
    """
    pass
