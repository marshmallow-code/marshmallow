"""Test utilities and fixtures."""
import datetime as dt
import uuid

import simplejson

import pytz

from marshmallow import Schema, fields, post_load, validate, missing
from marshmallow.exceptions import ValidationError

central = pytz.timezone("US/Central")


ALL_FIELDS = [
    fields.String,
    fields.Integer,
    fields.Boolean,
    fields.Float,
    fields.Number,
    fields.DateTime,
    fields.LocalDateTime,
    fields.Time,
    fields.Date,
    fields.TimeDelta,
    fields.Dict,
    fields.Url,
    fields.Email,
    fields.UUID,
    fields.Decimal,
]

##### Custom asserts #####


def assert_date_equal(d1, d2):
    assert d1.year == d2.year
    assert d1.month == d2.month
    assert d1.day == d2.day


def assert_datetime_equal(dt1, dt2):
    assert_date_equal(dt1, dt2)
    assert dt1.hour == dt2.hour
    assert dt1.minute == dt2.minute
    assert dt1.second == dt2.second
    assert dt1.microsecond == dt2.microsecond


def assert_time_equal(t1, t2):
    assert t1.hour == t2.hour
    assert t1.minute == t2.minute
    assert t1.second == t2.second
    assert t1.microsecond == t2.microsecond


##### Models #####


class User:
    SPECIES = "Homo sapiens"

    def __init__(
        self,
        name,
        age=0,
        id_=None,
        homepage=None,
        email=None,
        registered=True,
        time_registered=None,
        birthdate=None,
        balance=100,
        sex="male",
        employer=None,
        various_data=None,
    ):
        self.name = name
        self.age = age
        # A naive datetime
        self.created = dt.datetime(2013, 11, 10, 14, 20, 58)
        # A TZ-aware datetime
        self.updated = central.localize(
            dt.datetime(2013, 11, 10, 14, 20, 58), is_dst=False
        )
        self.id = id_
        self.homepage = homepage
        self.email = email
        self.balance = balance
        self.registered = True
        self.hair_colors = ["black", "brown", "blond", "redhead"]
        self.sex_choices = ("male", "female")
        self.finger_count = 10
        self.uid = uuid.uuid1()
        self.time_registered = time_registered or dt.time(1, 23, 45, 6789)
        self.birthdate = birthdate or dt.date(2013, 1, 23)
        self.activation_date = dt.date(2013, 12, 11)
        self.sex = sex
        self.employer = employer
        self.relatives = []
        self.various_data = various_data or {
            "pets": ["cat", "dog"],
            "address": "1600 Pennsylvania Ave\n" "Washington, DC 20006",
        }

    @property
    def since_created(self):
        return dt.datetime(2013, 11, 24) - self.created

    def __repr__(self):
        return "<User {}>".format(self.name)


class Blog:
    def __init__(self, title, user, collaborators=None, categories=None, id_=None):
        self.title = title
        self.user = user
        self.collaborators = collaborators or []  # List/tuple of users
        self.categories = categories
        self.id = id_

    def __contains__(self, item):
        return item.name in [each.name for each in self.collaborators]


class DummyModel:
    def __init__(self, foo):
        self.foo = foo

    def __eq__(self, other):
        return self.foo == other.foo

    def __str__(self):
        return "bar {}".format(self.foo)


###### Schemas #####


class Uppercased(fields.Field):
    """Custom field formatting example."""

    def _serialize(self, value, attr, obj):
        if value:
            return value.upper()


def get_lowername(obj):
    if obj is None:
        return missing
    if isinstance(obj, dict):
        return obj.get("name").lower()
    else:
        return obj.name.lower()


