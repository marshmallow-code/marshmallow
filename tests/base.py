"""Test utilities and fixtures."""

import datetime as dt
import functools
import typing
import uuid
from enum import Enum, IntEnum
from zoneinfo import ZoneInfo

import simplejson

from marshmallow import Schema, fields, missing, post_load, validate
from marshmallow.exceptions import ValidationError

central = ZoneInfo("America/Chicago")


class GenderEnum(IntEnum):
    male = 1
    female = 2
    non_binary = 3


class HairColorEnum(Enum):
    black = "black hair"
    brown = "brown hair"
    blond = "blond hair"
    red = "red hair"


class DateEnum(Enum):
    date_1 = dt.date(2004, 2, 29)
    date_2 = dt.date(2008, 2, 29)
    date_3 = dt.date(2012, 2, 29)


ALL_FIELDS = [
    fields.String,
    fields.Integer,
    fields.Boolean,
    fields.Float,
    fields.DateTime,
    fields.Time,
    fields.Date,
    fields.TimeDelta,
    fields.Dict,
    fields.Url,
    fields.Email,
    fields.UUID,
    fields.Decimal,
    fields.IP,
    fields.IPv4,
    fields.IPv6,
    fields.IPInterface,
    fields.IPv4Interface,
    fields.IPv6Interface,
    functools.partial(fields.Enum, GenderEnum),
    functools.partial(fields.Enum, HairColorEnum, by_value=fields.String),
    functools.partial(fields.Enum, GenderEnum, by_value=fields.Integer),
]


##### Custom asserts #####


def assert_date_equal(d1: dt.date, d2: dt.date) -> None:
    assert d1.year == d2.year
    assert d1.month == d2.month
    assert d1.day == d2.day


def assert_time_equal(t1: dt.time, t2: dt.time) -> None:
    assert t1.hour == t2.hour
    assert t1.minute == t2.minute
    assert t1.second == t2.second
    assert t1.microsecond == t2.microsecond


##### Validation #####


def predicate(
    func: typing.Callable[[typing.Any], bool],
) -> typing.Callable[[typing.Any], None]:
    def validate(value: typing.Any) -> None:
        if func(value) is False:
            raise ValidationError("Invalid value.")

    return validate


##### Models #####


class User:
    SPECIES = "Homo sapiens"

    def __init__(
        self,
        name,
        *,
        age=0,
        id_=None,
        homepage=None,
        email=None,
        registered=True,
        time_registered=None,
        birthdate=None,
        birthtime=None,
        balance=100,
        sex=GenderEnum.male,
        hair_color=HairColorEnum.black,
        employer=None,
        various_data=None,
    ):
        self.name = name
        self.age = age
        # A naive datetime
        self.created = dt.datetime(2013, 11, 10, 14, 20, 58)
        # A TZ-aware datetime
        self.updated = dt.datetime(2013, 11, 10, 14, 20, 58, tzinfo=central)
        self.id = id_
        self.homepage = homepage
        self.email = email
        self.balance = balance
        self.registered = registered
        self.hair_colors = list(HairColorEnum.__members__)
        self.sex_choices = list(GenderEnum.__members__)
        self.finger_count = 10
        self.uid = uuid.uuid1()
        self.time_registered = time_registered or dt.time(1, 23, 45, 6789)
        self.birthdate = birthdate or dt.date(2013, 1, 23)
        self.birthtime = birthtime or dt.time(0, 1, 2, 3333)
        self.activation_date = dt.date(2013, 12, 11)
        self.sex = sex
        self.hair_color = hair_color
        self.employer = employer
        self.relatives = []
        self.various_data = various_data or {
            "pets": ["cat", "dog"],
            "address": "1600 Pennsylvania Ave\nWashington, DC 20006",
        }

    @property
    def since_created(self):
        return dt.datetime(2013, 11, 24) - self.created

    def __repr__(self):
        return f"<User {self.name}>"


class Blog:
    def __init__(self, title, user, collaborators=None, categories=None, id_=None):
        self.title = title
        self.user = user
        self.collaborators = collaborators or []  # List/tuple of users
        self.categories = categories
        self.id = id_

    def __contains__(self, item):
        return item.name in [each.name for each in self.collaborators]


###### Schemas #####


class Uppercased(fields.String):
    """Custom field formatting example."""

    def _serialize(self, value, attr, obj, **kwargs):
        if value:
            return value.upper()
        return None


def get_lowername(obj):
    if obj is None:
        return missing
    if isinstance(obj, dict):
        return obj.get("name", "").lower()
    return obj.name.lower()


class UserSchema(Schema):
    name = fields.String()
    age: fields.Field = fields.Float()
    created = fields.DateTime()
    created_formatted = fields.DateTime(
        format="%Y-%m-%d", attribute="created", dump_only=True
    )
    created_iso = fields.DateTime(format="iso", attribute="created", dump_only=True)
    updated = fields.DateTime()
    species = fields.String(attribute="SPECIES")
    id = fields.String(dump_default="no-id")
    uppername = Uppercased(attribute="name", dump_only=True)
    homepage = fields.Url()
    email = fields.Email()
    balance = fields.Decimal()
    is_old: fields.Field = fields.Method("get_is_old")
    lowername = fields.Function(get_lowername)
    registered = fields.Boolean()
    hair_colors = fields.List(fields.Raw)
    sex_choices = fields.List(fields.Raw)
    finger_count = fields.Integer()
    uid = fields.UUID()
    time_registered = fields.Time()
    birthdate = fields.Date()
    birthtime = fields.Time()
    activation_date = fields.Date()
    since_created = fields.TimeDelta()
    sex = fields.Str(validate=validate.OneOf(list(GenderEnum.__members__)))
    various_data = fields.Dict()

    class Meta:
        render_module = simplejson

    def get_is_old(self, obj):
        if obj is None:
            return missing
        if isinstance(obj, dict):
            age = obj.get("age", 0)
        else:
            age = obj.age
        try:
            return age > 80
        except TypeError as te:
            raise ValidationError(str(te)) from te

    @post_load
    def make_user(self, data, **kwargs):
        return User(**data)


class UserExcludeSchema(UserSchema):
    class Meta:
        exclude = ("created", "updated")


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
    collaborators = fields.List(fields.Nested(UserSchema()))
    categories = fields.List(fields.String)
    id = fields.String()


class BlogOnlySchema(Schema):
    title = fields.String()
    user = fields.Nested(UserSchema)
    collaborators = fields.List(fields.Nested(UserSchema(only=("id",))))


class BlogSchemaExclude(BlogSchema):
    user = fields.Nested(UserSchema, exclude=("uppername", "species"))


class BlogSchemaOnlyExclude(BlogSchema):
    user = fields.Nested(UserSchema, only=("name",), exclude=("name", "species"))


class mockjson:  # noqa: N801
    @staticmethod
    def dumps(val):
        return b"{'foo': 42}"

    @staticmethod
    def loads(val):
        return {"foo": 42}
