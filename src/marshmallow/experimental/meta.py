from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from marshmallow.fields import Field
    from marshmallow.schema import SchemaMeta
    from marshmallow.types import UnknownOption


@typing.overload
def meta(
    *bases: SchemaMeta,
    fields: tuple[str, ...] | list[str] | None,
    additional: tuple[str, ...] | list[str] | None,
    include: dict[str, Field] | None,
    exclude: tuple[str, ...] | list[str] | None,
    many: bool | None,
    dateformat: str | None,
    datetimeformat: str | None,
    timeformat: str | None,
    render_module: typing.Any | None,
    index_errors: bool | None,
    load_only: tuple[str, ...] | list[str] | None,
    dump_only: tuple[str, ...] | list[str] | None,
    unknown: UnknownOption | None,
    register: bool | None,
    **kwargs,
):
    """
    :param *bases: The meta classes to inherit from. Inherits from the decorated schema's
        Meta class by default. Pass `None` to prevent inheritance.
    :param fields: Fields to include in the (de)serialized result
    :param additional: Fields to include in addition to the explicitly declared fields.
        `additional <marshmallow.Schema.Meta.additional>` and `fields <marshmallow.Schema.Meta.fields>`
        are mutually-exclusive options.
    :param include: Dictionary of additional fields to include in the schema. It is
        usually better to define fields as class variables, but you may need to
        use this option, e.g., if your fields are Python keywords.
    :param exclude: Fields to exclude in the serialized result.
        Nested fields can be represented with dot delimiters.
    :param many: Whether data should be (de)serialized as a collection by default.
    :param dateformat: Default format for `Date <marshmallow.fields.Date>` fields.
    :param datetimeformat: Default format for `DateTime <marshmallow.fields.DateTime>` fields.
    :param timeformat: Default format for `Time <marshmallow.fields.Time>` fields.
    :param render_module:  Module to use for `loads <marshmallow.Schema.loads>` and `dumps <marshmallow.Schema.dumps>`.
        Defaults to `json` from the standard library.
    :param index_errors: If `True`, errors dictionaries will include the index of invalid items in a collection.
    :param load_only: Fields to exclude from serialized results
    :param dump_only: Fields to exclude from serialized results
    :param unknown: Whether to exclude, include, or raise an error for unknown fields in the data.
        Use `EXCLUDE`, `INCLUDE` or `RAISE`.
    :param register: Whether to register the `Schema <marshmallow.Schema>` with marshmallow's internal
        class registry. Must be `True` if you intend to refer to this `Schema <marshmallow.Schema>`
        by class name in `Nested` fields. Only set this to `False` when memory
        usage is critical. Defaults to `True`.
    """


@typing.overload
def meta(*bases, **kwargs): ...


def meta(*bases, **kwargs):
    def wrapper(schema):
        mro = bases if bases else (schema.Meta,)
        meta = type(schema.Meta.__name__, mro, kwargs)
        return type(schema.__name__, (schema,), {"Meta": meta})

    return wrapper
