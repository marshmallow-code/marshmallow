from marshmallow import Schema, fields


class FooSerializer(Schema):
    _id = fields.Integer()
