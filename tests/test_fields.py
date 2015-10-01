# -*- coding: utf-8 -*-
import pytest

from marshmallow import fields, Schema, ValidationError
from marshmallow.marshalling import missing

from tests.base import ALL_FIELDS, User

class TestFieldAliases:

    def test_int_is_integer(self):
        assert fields.Int is fields.Integer

    def test_str_is_string(self):
        assert fields.Str is fields.String

    def test_bool_is_boolean(self):
        assert fields.Bool is fields.Boolean

    def test_URL_is_Url(self):  # flake8: noqa
        assert fields.URL is fields.Url

class TestField:

    def test_repr(self):
        default = u'œ∑´'
        field = fields.Field(default=default, attribute=None)
        assert repr(field) == (u'<fields.Field(default={0!r}, attribute=None, '
                                'validate=None, required=False, '
                                'load_only=False, dump_only=False, '
                                'missing={missing}, allow_none=False, '
                                'error_messages={error_messages})>'
                                .format(default, missing=missing,
                                        error_messages=field.error_messages))
        int_field = fields.Integer(validate=lambda x: True)
        assert '<fields.Integer' in repr(int_field)

    def test_error_raised_if_uncallable_validator_passed(self):
        with pytest.raises(ValueError):
            fields.Field(validate='notcallable')

    def test_custom_field_receives_attr_and_obj(self, user):
        class MyField(fields.Field):
            def _deserialize(self, val, attr, data):
                assert attr == 'name'
                assert data['foo'] == 42
                return val

        class MySchema(Schema):
            name = MyField()

        result = MySchema().load({'name': 'Monty', 'foo': 42})
        assert result.data == {'name': 'Monty'}

    def test_custom_field_receives_load_from_if_set(self, user):
        class MyField(fields.Field):
            def _deserialize(self, val, attr, data):
                assert attr == 'name'
                assert data['foo'] == 42
                return val

        class MySchema(Schema):
            Name = MyField(load_from='name')

        result = MySchema().load({'name': 'Monty', 'foo': 42})
        assert result.data == {'Name': 'Monty'}


class TestParentAndName:
    class MySchema(Schema):
        foo = fields.Field()
        bar = fields.List(fields.Str())

    @pytest.fixture()
    def schema(self):
        return self.MySchema()

    def test_simple_field_parent_and_name(self, schema):
        assert schema.fields['foo'].parent == schema
        assert schema.fields['foo'].name == 'foo'
        assert schema.fields['bar'].parent == schema
        assert schema.fields['bar'].name == 'bar'

    def test_list_field_inner_parent_and_name(self, schema):
        assert schema.fields['bar'].container.parent == schema.fields['bar']
        assert schema.fields['bar'].container.name == 'bar'

    def test_simple_field_root(self, schema):
        assert schema.fields['foo'].root == schema
        assert schema.fields['bar'].root == schema

    def test_list_field_inner_root(self, schema):
        assert schema.fields['bar'].container.root == schema


class TestMetadata:

    FIELDS_TO_TEST = [
        field for field in ALL_FIELDS
        if field not in [fields.FormattedString]
    ]

    @pytest.mark.parametrize('FieldClass', FIELDS_TO_TEST)
    def test_extra_metadata_may_be_added_to_field(self, FieldClass):  # noqa
        field = FieldClass(description='Just a normal field.')
        assert field.metadata['description'] == 'Just a normal field.'
        field = FieldClass(required=True, default=None, validate=lambda v: True,
                            description='foo', widget='select')
        assert field.metadata == {'description': 'foo', 'widget': 'select'}

    def test_metadata_may_be_added_to_formatted_string_field(self):
        field = fields.FormattedString('hello {name}', description='a greeting')
        assert field.metadata == {'description': 'a greeting'}


class TestErrorMessages:

    class MyField(fields.Field):
        default_error_messages = {
            'custom': 'Custom error message.'
        }

    def test_default_error_messages_get_merged_with_parent_error_messages(self):
        field = self.MyField()
        assert field.error_messages['custom'] == 'Custom error message'
        assert 'required' in field.error_messages

    def test_default_error_messages_get_merged_with_parent_error_messages(self):
        field = self.MyField(error_messages={'passed': 'Passed error message'})
        assert field.error_messages['passed'] == 'Passed error message'

    def test_fail(self):
        field = self.MyField()

        with pytest.raises(ValidationError) as excinfo:
            field.fail('required')
        assert excinfo.value.args[0] == 'Missing data for required field.'

        with pytest.raises(ValidationError) as excinfo:
            field.fail('null')
        assert excinfo.value.args[0] == 'Field may not be null.'

        with pytest.raises(ValidationError) as excinfo:
            field.fail('custom')
        assert excinfo.value.args[0] == 'Custom error message.'

        with pytest.raises(ValidationError) as excinfo:
            field.fail('validator_failed')
        assert excinfo.value.args[0] == 'Invalid value.'

        with pytest.raises(AssertionError) as excinfo:
            field.fail('doesntexist')

        assert 'doesntexist' in excinfo.value.args[0]
        assert 'MyField' in excinfo.value.args[0]
