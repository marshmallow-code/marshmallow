# -*- coding: utf-8 -*-
"""Test utilities and fixtures."""
import datetime as dt
import uuid

import pytz

from marshmallow import Serializer, fields
from marshmallow.exceptions import MarshallingError

central = pytz.timezone("US/Central")

##### Custom asserts #####

def assert_almost_equal(a, b, precision=5):
    assert round(a, precision) == round(a, precision)


def assert_date_equal(d1, d2):
    assert d1.year == d2.year
    assert d1.month == d2.month
    assert d1.day == d2.day


def assert_datetime_equal(dt1, dt2):
    assert_date_equal(dt1, dt2)
    assert dt1.hour == dt2.hour
    assert dt1.minute == dt2.minute


def assert_time_equal(t1, t2, microseconds=True):
    assert t1.hour == t2.hour
    assert t1.minute == t2.minute
    assert t1.second == t2.second
    if microseconds:
        assert t1.microsecond == t2.microsecond


##### Models #####


class User(object):
    SPECIES = "Homo sapiens"

    def __init__(self, name, age=0, id_=None, homepage=None,
                 email=None, registered=True, time_registered=None,
                 birthdate=None, balance=100, sex='male', employer=None):
        self.name = name
        self.age = age
        # A naive datetime
        self.created = dt.datetime(2013, 11, 10, 14, 20, 58)
        # A TZ-aware datetime
        self.updated = central.localize(dt.datetime(2013, 11, 10, 14, 20, 58), is_dst=False)
        self.id = id_
        self.homepage = homepage
        self.email = email
        self.balance = balance
        self.registered = True
        self.hair_colors = ['black', 'brown', 'blond', 'redhead']
        self.sex_choices = ('male', 'female')
        self.finger_count = 10
        self.uid = uuid.uuid1()
        self.time_registered = time_registered or dt.time(1, 23, 45, 6789)
        self.birthdate = birthdate or dt.date(2013, 1, 23)
        self.sex = sex
        self.employer = employer
        self.relatives = []

    @property
    def since_created(self):
        return dt.datetime(2013, 11, 24) - self.created

    def __repr__(self):
        return "<User {0}>".format(self.name)


class Blog(object):
    def __init__(self, title, user, collaborators=None, categories=None, id_=None):
        self.title = title
        self.user = user
        self.collaborators = collaborators or []  # List/tuple of users
        self.categories = categories
        self.id = id_

    def __contains__(self, item):
        return item.name in [each.name for each in self.collaborators]

###### Serializers #####


class Uppercased(fields.Field):
    '''Custom field formatting example.'''
    def _format(self, value):
        if value:
            return value.upper()


class UserSerializer(Serializer):
    name = fields.String()
    age = fields.Float()
    created = fields.DateTime()
    created_formatted = fields.DateTime(format="%Y-%m-%d", attribute="created")
    created_iso = fields.DateTime(format="iso", attribute="created")
    updated = fields.DateTime()
    updated_local = fields.LocalDateTime(attribute="updated")
    species = fields.String(attribute="SPECIES")
    id = fields.String(default="no-id")
    uppername = Uppercased(attribute='name')
    homepage = fields.Url()
    email = fields.Email()
    balance = fields.Price()
    is_old = fields.Method("get_is_old")
    lowername = fields.Function(lambda obj: obj.name.lower())
    registered = fields.Boolean()
    hair_colors = fields.List(fields.Raw)
    sex_choices = fields.List(fields.Raw)
    finger_count = fields.Integer()
    uid = fields.UUID()
    time_registered = fields.Time()
    birthdate = fields.Date()
    since_created = fields.TimeDelta()
    sex = fields.Select(['male', 'female'])

    def get_is_old(self, obj):
        try:
            return obj.age > 80
        except TypeError as te:
            raise MarshallingError(te)

    def make_object(self, data):
        return User(**data)


class UserMetaSerializer(Serializer):
    """The equivalent of the UserSerializer, using the ``fields`` option."""
    uppername = Uppercased(attribute='name')
    balance = fields.Price()
    is_old = fields.Method("get_is_old")
    lowername = fields.Function(lambda obj: obj.name.lower())
    updated_local = fields.LocalDateTime(attribute="updated")
    species = fields.String(attribute="SPECIES")
    homepage = fields.Url()
    email = fields.Email()

    def get_is_old(self, obj):
        try:
            return obj.age > 80
        except TypeError as te:
            raise MarshallingError(te)

    class Meta:
        fields = ('name', 'age', 'created', 'updated', 'id', 'homepage',
                  'uppername', 'email', 'balance', 'is_old', 'lowername',
                  "updated_local", "species", 'registered', 'hair_colors',
                  'sex_choices', "finger_count", 'uid', 'time_registered',
                  'birthdate', 'since_created')


class UserExcludeSerializer(UserSerializer):
    class Meta:
        exclude = ("created", "updated", "field_not_found_but_thats_ok")


class UserAdditionalSerializer(Serializer):
    lowername = fields.Function(lambda obj: obj.name.lower())

    class Meta:
        additional = ("name", "age", "created", "email")


class UserIntSerializer(UserSerializer):
    age = fields.Integer()


class UserFixedSerializer(UserSerializer):
    age = fields.Fixed(decimals=2)


class UserFloatStringSerializer(UserSerializer):
    age = fields.Float(as_string=True)


class UserDecimalSerializer(UserSerializer):
    age = fields.Arbitrary()


class ExtendedUserSerializer(UserSerializer):
    is_old = fields.Boolean()


class UserRelativeUrlSerializer(UserSerializer):
    homepage = fields.Url(relative=True)


class BlogSerializer(Serializer):
    title = fields.String()
    user = fields.Nested(UserSerializer)
    collaborators = fields.Nested(UserSerializer, many=True)
    categories = fields.List(fields.String)
    id = fields.String()


class BlogUserMetaSerializer(Serializer):
    user = fields.Nested(UserMetaSerializer())
    collaborators = fields.Nested(UserMetaSerializer, many=True)


class BlogSerializerMeta(Serializer):
    '''Same as BlogSerializer but using ``fields`` options.'''
    user = fields.Nested(UserSerializer)
    collaborators = fields.Nested(UserSerializer, many=True)

    class Meta:
        fields = ('title', 'user', 'collaborators', 'categories', "id")


class BlogSerializerOnly(Serializer):
    title = fields.String()
    user = fields.Nested(UserSerializer)
    collaborators = fields.Nested(UserSerializer, only=("id", ), many=True)


class BlogSerializerExclude(BlogSerializer):
    user = fields.Nested(UserSerializer, exclude=("uppername", "species"))


class BlogSerializerOnlyExclude(BlogSerializer):
    user = fields.Nested(UserSerializer, only=("name", ), exclude=("name", "species"))


class BlogSerializerPrefixedUser(BlogSerializer):
    user = fields.Nested(UserSerializer(prefix="usr_"))
    collaborators = fields.Nested(UserSerializer(prefix="usr_"), many=True)


class mockjson(object):

    @staticmethod
    def dumps(val):
        return '{"foo": 42}'.encode('utf-8')

    @staticmethod
    def loads(val):
        return {'foo': 42}
