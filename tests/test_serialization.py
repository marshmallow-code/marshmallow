#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
import datetime as dt
import uuid
import warnings

import pytest
import pytz

from marshmallow import Serializer, fields, validate, utils
from marshmallow.exceptions import MarshallingError
from marshmallow.compat import unicode, binary_type, total_seconds


central = pytz.timezone("US/Central")

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


class Uppercased(fields.Raw):
    '''Custom field formatting example.'''
    def format(self, value):
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


class UserMetaSerializer(Serializer):
    '''The equivalent of the UserSerializer, using the ``fields`` option.'''
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

##### The Tests #####

def assert_almost_equal(a, b, precision=5):
    assert round(a, precision) == round(a, precision)

@pytest.fixture
def user():
    return User(name="Monty", age=42.3, homepage="http://monty.python.org/")

@pytest.fixture
def serialized_user(user):
    return UserSerializer(user)

# Run tests with both verbose serializer and "meta" option serializer
@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_serializing_basic_object(SerializerClass, user):
    s = SerializerClass(user)
    assert s.data['name'] == user.name
    assert_almost_equal(s.data['age'], 42.3)
    assert s.data['registered']


def test_serializing_none():
    s = UserSerializer(None)
    assert s.data['name'] == ''
    assert s.data['age'] == 0


@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_fields_are_not_copies(SerializerClass):
    s = SerializerClass(User('Monty', age=42))
    s2 = SerializerClass(User('Monty', age=43))
    assert s.fields is not s2.fields


def test_json(serialized_user):
    json_data = serialized_user.json
    expected = binary_type(json.dumps(serialized_user.data).encode("utf-8"))
    assert json_data == expected


def test_to_json_returns_bytestring(serialized_user):
    assert isinstance(serialized_user.to_json(), binary_type)


def test_naive_datetime_field(serialized_user):
    assert serialized_user.data['created'] == 'Sun, 10 Nov 2013 14:20:58 -0000'

def test_datetime_formatted_field(user, serialized_user):
    result = serialized_user.data['created_formatted']
    assert result == user.created.strftime("%Y-%m-%d")

def test_datetime_iso_field(user, serialized_user):
    assert serialized_user.data['created_iso'] == utils.isoformat(user.created)

def test_tz_datetime_field(serialized_user):
    # Datetime is corrected back to GMT
    assert serialized_user.data['updated'] == 'Sun, 10 Nov 2013 20:20:58 -0000'

def test_local_datetime_field(serialized_user):
    assert serialized_user.data['updated_local'] == 'Sun, 10 Nov 2013 14:20:58 -0600'

def test_class_variable(serialized_user):
    assert serialized_user.data['species'] == 'Homo sapiens'

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_serialize_many(SerializerClass):
    user1 = User(name="Mick", age=123)
    user2 = User(name="Keith", age=456)
    users = [user1, user2]
    serialized = SerializerClass(users, many=True)
    assert len(serialized.data) == 2
    assert serialized.data[0]['name'] == "Mick"
    assert serialized.data[1]['name'] == "Keith"

def test_no_implicit_list_handling():
    users = [User(name='Mick'), User(name='Keith')]
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        with pytest.raises(TypeError):
            UserSerializer(users)
    assert issubclass(w[-1].category, DeprecationWarning)


def test_inheriting_serializer(user):
    serialized = ExtendedUserSerializer(user)
    assert serialized.data['name'] == user.name
    assert not serialized.data['is_old']

def test_custom_field(serialized_user, user):
    assert serialized_user.data['uppername'] == user.name.upper()

def test_url_field(serialized_user, user):
    assert serialized_user.data['homepage'] == user.homepage

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_url_field_validation(SerializerClass):
    invalid = User("John", age=42, homepage="/john")
    s = SerializerClass(invalid)
    assert s.is_valid(["homepage"]) is False

