# -*- coding: utf-8 -*-
import pytest

from marshmallow.exceptions import ValidationError, MarshallingError, UnmarshallingError
from marshmallow import fields, Schema


class TestValidationError:

    def test_stores_message_in_list(self):
        err = ValidationError('foo')
        assert err.messages == ['foo']

    def test_can_pass_list_of_messages(self):
        err = ValidationError(['foo', 'bar'])
        assert err.messages == ['foo', 'bar']

    def test_stores_dictionaries(self):
        messages = {'user': {'email': ['email is invalid']}}
        err = ValidationError(messages)
        assert err.messages == messages

    def test_can_store_field_names(self):
        err = ValidationError('invalid email', field_names='email')
        assert err.field_names == ['email']
        err = ValidationError('invalid email', field_names=['email'])
        assert err.field_names == ['email']

    def test_str(self):
        err = ValidationError('invalid email')
        assert str(err) == 'invalid email'

        err2 = ValidationError('invalid email', 'email')
        assert str(err2) == 'invalid email'


class TestMarshallingError:

    def test_deprecated(self):
        pytest.deprecated_call(MarshallingError, 'foo')

    def test_can_store_field_and_field_name(self):
        field_name = 'foo'
        field = fields.Str()
        err = MarshallingError('something went wrong', fields=[field],
                               field_names=[field_name])
        assert err.fields == [field]
        assert err.field_names == [field_name]

    def test_can_be_raised_by_custom_field(self):
        class MyField(fields.Field):
            def _serialize(self, val, attr, obj):
                raise MarshallingError('oops')

        class MySchema(Schema):
            foo = MyField()

        s = MySchema()
        result = s.dump({'foo': 42})
        assert 'foo' in result.errors
        assert result.errors['foo'] == ['oops']

class TestUnmarshallingError:

    def test_deprecated(self):
        pytest.deprecated_call(UnmarshallingError, 'foo')

    def test_can_store_field_and_field_name(self):
        field_name = 'foo'
        field = fields.Str()
        err = UnmarshallingError('something went wrong', fields=[field],
                                 field_names=[field_name])
        assert err.fields == [field]
        assert err.field_names == [field_name]

    def test_can_be_raised_by_validator(self):
        def validator(val):
            raise UnmarshallingError('oops')

        class MySchema(Schema):
            foo = fields.Field(validate=[validator])

        s = MySchema()
        result = s.load({'foo': 42})
        assert 'foo' in result.errors
        assert result.errors['foo'] == ['oops']
