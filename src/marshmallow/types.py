"""Type aliases.

.. warning::

    This module is provisional. Types may be modified, added, and removed between minor releases.
"""

from __future__ import annotations

import typing

#: A type that can be either a sequence of strings or a set of strings
StrSequenceOrSet: typing.TypeAlias = typing.Sequence[str] | typing.AbstractSet[str]

#: Type for validator functions
Validator: typing.TypeAlias = typing.Callable[[typing.Any], typing.Any]

#: A valid option for the ``unknown`` schema option and argument
UnknownOption: typing.TypeAlias = typing.Literal["exclude", "include", "raise"]


class SchemaValidator(typing.Protocol):
    def __call__(
        self,
        output: typing.Any,
        original_data: typing.Any = ...,
        *,
        partial: bool | StrSequenceOrSet | None = None,
        unknown: UnknownOption | None = None,
        many: bool = False,
    ) -> None: ...


class RenderModule(typing.Protocol):
    def dumps(
        self, obj: typing.Any, *args: typing.Any, **kwargs: typing.Any
    ) -> str: ...

    def loads(
        self, s: str | bytes | bytearray, *args: typing.Any, **kwargs: typing.Any
    ) -> typing.Any: ...
