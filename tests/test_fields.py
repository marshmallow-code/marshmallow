# -*- coding: utf-8 -*-
from marshmallow import fields

class TestFieldAliases:

    def test_enum_is_select(self):
        assert fields.Enum is fields.Select

    def test_int_is_integer(self):
        assert fields.Int is fields.Integer

    def test_str_is_string(self):
        assert fields.Str is fields.String

    def test_bool_is_boolean(self):
        assert fields.Bool is fields.Boolean
