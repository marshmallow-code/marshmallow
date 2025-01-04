"""Abstract base classes.

These are necessary to avoid circular imports between schema.py and fields.py.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class FieldABC(ABC):
    """Abstract base class from which all Field classes inherit."""

    @abstractmethod
    def serialize(self, attr, obj, accessor=None):
        pass

    @abstractmethod
    def deserialize(self, value):
        pass

    @abstractmethod
    def _serialize(self, value, attr, obj, **kwargs):
        pass

    @abstractmethod
    def _deserialize(self, value, attr, data, **kwargs):
        pass
