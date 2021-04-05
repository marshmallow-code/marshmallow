from marshmallow import fields


class FrozenSet(fields.Iterable):
    serialization_type = frozenset
    deserialization_type = frozenset
    default_error_messages = {"invalid": "Not a valid frozenset."}
