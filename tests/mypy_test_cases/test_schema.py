import json

from marshmallow import EXCLUDE, Schema
from marshmallow.fields import Integer, String


# Test that valid `Meta` class attributes pass type checking
class MySchema(Schema):
    foo = String()
    bar = Integer()

    class Meta(Schema.Meta):
        fields = ("foo", "bar")
        additional = ("baz", "qux")
        include = {
            "foo2": String(),
        }
        exclude = ("bar", "baz")
        many = True
        dateformat = "%Y-%m-%d"
        datetimeformat = "%Y-%m-%dT%H:%M:%S"
        timeformat = "%H:%M:%S"
        render_module = json
        ordered = False
        index_errors = True
        load_only = ("foo", "bar")
        dump_only = ("baz", "qux")
        unknown = EXCLUDE
        register = False
