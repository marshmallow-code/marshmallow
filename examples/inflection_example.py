from marshmallow import Schema, fields


def camelcase(s):
    parts = iter(s.split("_"))
    return next(parts) + "".join(i.title() for i in parts)


class CamelCaseSchema(Schema):
    """Schema that uses camel-case for its external representation
    and snake-case for its internal representation.
    """

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


# -----------------------------------------------------------------------------


class UserSchema(CamelCaseSchema):
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)


schema = UserSchema()
loaded = schema.load({"firstName": "David", "lastName": "Bowie"})
print(loaded)  # => {'last_name': 'Bowie', 'first_name': 'David'}
dumped = schema.dump(loaded)
print(dumped)  # => {'lastName': 'Bowie', 'firstName': 'David'}