def test_relative_url_field():
    u = User("John", age=42, homepage="/john")
    serialized = UserRelativeUrlSerializer(u)
    assert serialized.is_valid()

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_stores_invalid_url_error(SerializerClass):
    user = User(name="John Doe", homepage="www.foo.com")
    serialized = SerializerClass(user)
    assert "homepage" in serialized.errors
    expected = '"www.foo.com" is not a valid URL. Did you mean: "http://www.foo.com"?'
    assert serialized.errors['homepage'] == expected

def test_default():
    user = User("John")  # No ID set
    serialized = UserSerializer(user)
    assert serialized.data['id'] == "no-id"

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_email_field(SerializerClass):
    u = User("John", email="john@example.com")
    s = SerializerClass(u)
    assert s.data['email'] == "john@example.com"

def test_stored_invalid_email():
    u = User("John", email="johnexample.com")
    s = UserSerializer(u)
    assert "email" in s.errors
    assert s.errors['email'] == '"johnexample.com" is not a valid email address.'

def test_integer_field():
    u = User("John", age=42.3)
    serialized = UserIntSerializer(u)
    assert type(serialized.data['age']) == int
    assert serialized.data['age'] == 42

def test_integer_default():
    user = User("John", age=None)
    serialized = UserIntSerializer(user)
    assert type(serialized.data['age']) == int
    assert serialized.data['age'] == 0

def test_fixed_field():
    u = User("John", age=42.3)
    serialized = UserFixedSerializer(u)
    assert serialized.data['age'] == "42.30"

def test_as_string():
    u = User("John", age=42.3)
    serialized = UserFloatStringSerializer(u)
    assert type(serialized.data['age']) == str
    assert_almost_equal(float(serialized.data['age']), 42.3)

def test_decimal_field():
    u = User("John", age=42.3)
    s = UserDecimalSerializer(u)
    assert type(s.data['age']) == unicode
    assert_almost_equal(float(s.data['age']), 42.3)

def test_price_field(serialized_user):
    assert serialized_user.data['balance'] == "100.00"

def test_validate():
    valid = User("Joe", email="joe@foo.com")
    invalid = User("John", email="johnexample.com")
    assert UserSerializer(valid).is_valid()
    assert UserSerializer(invalid).is_valid() is False

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_validate_field(SerializerClass):
    invalid = User("John", email="johnexample.com")
    assert SerializerClass(invalid).is_valid(["name"]) is True
    assert SerializerClass(invalid).is_valid(["email"]) is False

def test_validating_nonexistent_field_raises_error(serialized_user):
    with pytest.raises(KeyError):
        serialized_user.is_valid(["foobar"])

def test_fields_param_must_be_list_or_tuple():
    invalid = User("John", email="johnexample.com")
    with pytest.raises(ValueError):
        UserSerializer(invalid).is_valid("name")

def test_extra():
    user = User("Joe", email="joe@foo.com")
    s = UserSerializer(user, extra={"fav_color": "blue"})
    assert s.data['fav_color'] == "blue"

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_method_field(SerializerClass, serialized_user):
    assert serialized_user.data['is_old'] is False
    u = User("Joe", age=81)
    assert SerializerClass(u).data['is_old'] is True

def test_function_field(serialized_user, user):
    assert serialized_user.data['lowername'] == user.name.lower()

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_prefix(SerializerClass, user):
    s = SerializerClass(user, prefix="usr_")
    assert s.data['usr_name'] == user.name

def test_fields_must_be_declared_as_instances():
    class BadUserSerializer(Serializer):
        name = fields.String
    with pytest.raises(TypeError):
        BadUserSerializer(user)

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_serializing_generator(SerializerClass):
    users = [User("Foo"), User("Bar")]
    user_gen = (u for u in users)
    s = SerializerClass(user_gen, many=True)
    assert len(s.data) == 2
    assert s.data[0] == SerializerClass(users[0]).data


def test_serializing_empty_list_returns_empty_list():
    assert UserSerializer([], many=True).data == []
    assert UserMetaSerializer([], many=True).data == []


