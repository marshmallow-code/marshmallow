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


class TestSerializer(unittest.TestCase):

    def setUp(self):
        self.obj = User(name="Monty", age=42.3, homepage="http://monty.python.org/")
        self.serialized = UserSerializer(self.obj)

    def test_serializing_basic_object(self):
        assert self.serialized.data['name'] == "Monty"
        assert_almost_equal(self.serialized.data['age'], 42.3)
        assert self.serialized.data['registered']

    def test_serializing_none(self):
        s = UserSerializer(None)
        assert s.data['name'] == ''
        assert s.data['age'] == 0

    def test_fields_are_copies(self):
        s = UserSerializer(User("Monty", age=42))
        s2 = UserSerializer(User("Monty", age=43))
        assert s.fields is not s2.fields

    def test_json(self):
        json_data = self.serialized.json
        expected = binary_type(json.dumps(self.serialized.data).encode("utf-8"))
        assert json_data == expected

    def test_to_json_returns_bytestring(self):
        assert isinstance(self.serialized.to_json(), binary_type)

    def test_naive_datetime_field(self):
        assert self.serialized.data['created'] == 'Sun, 10 Nov 2013 14:20:58 -0000'

    def test_datetime_formatted_field(self):
        result = self.serialized.data['created_formatted']
        assert result == self.obj.created.strftime("%Y-%m-%d")

    def test_datetime_iso_field(self):
        assert self.serialized.data['created_iso'] == utils.isoformat(self.obj.created)

    def test_tz_datetime_field(self):
        # Datetime is corrected back to GMT
        assert self.serialized.data['updated'] == 'Sun, 10 Nov 2013 20:20:58 -0000'

    def test_local_datetime_field(self):
        assert self.serialized.data['updated_local'] == 'Sun, 10 Nov 2013 14:20:58 -0600'

    def test_class_variable(self):
        assert self.serialized.data['species'] == 'Homo sapiens'

    def test_serialize_many(self):
        user1 = User(name="Mick", age=123)
        user2 = User(name="Keith", age=456)
        users = [user1, user2]
        serialized = UserSerializer(users, many=True)
        assert len(serialized.data) == 2
        assert serialized.data[0]['name'] == "Mick"
        assert serialized.data[1]['name'] == "Keith"

    def test_no_implicit_list_handling(self):
        users = [User(name='Mick'), User(name='Keith')]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            with pytest.raises(TypeError):
                UserSerializer(users)
        assert issubclass(w[-1].category, DeprecationWarning)

    def test_serialize_many_with_meta(self):
        user1 = User(name="Mick", age=123)
        user2 = User(name="Keith", age=456)
        users = [user1, user2]
        s = UserMetaSerializer(users, many=True)
        assert len(s.data) == 2
        assert s.data[0]['name'] == "Mick"
        assert s.data[0]['created'] == utils.rfcformat(user1.created)
        assert s.data[1]['name'] == "Keith"

    def test_inheriting_serializer(self):
        serialized = ExtendedUserSerializer(self.obj)
        assert serialized.data['name'] == self.obj.name
        assert not serialized.data['is_old']

    def test_custom_field(self):
        assert self.serialized.data['uppername'] == "MONTY"

    def test_url_field(self):
        assert self.serialized.data['homepage'] == "http://monty.python.org/"

    def test_url_field_validation(self):
        invalid = User("John", age=42, homepage="/john")
        s = UserSerializer(invalid)
        assert s.is_valid(["homepage"]) is False

    def test_relative_url_field(self):
        u = User("John", age=42, homepage="/john")
        serialized = UserRelativeUrlSerializer(u)
        assert serialized.is_valid()

    def test_stores_invalid_url_error(self):
        user = User(name="John Doe", homepage="www.foo.com")
        serialized = UserSerializer(user)
        assert "homepage" in serialized.errors
        expected = '"www.foo.com" is not a valid URL. Did you mean: "http://www.foo.com"?'
        assert serialized.errors['homepage'] == expected

    def test_default(self):
        user = User("John")  # No ID set
        serialized = UserSerializer(user)
        assert serialized.data['id'] == "no-id"

    def test_email_field(self):
        u = User("John", email="john@example.com")
        s = UserSerializer(u)
        assert s.data['email'] == "john@example.com"

    def test_stored_invalid_email(self):
        u = User("John", email="johnexample.com")
        s = UserSerializer(u)
        assert "email" in s.errors
        assert s.errors['email'] == '"johnexample.com" is not a valid email address.'

    def test_integer_field(self):
        u = User("John", age=42.3)
        serialized = UserIntSerializer(u)
        assert type(serialized.data['age']) == int
        assert serialized.data['age'] == 42

    def test_integer_default(self):
        user = User("John", age=None)
        serialized = UserIntSerializer(user)
        assert type(serialized.data['age']) == int
        assert serialized.data['age'] == 0

    def test_fixed_field(self):
        u = User("John", age=42.3)
        serialized = UserFixedSerializer(u)
        assert serialized.data['age'] == "42.30"

    def test_as_string(self):
        u = User("John", age=42.3)
        serialized = UserFloatStringSerializer(u)
        assert type(serialized.data['age']) == str
        assert_almost_equal(float(serialized.data['age']), 42.3)

    def test_decimal_field(self):
        u = User("John", age=42.3)
        s = UserDecimalSerializer(u)
        assert type(s.data['age']) == unicode
        assert_almost_equal(float(s.data['age']), 42.3)

    def test_price_field(self):
        assert self.serialized.data['balance'] == "100.00"

    def test_validate(self):
        valid = User("Joe", email="joe@foo.com")
        invalid = User("John", email="johnexample.com")
        assert UserSerializer(valid).is_valid()
        assert UserSerializer(invalid).is_valid() is False

    def test_validate_field(self):
        invalid = User("John", email="johnexample.com")
        assert UserSerializer(invalid).is_valid(["name"]) is True
        assert UserSerializer(invalid).is_valid(["email"]) is False

    def test_validating_nonexistent_field_raises_error(self):
        with pytest.raises(KeyError):
            self.serialized.is_valid(["foobar"])

    def test_fields_param_must_be_list_or_tuple(self):
        invalid = User("John", email="johnexample.com")
        with pytest.raises(ValueError):
            UserSerializer(invalid).is_valid("name")

    def test_extra(self):
        user = User("Joe", email="joe@foo.com")
        s = UserSerializer(user, extra={"fav_color": "blue"})
        assert s.data['fav_color'] == "blue"

    def test_method_field(self):
        assert self.serialized.data['is_old'] is False
        u = User("Joe", age=81)
        assert UserSerializer(u).data['is_old'] is True

    def test_function_field(self):
        assert self.serialized.data['lowername'] == self.obj.name.lower()

    def test_prefix(self):
        s = UserSerializer(self.obj, prefix="usr_")
        assert s.data['usr_name'] == self.obj.name

    def test_fields_must_be_declared_as_instances(self):
        class BadUserSerializer(Serializer):
            name = fields.String
        with pytest.raises(TypeError):
            BadUserSerializer(self.obj)

    def test_serializing_generator(self):
        users = [User("Foo"), User("Bar")]
        user_gen = (u for u in users)
        s = UserSerializer(user_gen, many=True)
        assert len(s.data) == 2
        assert s.data[0] == UserSerializer(users[0]).data

    def test_serializing_generator_with_meta_fields(self):
        users = [User("Foo"), User("Bar")]
        user_gen = (u for u in users)
        s = UserMetaSerializer(user_gen, many=True)
        assert len(s.data), 2
        assert s.data[0], UserMetaSerializer(users[0]).data

    def test_serializing_empty_list_returns_empty_list(self):
        assert UserSerializer([], many=True).data == []
        assert UserMetaSerializer([], many=True).data == []

    def test_serializing_dict(self):
        user = {"name": "foo", "email": "foo", "age": 42.3}
        s = UserSerializer(user)
        assert s.data['name'] == "foo"
        assert s.data['age'] == 42.3
        assert s.is_valid(['email']) is False

    def test_exclude_in_init(self):
        s = UserSerializer(self.obj, exclude=('age', 'homepage'))
        assert 'homepage' not in s.data
        assert 'age' not in s.data
        assert 'name' in s.data

    def test_only_in_init(self):
        s = UserSerializer(self.obj, only=('name', 'age'))
        assert 'homepage' not in s.data
        assert 'name' in s.data
        assert 'age' in s.data

    def test_invalid_only_param(self):
        with pytest.raises(AttributeError):
            UserSerializer(self.obj, only=("_invalid", "name"))

    def test_strict_init(self):
        invalid = User("Foo", email="foo.com")
        with pytest.raises(MarshallingError):
            UserSerializer(invalid, strict=True)

    def test_strict_meta_option(self):
        class StrictUserSerializer(UserSerializer):
            class Meta:
                strict = True
        invalid = User("Foo", email="foo.com")
        with pytest.raises(MarshallingError):
            StrictUserSerializer(invalid)

    def test_can_serialize_uuid(self):
        assert self.serialized.data['uid'] == str(self.obj.uid)

    def test_can_serialize_time(self):
        expected = self.obj.time_registered.isoformat()[:12]
        assert self.serialized.data['time_registered'] == expected

    def test_invalid_time(self):
        u = User('Joe', time_registered='foo')
        s = UserSerializer(u)
        assert s.is_valid(['time_registered']) is False
        assert s.errors['time_registered'] == "'foo' cannot be formatted as a time."

    def test_invalid_date(self):
        u = User("Joe", birthdate='foo')
        s = UserSerializer(u)
        assert s.is_valid(['birthdate']) is False
        assert s.errors['birthdate'] == "'foo' cannot be formatted as a date."

    def test_invalid_selection(self):
        u = User('Jonhy')
        u.sex = 'hybrid'
        s = UserSerializer(u)
        assert s.is_valid(['sex']) is False
        assert s.errors['sex'] == "'hybrid' is not a valid choice for this field."

    def test_custom_json(self):
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


