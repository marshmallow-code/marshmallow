from marshmallow import Serializer, fields


class FooSerializer(Serializer):
    _id = fields.Integer()
