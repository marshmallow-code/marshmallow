# -*- coding: utf-8 -*-
import pytest

from marshmallow import fields, Schema
from marshmallow.exceptions import ValidationError
from marshmallow.compat import OrderedDict

from tests.base import *  # noqa

class TestStrict:

    class StrictUserSchema(UserSchema):
        class Meta:
            strict = True

    def test_strict_meta_option(self):
        with pytest.raises(ValidationError):
            self.StrictUserSchema().load({'email': 'foo.com'})

    def test_strict_meta_option_is_inherited(self):
        class StrictUserSchema(UserSchema):
            class Meta:
                strict = True

        class ChildStrictSchema(self.StrictUserSchema):
            pass
        with pytest.raises(ValidationError):
            ChildStrictSchema().load({'email': 'foo.com'})


class TestSkipMissingOption:

    class UserSkipSchema(Schema):
        name = fields.Str()
        email = fields.Email()
        age = fields.Int(default=None)
        nicknames = fields.List(fields.String)

        class Meta:
            skip_missing = True

    def test_skip_missing_opt(self):
        schema = self.UserSkipSchema()
        assert schema.opts.skip_missing is True
        assert schema.skip_missing is True

    def test_missing_values_are_skipped(self):
        user = User(name='Joe', email=None, age=None)
        schema = self.UserSkipSchema()
        result = schema.dump(user)
        assert 'name' in result.data
        assert 'email' not in result.data
        assert 'age' not in result.data

    def test_missing_values_are_skipped_with_many(self):
        users = [User(name='Joe', email=None, age=None),
                 User(name='Jane', email=None, age=None)]
        schema = self.UserSkipSchema(many=True)
        results = schema.dump(users)
        for data in results.data:
            assert 'name' in data
            assert 'email' not in data
            assert 'age' not in data

    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/71
    def test_missing_string_values_can_be_skipped(self):
        user = dict(email='foo@bar.com', age=42)
        schema = self.UserSkipSchema()
        result = schema.dump(user)
        assert 'name' not in result.data
        assert 'email' in result.data
        assert 'age' in result.data

    def test_empty_list_can_be_skipped(self):
        schema = self.UserSkipSchema()
        user = dict(age=42, nicknames=['foo', 'bar'])
        result = schema.dump(user)
        assert 'nicknames' in result.data


class TestUnordered:

    class UnorderedSchema(Schema):
        name = fields.Str()
        email = fields.Str()

        class Meta:
            ordered = False

    def test_unordered_dump_returns_dict(self):
        schema = self.UnorderedSchema()
        u = User('steve', email='steve@steve.steve')
        result = schema.dump(u)
        assert not isinstance(result.data, OrderedDict)
        assert type(result.data) is dict

    def test_unordered_load_returns_dict(self):
        schema = self.UnorderedSchema()
        result = schema.load({'name': 'steve', 'email': 'steve@steve.steve'})
        assert not isinstance(result.data, OrderedDict)
        assert type(result.data) is dict


class KeepOrder(Schema):
    class Meta:
        ordered = True

    name = fields.String()
    email = fields.Email()
    age = fields.Integer()
    created = fields.DateTime()
    id = fields.Integer()
    homepage = fields.Url()
    birthdate = fields.DateTime()

class OrderedMetaSchema(Schema):
    class Meta:
        fields = ('name', 'email', 'age', 'created',
                    'id', 'homepage', 'birthdate')
        ordered = True

class OrderedNestedOnly(Schema):
    class Meta:
        ordered = True

    user = fields.Nested(KeepOrder)

class TestFieldOrdering:

    def test_ordered_option_is_inherited(self, user):
        class ChildOrderedSchema(KeepOrder):
            pass

        schema = ChildOrderedSchema()
        assert schema.opts.ordered is True
        assert schema.dict_class == OrderedDict

        data, _ = schema.dump(user)
        keys = list(data)
        assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage', 'birthdate']

    def test_ordering_is_off_by_default(self):
        class DummySchema(Schema):
            pass

        schema = DummySchema()
        assert schema.ordered is False

    def test_declared_field_order_is_maintained_on_dump(self, user):
        ser = KeepOrder()
        data, errs = ser.dump(user)
        keys = list(data)
        assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage', 'birthdate']

    def test_declared_field_order_is_maintained_on_load(self, serialized_user):
        schema = KeepOrder()
        data, errs = schema.load(serialized_user.data)
        keys = list(data)
        assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage', 'birthdate']

    def test_nested_field_order_with_only_arg_is_maintained_on_dump(self, user):
        schema = OrderedNestedOnly()
        data, errs = schema.dump({'user': user})
        user_data = data['user']
        keys = list(user_data)
        assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage', 'birthdate']

    def test_nested_field_order_with_only_arg_is_maintained_on_load(self):
        schema = OrderedNestedOnly()
        data, errs = schema.load({'user': {
            'name': 'Foo',
            'email': 'Foo@bar.com',
            'age': 42,
            'created': dt.datetime.now().isoformat(),
            'id': 123,
            'homepage': 'http://foo.com',
            'birthdate': dt.datetime.now().isoformat(),
        }})
        user_data = data['user']
        keys = list(user_data)
        assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage', 'birthdate']

    def test_nested_field_order_with_exlude_arg_is_maintained(self, user):
        class HasNestedExclude(Schema):
            class Meta:
                ordered = True

            user = fields.Nested(KeepOrder, exclude=('birthdate', ))

        ser = HasNestedExclude()
        data, errs = ser.dump({'user': user})
        user_data = data['user']
        keys = list(user_data)
        assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage']

    def test_meta_fields_order_is_maintained_on_dump(self, user):
        ser = OrderedMetaSchema()
        data, errs = ser.dump(user)
        keys = list(data)
        assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage', 'birthdate']

    def test_meta_fields_order_is_maintained_on_load(self, serialized_user):
        schema = OrderedMetaSchema()
        data, errs = schema.load(serialized_user.data)
        keys = list(data)
        assert keys == ['name', 'email', 'age', 'created', 'id', 'homepage', 'birthdate']

class TestIncludeOption:

    class AddFieldsSchema(Schema):
        name = fields.Str()

        class Meta:
            include = {
                'from': fields.Str()
            }

    def test_fields_are_added(self):
        s = self.AddFieldsSchema()
        in_data = {'name': 'Steve', 'from': 'Oskosh'}
        result = s.load({'name': 'Steve', 'from': 'Oskosh'})
        assert result.data == in_data

    def test_ordered_included(self):
        class AddFieldsOrdered(Schema):
            name = fields.Str()
            email = fields.Str()

            class Meta:
                include = OrderedDict([
                    ('from', fields.Str()),
                    ('in', fields.Str()),
                    ('@at', fields.Str())
                ])
                ordered = True

        s = AddFieldsOrdered()
        in_data = {'name': 'Steve', 'from': 'Oskosh', 'email': 'steve@steve.steve',
                    'in': 'VA', '@at': 'Charlottesville'}
        # declared fields, then "included" fields
        expected_fields = ['name', 'email', 'from', 'in', '@at']
        assert list(AddFieldsOrdered._declared_fields.keys()) == expected_fields

        result = s.load(in_data)
        assert list(result.data.keys()) == expected_fields

    def test_added_fields_are_inherited(self):

        class AddFieldsChild(self.AddFieldsSchema):
            email = fields.Str()

        s = AddFieldsChild()
        assert 'email' in s._declared_fields.keys()
        assert 'from' in s._declared_fields.keys()
        assert isinstance(s._declared_fields['from'], fields.Str)
