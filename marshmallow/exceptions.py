# -*- coding: utf-8 -*-
"""Exception classes for marshmallow-related errors."""
import warnings

from marshmallow.compat import basestring

class MarshmallowError(Exception):
    """Base class for all marshmallow-related errors."""
    pass


class ValidationError(MarshmallowError):
    """Raised when validation fails on a field. Validators and custom fields should
    raise this exception.

    :param message: An error message, list of error messages, or dict of
        error messages.
    :param list field_names: Field names to store the error on.
        If `None`, the error is stored in its default location.
    :param list fields: `Field` objects to which the error applies.
    """

    def __init__(self, message, field_names=None, fields=None, data=None):
        if not isinstance(message, dict) and not isinstance(message, list):
            messages = [message]
        else:
            messages = message
        #: String, list, or dictionary of error messages.
        #: If a `dict`, the keys will be field names and the values will be lists of
        #: messages.
        self.messages = messages
        #: List of field objects which failed validation.
        self.fields = fields
        if isinstance(field_names, basestring):
            #: List of field_names which failed validation.
            self.field_names = [field_names]
        else:  # fields is a list or None
            self.field_names = field_names or []
        # Store nested data
        self.data = data
        MarshmallowError.__init__(self, message)


class RegistryError(NameError):
    """Raised when an invalid operation is performed on the serializer
    class registry.
    """
    pass


class MarshallingError(ValidationError):
    """Raised in case of a marshalling error. If raised during serialization,
    the error is caught and the error message is stored in an ``errors``
    dictionary (unless ``strict`` mode is turned on).

    .. deprecated:: 2.0.0
        Use :exc:`ValidationError` instead.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn('MarshallingError is deprecated. Raise a ValidationError instead',
                      category=DeprecationWarning)
        super(MarshallingError, self).__init__(*args, **kwargs)


class UnmarshallingError(ValidationError):
    """Raised when invalid data are passed to a deserialization function. If
    raised during deserialization, the error is caught and the error message
    is stored in an ``errors`` dictionary.

    .. deprecated:: 2.0.0
        Use :exc:`ValidationError` instead.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn('UnmarshallingError is deprecated. Raise a ValidationError instead',
                      category=DeprecationWarning)
        super(UnmarshallingError, self).__init__(*args, **kwargs)