def test_serializing_dict(user):
    user = {"name": "foo", "email": "foo", "age": 42.3}
    s = UserSerializer(user)
    assert s.data['name'] == "foo"
    assert s.data['age'] == 42.3
    assert s.is_valid(['email']) is False

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_exclude_in_init(SerializerClass, user):
    s = SerializerClass(user, exclude=('age', 'homepage'))
    assert 'homepage' not in s.data
    assert 'age' not in s.data
    assert 'name' in s.data

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_only_in_init(SerializerClass, user):
    s = SerializerClass(user, only=('name', 'age'))
    assert 'homepage' not in s.data
    assert 'name' in s.data
    assert 'age' in s.data

def test_invalid_only_param(user):
    with pytest.raises(AttributeError):
        UserSerializer(user, only=("_invalid", "name"))

def test_strict_init():
    invalid = User("Foo", email="foo.com")
    with pytest.raises(MarshallingError):
        UserSerializer(invalid, strict=True)

def test_strict_meta_option():
    class StrictUserSerializer(UserSerializer):
        class Meta:
            strict = True
    invalid = User("Foo", email="foo.com")
    with pytest.raises(MarshallingError):
        StrictUserSerializer(invalid)

def test_can_serialize_uuid(serialized_user, user):
    assert serialized_user.data['uid'] == str(user.uid)

def test_can_serialize_time(user, serialized_user):
    expected = user.time_registered.isoformat()[:12]
    assert serialized_user.data['time_registered'] == expected

def test_invalid_time():
    u = User('Joe', time_registered='foo')
    s = UserSerializer(u)
    assert s.is_valid(['time_registered']) is False
    assert s.errors['time_registered'] == "'foo' cannot be formatted as a time."

def test_invalid_date():
    u = User("Joe", birthdate='foo')
    s = UserSerializer(u)
    assert s.is_valid(['birthdate']) is False
    assert s.errors['birthdate'] == "'foo' cannot be formatted as a date."

def test_invalid_selection():
    u = User('Jonhy')
    u.sex = 'hybrid'
    s = UserSerializer(u)
    assert s.is_valid(['sex']) is False
    assert s.errors['sex'] == "'hybrid' is not a valid choice for this field."

def test_custom_json():
    class UserJSONSerializer(Serializer):
        name = fields.String()
        class Meta:
            json_module = mockjson

    user = User('Joe')
    s = UserJSONSerializer(user)
    assert s.json == mockjson.dumps('val')


def test_custom_error_message():
    class ErrorSerializer(Serializer):
        email = fields.Email(error="Invalid email")
        homepage = fields.Url(error="Bad homepage.")
        balance = fields.Fixed(error="Bad balance.")

    u = User("Joe", email="joe.net", homepage="joe@example.com", balance="blah")
    s = ErrorSerializer(u)
    assert s.is_valid() is False
    assert s.errors['email'] == "Invalid email"
    assert s.errors['homepage'] == "Bad homepage."
    assert s.errors['balance'] == "Bad balance."


def test_error_raised_if_fields_option_is_not_list():
    class BadSerializer(Serializer):
        name = fields.String()

        class Meta:
            fields = 'name'

    u = User('Joe')
    with pytest.raises(ValueError):
        BadSerializer(u)


def test_error_raised_if_additional_option_is_not_list():
    class BadSerializer(Serializer):
        name = fields.String()

        class Meta:
            additional = 'email'

    u = User('Joe')
    with pytest.raises(ValueError):
        BadSerializer(u)


def test_meta_serializer_fields():
    u = User("John", age=42.3, email="john@example.com",
             homepage="http://john.com")
    s = UserMetaSerializer(u)
    assert s.data['name'] == u.name
    assert s.data['balance'] == "100.00"
    assert s.data['uppername'] == "JOHN"
    assert s.data['is_old'] is False
    assert s.data['created'] == utils.rfcformat(u.created)
    assert s.data['updated_local'] == utils.rfcformat(u.updated, localtime=True)
    assert s.data['finger_count'] == 10


