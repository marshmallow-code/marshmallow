# -*- coding: utf-8 -*-
"""Exception classes for marshmallow-related errors."""

class MarshmallowError(Exception):
    """Base class for all marshmallow-related errors."""
    pass


class _WrappingException(MarshmallowError):
    """Exception that wraps a different, underlying exception. Used so that
    an error in serialization or deserialization can be reraised as an
    :exc:`MarshmallowError <MarshmallowError>`.
    """

    def __init__(self, underlying_exception):
        if isinstance(underlying_exception, Exception):
            self.underlying_exception = underlying_exception
        else:
            self.underlying_exception = None
        super(_WrappingException, self).__init__(str(underlying_exception))


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


class RegistryError(ForcedError, NameError):
    """Raised when an invalid operation is performed on the serializer
    class registry.
    """
    pass


class MarshallingError(_WrappingException):
    """Raised in case of a marshalling error. If a MarshallingError is raised
    during serialization, the error is caught and the error message
    is stored in the Serializer's ``error`` dictionary (unless ``strict`` mode
    is turned on).
    """
    pass


class UnmarshallingError(_WrappingException):
    """Raised when invalid data are passed to a deserialization function."""
    pass
