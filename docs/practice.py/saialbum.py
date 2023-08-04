from datetime import date


class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.created_at = dt.datetime.now()

    def __repr__(self):
        return "<User(name={self.name!r})>".format(self=self)


from marshmallow import Schema, fields

userSchema = Schema.from_dict(
    {"name": fields.Str(), "email": fields.Email(), "created_at": fields.DateTime()}
)

from pprint import pprint

spr = dict(name="spr the great", email="   ", created_at=date(2017, 8, 17))
Schema = userSchema()
result = Schema.dump(spr)
pprint(result)
