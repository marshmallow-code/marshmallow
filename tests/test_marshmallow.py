#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
import datetime as dt

from nose.tools import *  # PEP8 asserts
import pytz

from marshmallow import Serializer, fields, types, pprint
from marshmallow.compat import LINUX, unicode

central = pytz.timezone("US/Central")

##### Models #####

class User(object):
    SPECIES = "Homo sapiens"

    def __init__(self, name, age=0, id_=None, homepage=None, email=None):
        self.name = name
        self.age = age
        # A naive datetime
        self.created = dt.datetime(2013, 11, 10, 14, 20, 58)
        # A TZ-aware datetime
        self.updated = central.localize(dt.datetime(2013, 11, 10, 14, 20, 58), is_dst=False)
        self.id = id_
        self.homepage = homepage
        self.email = email
        self.balance = 100

    @property
    def is_old(self):
        return self.age > 80

class Blog(object):

    def __init__(self, title, user, collaborators=None, categories=None):
        self.title = title
        self.user = user
        self.collaborators = collaborators  # List/tuple of users
        self.categories = categories

###### Serializers #####

class Uppercased(fields.Raw):
    '''Custom field formatting example.'''
    def format(self, value):
        return value.upper()


class UserSerializer(Serializer):
    name = fields.String()
    age = fields.Float()
    created = fields.DateTime()
    updated = fields.DateTime()
    updated_local = fields.LocalDateTime(attribute="updated")
    species = fields.String(attribute="SPECIES")
    id = fields.String(default="no-id")
    uppername = Uppercased(attribute='name')
    homepage = fields.Url()
    email = fields.Email()
    balance = fields.Price()

    is_old = fields.Method("get_is_old")

    def get_is_old(self, obj):
        return obj.age > 80

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


class BlogSerializer(Serializer):
    title = fields.String()
    user = fields.Nested(UserSerializer)
    collaborators = fields.Nested(UserSerializer)
    categories = fields.List(fields.String)


class BlogSerializerOnly(Serializer):
    title = fields.String()
    user = fields.Nested(UserSerializer)
    collaborators = fields.Nested(UserSerializer, only=("id", ))

class BlogSerializerExclude(BlogSerializer):
    user = fields.Nested(UserSerializer, exclude=("uppername", "species"))

class BlogSerializerOnlyExclude(BlogSerializer):
    user = fields.Nested(UserSerializer, only=("name", ), exclude=("name", "species"))

##### The Tests #####


class TestSerializer(unittest.TestCase):

    def setUp(self):
        self.obj = User(name="Monty", age=42.3, homepage="http://monty.python.org/")
        self.serialized = UserSerializer(self.obj)

    def test_serializing_basic_object(self):
        assert_equal(self.serialized.data['name'], "Monty")
        assert_almost_equal(self.serialized.data['age'], 42.3)

    def test_fields_are_copies(self):
        s = UserSerializer(User("Monty", age=42))
        s2 = UserSerializer(User("Monty", age=43))
        assert_true(s.fields is not s2.fields)

    def test_json(self):
        json_data = self.serialized.json
        reloaded = json.loads(json_data)
        assert_almost_equal(reloaded['age'], 42.3)

    def test_naive_datetime_field(self):
        assert_equal(self.serialized.data['created'],
                    'Sun, 10 Nov 2013 14:20:58 -0000')

    def test_tz_datetime_field(self):
        # Datetime is corrected back to GMT
        assert_equal(self.serialized.data['updated'],
                    'Sun, 10 Nov 2013 20:20:58 -0000')

    @unittest.skipIf(LINUX, "Skip due to different localtime behavior on Linux")
    def test_local_datetime_field(self):
        assert_equal(self.serialized.data['updated_local'],
                    'Sun, 10 Nov 2013 14:20:58 -0600')

    def test_class_variable(self):
        assert_equal(self.serialized.data['species'], 'Homo sapiens')

    def test_serialize_many(self):
        user1 = User(name="Mick", age=123)
        user2 = User(name="Keith", age=456)
        users = [user1, user2]
        serialized = UserSerializer(users)
        assert_equal(len(serialized.data), 2)
        assert_equal(serialized.data[0]['name'], "Mick")
        assert_equal(serialized.data[1]['name'], "Keith")

    def test_inheriting_serializer(self):
        serialized = ExtendedUserSerializer(self.obj)
        assert_equal(serialized.data['name'], self.obj.name)
        assert_false(serialized.data['is_old'])

    def test_custom_field(self):
        assert_equal(self.serialized.data['uppername'], "MONTY")

    def test_url_field(self):
        assert_equal(self.serialized.data['homepage'], "http://monty.python.org/")

    def test_stores_invalid_url_error(self):
        user = User(name="John Doe", homepage="www.foo.com")
        serialized = UserSerializer(user)
        assert_in("homepage", serialized.errors)
        assert_equal(serialized.errors['homepage'],
            'www.foo.com is not a valid URL. Did you mean: "http://www.foo.com"?')

    def test_default(self):
        user = User("John")  # No ID set
        serialized = UserSerializer(user)
        assert_equal(serialized.data['id'], "no-id")

    def test_email_field(self):
        u = User("John", email="john@example.com")
        s = UserSerializer(u)
        assert_equal(s.data['email'], "john@example.com")

    def test_stored_invalid_email(self):
        u = User("John", email="johnexample.com")
        s = UserSerializer(u)
        assert_in("email", s.errors)
        assert_equal(s.errors['email'], "johnexample.com is not a valid email address.")

    def test_integer_field(self):
        u = User("John", age=42.3)
        serialized = UserIntSerializer(u)
        assert_equal(type(serialized.data['age']), int)
        assert_equal(serialized.data['age'], 42)

    def test_fixed_field(self):
        u = User("John", age=42.3)
        serialized = UserFixedSerializer(u)
        assert_equal(serialized.data['age'], "42.30")

    def test_as_string(self):
        u = User("John", age=42.3)
        serialized = UserFloatStringSerializer(u)
        assert_equal(serialized.data['age'], "42.3")

    def test_decimal_field(self):
        u = User("John", age=42.3)
        s = UserDecimalSerializer(u)
        assert_equal(type(s.data['age']), unicode)
        assert_almost_equal(float(s.data['age']), 42.3)

    def test_price_field(self):
        assert_equal(self.serialized.data['balance'], "100.00")

    def test_validate(self):
        valid = User("Joe", email="joe@foo.com")
        invalid = User("John", email="johnexample.com")
        assert_true(UserSerializer(valid).is_valid())
        assert_false(UserSerializer(invalid).is_valid())

    def test_validate_field(self):
        invalid = User("John", email="johnexample.com")
        assert_true(UserSerializer(invalid).is_valid(["name"]))
        assert_false(UserSerializer(invalid).is_valid(["email"]))

    def test_fields_param_must_be_list_or_tuple(self):
        with assert_raises(ValueError):
            invalid = User("John", email="johnexample.com")
            UserSerializer(invalid).is_valid("name")

    def test_extra(self):
        user = User("Joe", email="joe@foo.com")
        s = UserSerializer(user, extra={"fav_color": "blue"})
        assert_equal(s.data['fav_color'], "blue")

    def test_method_field(self):
        assert_false(self.serialized.data['is_old'])
        u = User("Joe", age=81)
        assert_true(UserSerializer(u).data['is_old'])


