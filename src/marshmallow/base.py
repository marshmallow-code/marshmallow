"""Abstract base classes.

These are necessary to avoid circular imports between core.py and fields.py.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""
import typing


class FieldABC:
    """Abstract base class from which all Field classes inherit."""

    parent = None
    name = None
    root = None

    def serialize(self, attr, obj, accessor=None):
        raise NotImplementedError

    def deserialize(self, value):
        raise NotImplementedError

    def _serialize(self, value, attr, obj, **kwargs):
        raise NotImplementedError

    def _deserialize(self, value, attr, data, **kwargs):
        raise NotImplementedError


class SchemaABC:
    """Abstract base class from which all Schemas inherit."""

    def dump(self, obj, *, many: typing.Optional[bool] = None):
        raise NotImplementedError

    def dumps(self, obj, *, many: typing.Optional[bool] = None):
        raise NotImplementedError

    def load(
        self, data, *, many: typing.Optional[bool] = None, partial=None, unknown=None
    ):
        raise NotImplementedError

    def loads(
        self,
        json_data,
        *,
        many: typing.Optional[bool] = None,
        partial=None,
        unknown=None,
        **kwargs
    ):
        raise NotImplementedError
