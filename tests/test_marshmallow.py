#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
import datetime as dt
from collections import OrderedDict

from nose.tools import *  # PEP8 asserts
import pytz

from marshmallow import Serializer, fields, types

central = pytz.timezone("US/Central")

##### Models #####

class User(object):
    SPECIES = "Homo sapiens"

    def __init__(self, name, age, id_=None):
        self.name = name
        self.age = age
        # A naive datetime
        self.created = dt.datetime(2013, 11, 10, 14, 20, 58)
        # A TZ-aware datetime
        self.updated = central.localize(dt.datetime(2013, 11, 10, 14, 20, 58))
        self.id = id_

class Blog(object):

    def __init__(self, title, user, collaborators=None):
        self.title = title
        self.user = user
        self.collaborators = collaborators  # List/tuple of users

###### Serializers #####

class UserSerializer(Serializer):
    FIELDS = {
        "name": fields.String,
        "age": fields.Float,
        "created": fields.DateTime,
        "updated": fields.DateTime,
        "updated_local": fields.LocalDateTime(attribute="updated"),
        'species': fields.String(attribute="SPECIES"),
        "id": fields.String
    }

class UserSerializerOrdered(Serializer):
    FIELDS = OrderedDict([
        ("name", fields.String),
        ("age", fields.Float)
    ])

class BlogSerializer(Serializer):
    FIELDS = {
        "title": fields.String,
        "user": fields.Nested(UserSerializer),
        "collaborators": fields.Nested(UserSerializer)
    }

class BlogSerializerOnly(Serializer):
    FIELDS = {
        "title": fields.String,
        "user": fields.Nested(UserSerializer),
        "collaborators": fields.Nested(UserSerializer, only=("id", ))
    }

##### The Tests #####


class TestSerializer(unittest.TestCase):

    def setUp(self):
        self.obj = User(name="Monty", age=42.3)
        self.serialized = UserSerializer(self.obj)

    def test_serializing_basic_object(self):
        assert_equal(self.serialized.data['name'], "Monty")
        assert_equal(self.serialized.data['age'], "42.3")

    def test_json(self):
        json_data = self.serialized.json
        reloaded = json.loads(json_data)
        assert_equal(reloaded['age'], '42.3')

    def test_naive_datetime_field(self):
        assert_equal(self.serialized.data['created'],
                    'Sun, 10 Nov 2013 14:20:58 -0000')

    def test_tz_datetime_field(self):
        # Datetime is corrected back to GMT
        assert_equal(self.serialized.data['updated'],
                    "Sun, 10 Nov 2013 20:20:58 -0000")

    def test_local_datetime_field(self):
        assert_equal(self.serialized.data['updated_local'],
                    'Sun, 10 Nov 2013 14:20:58 -0600')

    def test_class_variable(self):
        assert_equal(self.serialized.data['species'], 'Homo sapiens')

    def test_ordered_dict_fields(self):
        serialized = UserSerializerOrdered(self.obj)
        expected = OrderedDict([("name", "Monty"), ("age", "42.3")])
        assert_equal(serialized.data, expected)

    def test_serialize_many(self):
        user1 = User(name="Mick", age=123)
        user2 = User(name="Keith", age=456)
        users = [user1, user2]
        serialized = UserSerializer(users)
        assert_equal(len(serialized.data), 2)
        assert_equal(serialized.data[0]['name'], "Mick")
        assert_equal(serialized.data[1]['name'], "Keith")


class TestNestedSerializer(unittest.TestCase):

    def setUp(self):
        self.user = User(name="Monty", age=42)
        self.blog = Blog("Monty's blog", user=self.user)


    def test_nested(self):
        serialized_blog = BlogSerializer(self.blog)
        serialized_user = UserSerializer(self.user)
        assert_equal(serialized_blog.data['user'], serialized_user.data)

    def test_nested_many_fields(self):
        col1 = User(name="Mick", age=123)
        col2 = User(name="Keith", age=456)
        self.blog.collaborators =[col1, col2]
        serialized_blog = BlogSerializer(self.blog)
        assert_equal(serialized_blog.data['collaborators'],
            [UserSerializer(col1).data, UserSerializer(col2).data])

    def test_nested_only(self):
        col1 = User(name="Mick", age=123, id_="abc")
        col2 = User(name="Keith", age=456, id_="def")
        self.blog.collaborators = [col1, col2]
        serialized_blog = BlogSerializerOnly(self.blog)
        assert_equal(serialized_blog.data['collaborators'], [{"id": "abc"}, {"id": "def"}])


class TestTypes(unittest.TestCase):

    def test_rfc822_gmt_naive(self):
        d = dt.datetime(2013, 11, 10, 1, 23, 45)
        assert_equal(types.rfc822(d), "Sun, 10 Nov 2013 01:23:45 -0000")

    def test_rfc822_cental(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45))
        assert_equal(types.rfc822(d), "Sun, 10 Nov 2013 07:23:45 -0000")

    def test_rfc822_cental_localized(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45))
        assert_equal(types.rfc822(d, localtime=True), "Sun, 10 Nov 2013 01:23:45 -0600")


if __name__ == '__main__':
    unittest.main()