class TestMetaOptions(unittest.TestCase):
    def setUp(self):
        self.obj = User(name="Monty", age=42.3,
                        homepage="http://monty.python.org/")
        self.serialized = UserSerializer(self.obj)

    def test_meta_serializer_fields(self):
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

    def test_meta_fields_mapping(self):
        s = UserMetaSerializer(self.obj)
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

    def test_meta_field_not_on_obj_raises_attribute_error(self):
        class BadUserSerializer(Serializer):
            class Meta:
                fields = ('name', 'notfound')
        with pytest.raises(AttributeError):
            BadUserSerializer(self.obj)

    def test_exclude_fields(self):
        s = UserExcludeSerializer(self.obj)
        assert "created" not in s.data
        assert "updated" not in s.data
        assert "name" in s.data

    def test_fields_option_must_be_list_or_tuple(self):
        class BadFields(Serializer):
            class Meta:
                fields = "name"
        with pytest.raises(ValueError):
            BadFields(self.obj)

    def test_exclude_option_must_be_list_or_tuple(self):
        class BadExclude(Serializer):
            class Meta:
                exclude = "name"
        with pytest.raises(ValueError):
            BadExclude(self.obj)

    def test_dateformat_option(self):
        format = '%Y-%m'

        class DateFormatSerializer(Serializer):
            updated = fields.DateTime("%m-%d")

            class Meta:
                fields = ('created', 'updated')
                dateformat = format
        serialized = DateFormatSerializer(self.obj)
        assert serialized.data['created'] == self.obj.created.strftime(format)
        assert serialized.data['updated'] == self.obj.updated.strftime("%m-%d")

    def test_default_dateformat(self):
        class DateFormatSerializer(Serializer):
            updated = fields.DateTime(format="%m-%d")

            class Meta:
                fields = ('created', 'updated')
        serialized = DateFormatSerializer(self.obj)
        assert serialized.data['created'] == utils.rfcformat(self.obj.created)
        assert serialized.data['updated'] == self.obj.updated.strftime("%m-%d")

    def test_inherit_meta(self):
        class InheritedMetaSerializer(UserMetaSerializer):
            pass
        result = InheritedMetaSerializer(self.obj).data
        expected = UserMetaSerializer(self.obj).data
        assert result == expected

    def test_additional(self):
        s = UserAdditionalSerializer(self.obj)
        assert s.data['lowername'] == self.obj.name.lower()
        assert s.data['name'] == self.obj.name

    def test_cant_set_both_additional_and_fields(self):
        class BadSerializer(Serializer):
            name = fields.String()

            class Meta:
                fields = ("name", 'email')
                additional = ('email', 'homepage')
        with pytest.raises(ValueError):
            BadSerializer(self.obj)

    def test_serializing_none(self):
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
        with pytest.raises(MarshallingError):
            MethodSerializer(invalid, strict=True)