def test_meta_fields_mapping(user):
    s = UserMetaSerializer(user)
    assert type(s.fields['name']) == fields.String
    assert type(s.fields['created']) == fields.DateTime
    assert type(s.fields['updated']) == fields.DateTime
    assert type(s.fields['updated_local']) == fields.LocalDateTime
    assert type(s.fields['age']) == fields.Float
    assert type(s.fields['balance']) == fields.Price
    assert type(s.fields['registered']) == fields.Boolean
    assert type(s.fields['sex_choices']) == fields.Raw
    assert type(s.fields['hair_colors']) == fields.Raw
    assert type(s.fields['finger_count']) == fields.Integer
    assert type(s.fields['uid']) == fields.UUID
    assert type(s.fields['time_registered']) == fields.Time
    assert type(s.fields['birthdate']) == fields.Date
    assert type(s.fields['since_created']) == fields.TimeDelta


def test_meta_field_not_on_obj_raises_attribute_error(user):
    class BadUserSerializer(Serializer):
        class Meta:
            fields = ('name', 'notfound')
    with pytest.raises(AttributeError):
        BadUserSerializer(user)

def test_exclude_fields(user):
    s = UserExcludeSerializer(user)
    assert "created" not in s.data
    assert "updated" not in s.data
    assert "name" in s.data

def test_fields_option_must_be_list_or_tuple(user):
    class BadFields(Serializer):
        class Meta:
            fields = "name"
    with pytest.raises(ValueError):
        BadFields(user)

def test_exclude_option_must_be_list_or_tuple(user):
    class BadExclude(Serializer):
        class Meta:
            exclude = "name"
    with pytest.raises(ValueError):
        BadExclude(user)

def test_dateformat_option(user):
    format = '%Y-%m'

    class DateFormatSerializer(Serializer):
        updated = fields.DateTime("%m-%d")

        class Meta:
            fields = ('created', 'updated')
            dateformat = format
    serialized = DateFormatSerializer(user)
    assert serialized.data['created'] == user.created.strftime(format)
    assert serialized.data['updated'] == user.updated.strftime("%m-%d")

def test_default_dateformat(user):
    class DateFormatSerializer(Serializer):
        updated = fields.DateTime(format="%m-%d")

        class Meta:
            fields = ('created', 'updated')
    serialized = DateFormatSerializer(user)
    assert serialized.data['created'] == utils.rfcformat(user.created)
    assert serialized.data['updated'] == user.updated.strftime("%m-%d")

def test_inherit_meta(user):
    class InheritedMetaSerializer(UserMetaSerializer):
        pass
    result = InheritedMetaSerializer(user).data
    expected = UserMetaSerializer(user).data
    assert result == expected

def test_additional(user):
    s = UserAdditionalSerializer(user)
    assert s.data['lowername'] == user.name.lower()
    assert s.data['name'] == user.name

def test_cant_set_both_additional_and_fields(user):
    class BadSerializer(Serializer):
        name = fields.String()

        class Meta:
            fields = ("name", 'email')
            additional = ('email', 'homepage')
    with pytest.raises(ValueError):
        BadSerializer(user)

def test_serializing_none_meta():
    s = UserMetaSerializer(None)
    # Since meta fields are used, defaults to None
    assert s.data['name'] is None
    assert s.data['email'] is None


