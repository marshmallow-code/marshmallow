from __future__ import annotations

from marshmallow.schema import Schema, SchemaOpts

from . import fields
from marshmallow.decorators import (
    pre_dump,
    post_dump,
    pre_load,
    post_load,
    validates,
    validates_schema,
)
from marshmallow.utils import EXCLUDE, INCLUDE, RAISE, pprint, missing
from marshmallow.exceptions import ValidationError
from packaging.version import Version

__version__ = "3.15.0"
__parsed_version__ = Version(__version__)
__version_info__: tuple[int, int, int] | tuple[
    int, int, int, str, int
] = __parsed_version__.release  # type: ignore[assignment]
if __parsed_version__.pre:
    __version_info__ += __parsed_version__.pre  # type: ignore[assignment]
__all__ = [
    "EXCLUDE",
    "INCLUDE",
    "RAISE",
    "Schema",
    "SchemaOpts",
    "fields",
    "validates",
    "validates_schema",
    "pre_dump",
    "post_dump",
    "pre_load",
    "post_load",
    "pprint",
    "ValidationError",
    "missing",
]
