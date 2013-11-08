#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
import datetime as dt

from nose.tools import *  # PEP8 asserts
import pytz

from marshmallow import Serializer, fields, types


class User(object):
    SPECIES = "Homo sapiens"

    def __init__(self, name, age):
        self.name = name
        self.age = age
        # A naive datetime
        self.created = dt.datetime(2013, 11, 10, 14, 20, 58)
        # A TZ-aware datetime
        central = pytz.timezone("US/Central")
        self.updated = central.localize(dt.datetime(2013, 11, 10, 14, 20, 58))


class UserSerializer(Serializer):
    FIELDS = {
        "name": fields.String,
        "age": fields.Float,
        "created": fields.DateTime,
        "updated": fields.DateTime
    }


class TestSerializer(unittest.TestCase):

    def setUp(self):
        self.obj = User(name="Monty", age=42.30)
        self.serialized = UserSerializer(self.obj)

    def test_serializing_basic_object(self):
        assert_equal(self.serialized.data['name'], "Monty")
        assert_equal(self.serialized.data['age'], "42.3")

    def test_json(self):
        json_data = self.serialized.json
        reloaded = json.loads(json_data)
        assert_equal(reloaded['age'], '42.3')

    def test_naive_datetime_field(self):
        assert_equal(self.serialized.data['created'], 'Sun, 10 Nov 2013 14:20:58 -0000')

    def test_tz_datetime_field(self):
        # Datetime is corrected back to GMT
        assert_equal(self.serialized.data['updated'], "Sun, 10 Nov 2013 20:20:58 -0000")

if __name__ == '__main__':
    unittest.main()