class TestNestedSerializer(unittest.TestCase):
    def setUp(self):
        self.user = User(name="Monty", age=81)
        col1 = User(name="Mick", age=123)
        col2 = User(name="Keith", age=456)
        self.blog = Blog("Monty's blog", user=self.user, categories=["humor", "violence"],
                         collaborators=[col1, col2])

    def test_flat_nested(self):
        class FlatBlogSerializer(Serializer):
            name = fields.String()
            user = fields.Nested(UserSerializer, only='name')
            collaborators = fields.Nested(UserSerializer, only='name', many=True)
        s = FlatBlogSerializer(self.blog)
        assert s.data['user'] == self.blog.user.name
        assert s.data['collaborators'][0] == self.blog.collaborators[0].name

    def test_flat_nested2(self):
        class FlatBlogSerializer(Serializer):
            name = fields.String()
            collaborators = fields.Nested(UserSerializer, many=True, only='uid')

        s = FlatBlogSerializer(self.blog)
        assert s.data['collaborators'][0] == str(self.blog.collaborators[0].uid)

    def test_nested(self):
        serialized_blog = BlogSerializer(self.blog)
        serialized_user = UserSerializer(self.user)
        assert serialized_blog.data['user'] == serialized_user.data

    def test_nested_many_fields(self):
        serialized_blog = BlogSerializer(self.blog)
        expected = [UserSerializer(col).data for col in self.blog.collaborators]
        assert serialized_blog.data['collaborators'] == expected

    def test_nested_meta_many(self):
        serialized_blog = BlogUserMetaSerializer(self.blog)
        assert len(serialized_blog.data['collaborators']) == 2
        expected = [UserMetaSerializer(col).data for col in self.blog.collaborators]
        assert serialized_blog.data['collaborators'] == expected

    def test_nested_only(self):
        col1 = User(name="Mick", age=123, id_="abc")
        col2 = User(name="Keith", age=456, id_="def")
        self.blog.collaborators = [col1, col2]
        serialized_blog = BlogSerializerOnly(self.blog)
        assert serialized_blog.data['collaborators'] == [{"id": col1.id}, {"id": col2.id}]

    def test_exclude(self):
        serialized = BlogSerializerExclude(self.blog)
        assert "uppername" not in serialized.data['user'].keys()

    def test_only_takes_precedence_over_exclude(self):
        serialized = BlogSerializerOnlyExclude(self.blog)
        assert serialized.data['user']['name'] == self.user.name

    def test_list_field(self):
        serialized = BlogSerializer(self.blog)
        assert serialized.data['categories'] == ["humor", "violence"]

    def test_nested_errors(self):
        invalid_user = User("Monty", email="foo")
        blog = Blog("Monty's blog", user=invalid_user)
        serialized_blog = BlogSerializer(blog)
        assert serialized_blog.is_valid() is False
        assert "email" in serialized_blog.errors['user']
        expected_msg = "\"{0}\" is not a valid email address.".format(invalid_user.email)
        assert serialized_blog.errors['user']['email'] == expected_msg
        # No problems with collaborators
        assert "collaborators" not in serialized_blog.errors

    def test_nested_method_field(self):
        s = BlogSerializer(self.blog)
        assert s.data['user']['is_old']
        assert s.data['collaborators'][0]['is_old']

    def test_nested_function_field(self):
        s = BlogSerializer(self.blog)
        assert s.data['user']['lowername'] == self.user.name.lower()
        expected = self.blog.collaborators[0].name.lower()
        assert s.data['collaborators'][0]['lowername'] == expected

    def test_nested_prefixed_field(self):
        s = BlogSerializerPrefixedUser(self.blog)
        assert s.data['user']['usr_name'] == self.user.name
        assert s.data['user']['usr_lowername'] == self.user.name.lower()

    def test_nested_prefixed_many_field(self):
        s = BlogSerializerPrefixedUser(self.blog)
        assert s.data['collaborators'][0]['usr_name'] == self.blog.collaborators[0].name

    def test_invalid_float_field(self):
        user = User("Joe", age="1b2")
        s = UserSerializer(user)
        assert s.is_valid(["age"]) is False
        assert "age" in s.errors

    def test_serializer_meta_with_nested_fields(self):
        s = BlogSerializerMeta(self.blog)
        assert s.data['title'] == self.blog.title
        assert s.data['user'] == UserSerializer(self.user).data
        assert s.data['collaborators'] == [UserSerializer(c).data
                                               for c in self.blog.collaborators]
        assert s.data['categories'] == self.blog.categories

    def test_serializer_with_nested_meta_fields(self):
        # Serializer has user = fields.Nested(UserMetaSerializer)
        s = BlogUserMetaSerializer(self.blog)
        assert s.data['user'] == UserMetaSerializer(self.blog.user).data

    def test_nested_fields_must_be_passed_a_serializer(self):
        class BadNestedFieldSerializer(BlogSerializer):
            user = fields.Nested(fields.String)
        with pytest.raises(ValueError):
            BadNestedFieldSerializer(self.blog)