class TestNestedSerializer(unittest.TestCase):

    def setUp(self):
        self.user = User(name="Monty", age=81)
        self.blog = Blog("Monty's blog", user=self.user, categories=["humor", "violence"])

    def test_nested(self):
        serialized_blog = BlogSerializer(self.blog)
        serialized_user = UserSerializer(self.user)
        assert_equal(serialized_blog.data['user'], serialized_user.data)

    def test_nested_many_fields(self):
        col1 = User(name="Mick", age=123)
        col2 = User(name="Keith", age=456)
        self.blog.collaborators = [col1, col2]
        serialized_blog = BlogSerializer(self.blog)
        assert_equal(serialized_blog.data['collaborators'],
            [UserSerializer(col1).data, UserSerializer(col2).data])

    def test_nested_only(self):
        col1 = User(name="Mick", age=123, id_="abc")
        col2 = User(name="Keith", age=456, id_="def")
        self.blog.collaborators = [col1, col2]
        serialized_blog = BlogSerializerOnly(self.blog)
        assert_equal(serialized_blog.data['collaborators'],
                    [{"id": col1.id}, {"id": col2.id}])

    def test_exclude(self):
        serialized = BlogSerializerExclude(self.blog)
        assert_not_in("uppername", serialized.data['user'].keys())

    def test_only_takes_precedence_over_exclude(self):
        serialized = BlogSerializerOnlyExclude(self.blog)
        assert_equal(serialized.data['user']['name'], self.user.name)

    def test_list_field(self):
        serialized = BlogSerializer(self.blog)
        assert_equal(serialized.data['categories'], ["humor", "violence"])

    def test_nested_errors(self):
        invalid_user = User("Monty", email="foo")
        blog = Blog("Monty's blog", user=invalid_user)
        serialized_blog = BlogSerializer(blog)
        assert_false(serialized_blog.is_valid())

    def test_nested_method_field(self):
        s = BlogSerializer(self.blog)
        assert_true(s.data['user']['is_old'])

class TestFields(unittest.TestCase):

    def test_repr(self):
        field = fields.String()
        assert_equal(repr(field), "<String Field>")


class TestTypes(unittest.TestCase):

    def test_rfc822_gmt_naive(self):
        d = dt.datetime(2013, 11, 10, 1, 23, 45)
        assert_equal(types.rfc822(d), "Sun, 10 Nov 2013 01:23:45 -0000")

    @unittest.skipIf(LINUX, "Skip due to different localtime behavior on Linux")
    def test_rfc822_central(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
        assert_equal(types.rfc822(d), 'Sun, 10 Nov 2013 07:23:45 -0000')

    @unittest.skipIf(LINUX, "Skip due to different localtime behavior on Linux")
    def test_rfc822_central_localized(self):
        d = central.localize(dt.datetime(2013, 11, 10, 8, 23, 45), is_dst=False)
        assert_equal(types.rfc822(d, localtime=True), "Sun, 10 Nov 2013 08:23:45 -0600")


if __name__ == '__main__':
    unittest.main()