@pytest.mark.parametrize('FieldClass', [
    fields.String,
    fields.Integer,
    fields.Boolean,
    fields.Float,
])
def test_required_field_failure(FieldClass):
    user_data = {"name": "Phil"}
    field = FieldClass(required=True)
    with pytest.raises(MarshallingError) as excinfo:
        field.output('age', user_data)
    assert excinfo.value.message == "{0!r} is a required field".format('age')


def test_required_list_field_failure():
    user_data = {"name": "Rosie"}
    field = fields.List(fields.String, required=True)
    with pytest.raises(MarshallingError) as excinfo:
        field.output('relatives', user_data)
    assert excinfo.value.message == '{0!r} is a required field'.format('relatives')


class TestUtils(unittest.TestCase):
    def test_to_marshallable_type(self):
        class Foo(object):
            CLASS_VAR = 'bar'

            def __init__(self):
                self.attribute = 'baz'

            @property
            def prop(self):
                return 42

        obj = Foo()
        u_dict = utils.to_marshallable_type(obj)
        assert u_dict['CLASS_VAR'] == Foo.CLASS_VAR
        assert u_dict['attribute'] == obj.attribute
        assert u_dict['prop'] == obj.prop

    def test_to_marshallable_type_none(self):
        assert utils.to_marshallable_type(None) == None

    def test_to_marshallable_type_list(self):
        assert utils.to_marshallable_type(['foo', 'bar']) == ['foo', 'bar']

    def test_to_marshallable_type_generator(self):
        gen = (e for e in ['foo', 'bar'])
        assert utils.to_marshallable_type(gen) == ['foo', 'bar']

    def test_marshallable(self):
        class ObjContainer(object):
            contained = {"foo": 1}

            def __marshallable__(self):
                return self.contained

        obj = ObjContainer()
        assert utils.to_marshallable_type(obj) == {"foo": 1}

    def test_is_collection(self):
        assert utils.is_collection([1, 'foo', {}]) is True
        assert utils.is_collection(('foo', 2.3)) is True
        assert utils.is_collection({'foo': 'bar'}) is False

    def test_rfcformat_gmt_naive(self):
        d = dt.datetime(2013, 11, 10, 1, 23, 45)
        assert utils.rfcformat(d) == "Sun, 10 Nov 2013 01:23:45 -0000"

    def test_rfcformat_central(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
        assert utils.rfcformat(d) == 'Sun, 10 Nov 2013 07:23:45 -0000'

    def test_rfcformat_central_localized(self):
        d = central.localize(dt.datetime(2013, 11, 10, 8, 23, 45), is_dst=False)
        assert utils.rfcformat(d, localtime=True) == "Sun, 10 Nov 2013 08:23:45 -0600"

    def test_isoformat(self):
        d = dt.datetime(2013, 11, 10, 1, 23, 45)
        assert utils.isoformat(d) == '2013-11-10T01:23:45+00:00'

    def test_isoformat_tzaware(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
        assert utils.isoformat(d) == "2013-11-10T07:23:45+00:00"

    def test_isoformat_localtime(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
        assert utils.isoformat(d, localtime=True) == "2013-11-10T01:23:45-06:00"

    def test_from_rfc(self):
        d = dt.datetime.now()
        rfc = utils.rfcformat(d)
        output = utils.from_rfc(rfc)
        assert output.year == d.year
        assert output.month == d.month
        assert output.day == d.day


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