class TestSelfReference(unittest.TestCase):
    def setUp(self):
        self.employer = User(name="Joe", age=59)
        self.user = User(name="Tom", employer=self.employer, age=28)

    def test_nesting_serializer_within_itself(self):
        class SelfSerializer(Serializer):
            name = fields.String()
            age = fields.Integer()
            employer = fields.Nested("self")

        s = SelfSerializer(self.user)
        assert s.is_valid()
        assert s.data['name'] == self.user.name
        assert s.data['employer']['name'] == self.employer.name
        assert s.data['employer']['age'] == self.employer.age

    def test_nesting_within_itself_meta(self):
        class SelfSerializer(Serializer):
            employer = fields.Nested("self")

            class Meta:
                additional = ('name', 'age')

        s = SelfSerializer(self.user)
        assert s.is_valid()
        assert s.data['name'] == self.user.name
        assert s.data['age'] == self.user.age
        assert s.data['employer']['name'] == self.employer.name
        assert s.data['employer']['age'] == self.employer.age

    def test_nested_self_with_only_param(self):
        class SelfSerializer(Serializer):
            employer = fields.Nested('self', only=('name', ))

            class Meta:
                fields = ('name', 'employer')

        s = SelfSerializer(self.user)
        assert s.data['name'] == self.user.name
        assert s.data['employer']['name'] == self.employer.name
        assert 'age' not in s.data['employer']

    def test_nested_many(self):
        class SelfManySerializer(Serializer):
            relatives = fields.Nested('self', many=True)

            class Meta:
                additional = ('name', 'age')

        person = User(name='Foo')
        person.relatives = [User(name="Bar", age=12), User(name='Baz', age=34)]
        s = SelfManySerializer(person)
        assert s.data['name'] == person.name
        assert len(s.data['relatives']) == len(person.relatives)
        assert s.data['relatives'][0]['name'] == person.relatives[0].name
        assert s.data['relatives'][0]['age'] == person.relatives[0].age