class UserSchema(Schema):
    name = fields.String()
    age = fields.Float()
    created = fields.DateTime()
    created_formatted = fields.DateTime(
        format="%Y-%m-%d", attribute="created", dump_only=True
    )
    created_iso = fields.DateTime(format="iso", attribute="created", dump_only=True)
    updated = fields.DateTime()
    updated_local = fields.LocalDateTime(attribute="updated", dump_only=True)
    species = fields.String(attribute="SPECIES")
    id = fields.String(default="no-id")
    uppername = Uppercased(attribute="name", dump_only=True)
    homepage = fields.Url()
    email = fields.Email()
    balance = fields.Decimal()
    is_old = fields.Method("get_is_old")
    lowername = fields.Function(get_lowername)
    registered = fields.Boolean()
    hair_colors = fields.List(fields.Raw)
    sex_choices = fields.List(fields.Raw)
    finger_count = fields.Integer()
    uid = fields.UUID()
    time_registered = fields.Time()
    birthdate = fields.Date()
    activation_date = fields.Date()
    since_created = fields.TimeDelta()
    sex = fields.Str(validate=validate.OneOf(["male", "female"]))
    various_data = fields.Dict()

    class Meta:
        render_module = simplejson

    def get_is_old(self, obj):
        if obj is None:
            return missing
        if isinstance(obj, dict):
            age = obj.get("age")
        else:
            age = obj.age
        try:
            return age > 80
        except TypeError as te:
            raise ValidationError(str(te))

    @post_load
    def make_user(self, data, **kwargs):
        return User(**data)


class UserMetaSchema(Schema):
    """The equivalent of the UserSchema, using the ``fields`` option."""

    uppername = Uppercased(attribute="name", dump_only=True)
    balance = fields.Decimal()
    is_old = fields.Method("get_is_old")
    lowername = fields.Function(get_lowername)
    updated_local = fields.LocalDateTime(attribute="updated", dump_only=True)
    species = fields.String(attribute="SPECIES")
    homepage = fields.Url()
    email = fields.Email()
    various_data = fields.Dict()

    def get_is_old(self, obj):
        if obj is None:
            return missing
        if isinstance(obj, dict):
            age = obj.get("age")
        else:
            age = obj.age
        try:
            return age > 80
        except TypeError as te:
            raise ValidationError(str(te))

    class Meta:
        fields = (
            "name",
            "age",
            "created",
            "updated",
            "id",
            "homepage",
            "uppername",
            "email",
            "balance",
            "is_old",
            "lowername",
            "updated_local",
            "species",
            "registered",
            "hair_colors",
            "sex_choices",
            "finger_count",
            "uid",
            "time_registered",
            "birthdate",
            "since_created",
            "various_data",
        )


class UserExcludeSchema(UserSchema):
    class Meta:
        exclude = ("created", "updated")


class UserAdditionalSchema(Schema):
    lowername = fields.Function(lambda obj: obj.name.lower())

    class Meta:
        additional = ("name", "age", "created", "email")


class UserIntSchema(UserSchema):
    age = fields.Integer()


class UserFloatStringSchema(UserSchema):
    age = fields.Float(as_string=True)


class ExtendedUserSchema(UserSchema):
    is_old = fields.Boolean()


class UserRelativeUrlSchema(UserSchema):
    homepage = fields.Url(relative=True)


class BlogSchema(Schema):
    title = fields.String()
    user = fields.Nested(UserSchema)
    collaborators = fields.Nested(UserSchema, many=True)
    categories = fields.List(fields.String)
    id = fields.String()


class BlogUserMetaSchema(Schema):
    user = fields.Nested(UserMetaSchema())
    collaborators = fields.Nested(UserMetaSchema, many=True)


class BlogSchemaMeta(Schema):
    """Same as BlogSerializer but using ``fields`` options."""

    user = fields.Nested(UserSchema)
    collaborators = fields.Nested(UserSchema, many=True)

    class Meta:
        fields = ("title", "user", "collaborators", "categories", "id")


class BlogOnlySchema(Schema):
    title = fields.String()
    user = fields.Nested(UserSchema)
    collaborators = fields.Nested(UserSchema, only=("id",), many=True)


class BlogSchemaExclude(BlogSchema):
    user = fields.Nested(UserSchema, exclude=("uppername", "species"))


class BlogSchemaOnlyExclude(BlogSchema):
    user = fields.Nested(UserSchema, only=("name",), exclude=("name", "species"))


class mockjson:  # noqa
    @staticmethod
    def dumps(val):
        return "{'foo': 42}".encode("utf-8")

    @staticmethod
    def loads(val):
        return {"foo": 42}