class TestFields(unittest.TestCase):
    def setUp(self):
        self.user = User("Foo", "foo@bar.com")

    def test_repr(self):
        field = fields.String()
        assert repr(field) == "<String Field>"

    def test_function_field(self):
        field = fields.Function(lambda obj: obj.name.upper())
        assert "FOO" == field.output("key", self.user)

    def test_function_with_uncallable_param(self):
        with pytest.raises(MarshallingError):
            fields.Function("uncallable")

    def test_method_field_with_method_missing(self):
        class BadSerializer(Serializer):
            bad_field = fields.Method('invalid')
        u = User('Foo')
        with pytest.raises(MarshallingError):
            BadSerializer(u, strict=True)

    def test_method_field_with_uncallable_attribute(self):
        class BadSerializer(Serializer):
            foo = 'not callable'
            bad_field = fields.Method('foo')
        u = User('Foo')
        with pytest.raises(MarshallingError):
            BadSerializer(u, strict=True)

    def test_datetime_field(self):
        field = fields.DateTime()
        expected = utils.rfcformat(self.user.created, localtime=False)
        assert field.output("created", self.user) == expected

    def test_localdatetime_field(self):
        field = fields.LocalDateTime()
        expected = utils.rfcformat(self.user.created, localtime=True)
        assert field.output("created", self.user) == expected

    def test_datetime_iso8601(self):
        field = fields.DateTime(format="iso")
        expected = utils.isoformat(self.user.created, localtime=False)
        assert field.output("created", self.user) == expected

    def test_localdatetime_iso(self):
        field = fields.LocalDateTime(format="iso")
        expected = utils.isoformat(self.user.created, localtime=True)
        assert field.output("created", self.user) == expected

    def test_datetime_format(self):
        format = "%Y-%m-%d"
        field = fields.DateTime(format=format)
        assert field.output("created", self.user) == self.user.created.strftime(format)

    def test_string_field_defaults_to_empty_string(self):
        field = fields.String()
        assert field.output("notfound", self.user) == ''

    def test_time_field(self):
        field = fields.Time()
        expected = self.user.time_registered.isoformat()[:12]
        assert field.output("time_registered", self.user) == expected

    def test_date_field(self):
        field = fields.Date()
        assert field.output('birthdate', self.user) == self.user.birthdate.isoformat()

    def test_timedelta_field(self):
        field = fields.TimeDelta()
        expected = total_seconds(self.user.since_created)
        assert field.output("since_created", self.user) == expected

    def test_select_field(self):
        field = fields.Select(['male', 'female'])
        assert field.output("sex", self.user) == "male"
        invalid = User('foo', sex='alien')
        with pytest.raises(MarshallingError):
            field.output('sex', invalid)

    def test_bad_list_field(self):
        with pytest.raises(MarshallingError):
            fields.List("string")
        with pytest.raises(MarshallingError):
            fields.List(UserSerializer)


class TestValidation(unittest.TestCase):

    def test_integer_with_validator(self):
        user = User(name='Joe', age='20')
        field = fields.Integer(validate=lambda x: 18 <= x <= 24)
        out = field.output('age', user)
        assert out == 20
        user2 = User(name='Joe', age='25')
        with pytest.raises(MarshallingError):
            field.output('age', user2)

    def test_float_with_validator(self):
        user = User(name='Joe', age=3.14)
        field = fields.Float(validate=lambda f: f <= 4.1)
        assert field.output('age', user) == user.age
        invalid = User('foo', age=5.1)
        with pytest.raises(MarshallingError):
            field.output('age', invalid)

    def test_string_validator(self):
        user = User(name='Joe')
        field = fields.String(validate=lambda n: len(n) == 3)
        assert field.output('name', user) == 'Joe'
        user2 = User(name='Joseph')
        with pytest.raises(MarshallingError):
            field.output('name', user2)

    def test_datetime_validator(self):
        user = User('Joe', birthdate=dt.datetime(2014, 8, 21))
        field = fields.DateTime(validate=lambda d: utils.from_rfc(d).year == 2014)
        assert field.output('birthdate', user) == utils.rfcformat(user.birthdate)
        user2 = User('Joe', birthdate=dt.datetime(2013, 8, 21))
        with pytest.raises(MarshallingError):
            field.output('birthdate', user2)

    def test_function_validator(self):
        user = User('joe')
        field = fields.Function(lambda d: d.name.upper(),
                                validate=lambda n: len(n) == 3)
        assert field.output('uppername', user) == 'JOE'
        invalid = User(name='joseph')
        with pytest.raises(MarshallingError):
            field.output('uppername', invalid)

    def test_method_validator(self):
        class MethodSerializer(Serializer):
            uppername = fields.Method('get_uppername',
                                      validate=lambda n: len(n) == 3)

            def get_uppername(self, obj):
                return obj.name.upper()
        user = User('joe')
        s = MethodSerializer(user, strict=True)
        assert s.data['uppername'] == 'JOE'
        invalid = User(name='joseph')
        with pytest.raises(MarshallingError) as excinfo:
            MethodSerializer(invalid, strict=True)
        assert 'is not True' in str(excinfo)


@pytest.mark.parametrize('FieldClass', [
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
    fields.Fixed,
    fields.Url,
    fields.Email,
])
def test_required_field_failure(FieldClass):
    user_data = {"name": "Phil"}
    field = FieldClass(required=True)
    with pytest.raises(MarshallingError) as excinfo:
        field.output('age', user_data)
    assert "{0!r} is a required field".format('age') in str(excinfo)


@pytest.mark.parametrize(('FieldClass', 'value'), [
    (fields.String, ''),
    (fields.Integer, 0),
    (fields.Float, 0.0)
])
def test_required_field_falsy_is_ok(FieldClass, value):
    user_data = {'name': value}
    field = FieldClass(required=True)
    result = field.output('name', user_data)
    assert result  is not None
    assert result == value


def test_required_list_field_failure():
    user_data = {"name": "Rosie"}
    field = fields.List(fields.String, required=True)
    with pytest.raises(MarshallingError) as excinfo:
        field.output('relatives', user_data)
    assert '{0!r} is a required field'.format('relatives') in str(excinfo)


def test_serialization_with_required_field():
    class RequiredUserSerializer(Serializer):
        name = fields.String(required=True)

    user = User(name=None)
    s = RequiredUserSerializer(user)
    assert s.is_valid() is False
    assert 'name' in s.errors
    assert s.errors['name'] == '{0!r} is a required field.'.format('name')



class TestValidators(unittest.TestCase):
    def test_invalid_email(self):
        invalid1 = "user@example"
        with pytest.raises(ValueError):
            validate.email(invalid1)
        invalid2 = "example.com"
        with pytest.raises(ValueError):
            validate.email(invalid2)
        invalid3 = "user"
        with pytest.raises(ValueError):
            validate.email(invalid3)


class TestMarshaller(unittest.TestCase):
    def test_stores_errors(self):
        u = User("Foo", email="foobar")
        marshal = fields.Marshaller()
        marshal(u, {"email": fields.Email()})
        assert "email" in marshal.errors

    def test_strict_mode_raises_errors(self):
        u = User("Foo", email="foobar")
        marshal = fields.Marshaller(strict=True)
        with pytest.raises(MarshallingError):
            marshal(u, {"email": fields.Email()})

    def test_prefix(self):
        u = User("Foo", email="foo@bar.com")
        marshal = fields.Marshaller(prefix='usr_')
        result = marshal(u, {"email": fields.Email(), 'name': fields.String()})
        assert result['usr_name'] == u.name
        assert result['usr_email'] == u.email

    def test_marshalling_generator(self):
        gen = (u for u in [User("Foo"), User("Bar")])
        marshal = fields.Marshaller()
        res = marshal(gen, {"name": fields.String()}, many=True)
        assert len(res) == 2


class UserContextSerializer(Serializer):
    is_owner = fields.Method('get_is_owner')
    is_collab = fields.Function(lambda user, ctx: user in ctx['blog'])

    def get_is_owner(self, user, context):
        return context['blog'].user.name == user.name


class TestContext(unittest.TestCase):

    def test_context_method(self):
        owner = User('Joe')
        blog = Blog(title='Joe Blog', user=owner)
        context = {'blog': blog}
        s = UserContextSerializer(owner, context=context)
        assert s.data['is_owner'] is True
        nonowner = User('Fred')
        s = UserContextSerializer(nonowner, context=context)
        assert s.data['is_owner'] is False

    def test_context_method_function(self):
        owner = User('Fred')
        blog = Blog('Killer Queen', user=owner)
        collab = User('Brian')
        blog.collaborators.append(collab)
        context = {'blog': blog}
        s = UserContextSerializer(collab, context=context)
        assert s.data['is_collab'] is True
        noncollab = User('Foo')
        result = UserContextSerializer(noncollab, context=context).data['is_collab']
        assert result is False

    def test_function_field_raises_error_when_context_not_available(self):
        owner = User('Joe')
        # no context
        with pytest.raises(MarshallingError):
            UserContextSerializer(owner, strict=True)

if __name__ == '__main__':
    unittest.main()
