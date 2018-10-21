# -*- coding: utf-8 -*-

from collections import namedtuple

import pytest

from marshmallow import fields, EXCLUDE, INCLUDE
from marshmallow.marshalling import Marshaller, Unmarshaller, missing, merge_errors
from marshmallow.exceptions import ValidationError

from tests.base import User

def test_missing_is_falsy():
    assert bool(missing) is False

class TestMarshaller:

    @pytest.fixture()
    def marshal(self):
        return Marshaller()

    def test_marshalling_generator(self, marshal):
        gen = (u for u in [User('Foo'), User('Bar')])
        res = marshal(gen, {'name': fields.String()}, many=True)
        assert len(res) == 2

    def test_default_to_missing(self, marshal):
        u = {'name': 'Foo'}
        res = marshal(
            u, {
                'name': fields.String(),
                'email': fields.Email(default=missing),
            },
        )
        assert res['name'] == u['name']
        assert 'email' not in res

    def test_serialize_fields_with_load_only_param(self, marshal):
        u = User('Foo', email='foo@bar.com')
        fields_dict = {
            'name': fields.String(),
            'email': fields.Email(load_only=True),
        }
        result = marshal(u, fields_dict)
        assert result['name'] == 'Foo'
        assert 'email' not in result

    # Regression test for https://github.com/marshmallow-code/marshmallow/issues/538
    def test_missing_data_are_skipped(self, marshal):
        assert marshal({}, {'foo': fields.Field()}) == {}
        assert marshal({}, {'foo': fields.Str()}) == {}
        assert marshal({}, {'foo': fields.Int()}) == {}
        assert marshal({}, {'foo': fields.Int(as_string=True)}) == {}
        assert marshal({}, {'foo': fields.Decimal(as_string=True)}) == {}

    def test_serialize_with_load_only_doesnt_validate(self, marshal):
        fields_dict = {
            'email': fields.Email(load_only=True),
        }
        marshal({'email': 'invalid'}, fields_dict)
        assert 'email' not in marshal.errors

    def test_serialize_fields_with_data_key_param(self, marshal):
        data = {
            'name': 'Mike',
            'email': 'm@wazow.ski',
        }
        fields_dict = {
            'name': fields.String(data_key='NaMe'),
            'email': fields.Email(attribute='email', data_key='EmAiL'),
        }
        result = marshal.serialize(data, fields_dict)
        assert result['NaMe'] == 'Mike'
        assert result['EmAiL'] == 'm@wazow.ski'

    def test_stores_indices_of_errors_when_many_equals_true(self, marshal):
        users = [
            {'age': 42},
            {'age': 'dummy'},
            {'age': '__dummy'},
        ]
        try:
            marshal(users, {'age': fields.Int()}, many=True, index_errors=True)
        except ValidationError:
            pass
        # 2nd and 3rd elements have an error
        assert 1 in marshal.errors
        assert 2 in marshal.errors
        assert 'age' in marshal.errors[1]
        assert 'age' in marshal.errors[2]

    def test_doesnt_store_errors_when_index_errors_equals_false(self, marshal):
        users = [
            {'age': 42},
            {'age': 'dummy'},
            {'age': '__dummy'},
        ]
        try:
            marshal(users, {'age': fields.Int()}, many=True, index_errors=False)
        except ValidationError:
            pass
        assert 1 not in marshal.errors
        assert 'age' in marshal.errors

class TestUnmarshaller:

    @pytest.fixture
    def unmarshal(self):
        return Unmarshaller()

    def test_extra_data_unknown_exclude(self, unmarshal):
        fields_ = {'name': fields.Str()}
        ret = unmarshal({'extra': 42, 'name': 'Steve'}, fields_, unknown=EXCLUDE)
        assert 'extra' not in ret

    def test_extra_data_unknown_include(self, unmarshal):
        fields_ = {'name': fields.Str()}
        ret = unmarshal({'extra': 42, 'name': 'Steve'}, fields_, unknown=INCLUDE)
        assert ret['extra'] == 42

    def test_stores_errors(self, unmarshal):
        data = {'email': 'invalid-email'}
        try:
            unmarshal(data, {'email': fields.Email()})
        except ValidationError:
            pass
        assert 'email' in unmarshal.errors

    def test_stores_indices_of_errors_when_many_equals_true(self, unmarshal):
        users = [
            {'email': 'bar@example.com'},
            {'email': 'foobar'},
            {'email': 'invalid'},
        ]
        try:
            unmarshal(users, {'email': fields.Email()}, many=True)
        except ValidationError:
            pass
        # 2nd and 3rd elements have an error
        assert 1 in unmarshal.errors
        assert 2 in unmarshal.errors
        assert 'email' in unmarshal.errors[1]
        assert 'email' in unmarshal.errors[2]

    def test_doesnt_store_errors_when_index_errors_equals_false(self, unmarshal):
        users = [
            {'email': 'bar@example.com'},
            {'email': 'foobar'},
            {'email': 'invalid'},
        ]
        try:
            unmarshal(users, {'email': fields.Email()}, many=True, index_errors=False)
        except ValidationError:
            pass
        assert 1 not in unmarshal.errors
        assert 'email' in unmarshal.errors

    def test_deserialize(self, unmarshal):
        user_data = {
            'age': '12',
        }
        result = unmarshal.deserialize(user_data, {'age': fields.Integer()})
        assert result['age'] == 12

    def test_extra_fields(self, unmarshal):
        data = {'name': 'Mick'}
        fields_dict = {'name': fields.String(), 'age': fields.Integer()}
        # data doesn't have to have all the fields in the schema
        result = unmarshal(data, fields_dict)
        assert result['name'] == data['name']
        assert 'age' not in result

    def test_deserialize_many(self, unmarshal):
        users_data = [
            {'name': 'Mick', 'age': '71'},
            {'name': 'Keith', 'age': '70'},
        ]
        fields_dict = {
            'name': fields.String(),
            'age': fields.Integer(),
        }
        result = unmarshal.deserialize(users_data, fields_dict, many=True)
        assert isinstance(result, list)
        user = result[0]
        assert user['age'] == 71

    # def test_deserialize_strict_raises_error(self, unmarshal):
    #     with pytest.raises(ValidationError):
    #         unmarshal(
    #             {'email': 'invalid', 'name': 'Mick'},
    #             {'email': fields.Email(), 'name': fields.String()},
    #             strict=True
    #         )

    def test_deserialize_stores_errors(self, unmarshal):
        user_data = {
            'email': 'invalid',
            'age': 'nan',
            'name': 'Valid Name',
        }
        fields_dict = {
            'email': fields.Email(),
            'age': fields.Integer(),
            'name': fields.String(),
        }
        try:
            unmarshal(user_data, fields_dict)
        except ValidationError:
            pass
        errors = unmarshal.errors
        assert 'email' in errors
        assert 'age' in errors
        assert 'name' not in errors

    def test_deserialize_fields_with_attribute_param(self, unmarshal):
        data = {
            'username': 'mick@stones.com',
            'name': 'Mick',
        }
        fields_dict = {
            'username': fields.Email(attribute='email'),
            'name': fields.String(attribute='firstname'),
        }
        result = unmarshal.deserialize(data, fields_dict)
        assert result['email'] == 'mick@stones.com'
        assert result['firstname'] == 'Mick'

    def test_deserialize_fields_with_data_key_param(self, unmarshal):
        data = {
            'Name': 'Mick',
            'UserName': 'foo@bar.com',
            'years': '42',
        }
        fields_dict = {
            'name': fields.String(data_key='Name'),
            'username': fields.Email(attribute='email', data_key='UserName'),
            'years': fields.Integer(data_key='Years'),
        }
        result = unmarshal.deserialize(data, fields_dict, unknown=EXCLUDE)
        assert result['name'] == 'Mick'
        assert result['email'] == 'foo@bar.com'
        assert 'years' not in result

    def test_deserialize_fields_with_dump_only_param(self, unmarshal):
        data = {
            'name': 'Mick',
            'years': '42',
        }
        fields_dict = {
            'name': fields.String(),
            'years': fields.Integer(dump_only=True),
            'always_invalid': fields.Field(validate=lambda f: False, dump_only=True),
        }
        result = unmarshal.deserialize(data, fields_dict, unknown=EXCLUDE)
        assert result['name'] == 'Mick'
        assert 'years' not in result

        assert 'always_invalid' not in unmarshal.errors


CustomError = namedtuple('CustomError', ['code', 'message'])


class TestMergeErrors:
    def test_merging_none_and_string(self):
        assert 'error1' == merge_errors(None, 'error1')

    def test_merging_none_and_custom_error(self):
        assert CustomError(123, 'error1') == merge_errors(None, CustomError(123, 'error1'))

    def test_merging_none_and_list(self):
        assert ['error1', 'error2'] == merge_errors(None, ['error1', 'error2'])

    def test_merging_none_and_dict(self):
        assert {'field1': 'error1'} == merge_errors(None, {'field1': 'error1'})

    def test_merging_string_and_none(self):
        assert 'error1' == merge_errors('error1', None)

    def test_merging_custom_error_and_none(self):
        assert CustomError(123, 'error1') == merge_errors(CustomError(123, 'error1'), None)

    def test_merging_list_and_none(self):
        assert ['error1', 'error2'] == merge_errors(['error1', 'error2'], None)

    def test_merging_dict_and_none(self):
        assert {'field1': 'error1'} == merge_errors({'field1': 'error1'}, None)

    def test_merging_string_and_string(self):
        assert ['error1', 'error2'] == merge_errors('error1', 'error2')

    def test_merging_custom_error_and_string(self):
        assert [CustomError(123, 'error1'), 'error2'] == merge_errors(
            CustomError(123, 'error1'), 'error2',
        )

    def test_merging_string_and_custom_error(self):
        assert ['error1', CustomError(123, 'error2')] == merge_errors(
            'error1', CustomError(123, 'error2'),
        )

    def test_merging_custom_error_and_custom_error(self):
        assert [CustomError(123, 'error1'), CustomError(456, 'error2')] == merge_errors(
            CustomError(123, 'error1'),
            CustomError(456, 'error2'),
        )

    def test_merging_string_and_list(self):
        assert ['error1', 'error2'] == merge_errors('error1', ['error2'])

    def test_merging_string_and_dict(self):
        assert {'_schema': 'error1', 'field1': 'error2'} == merge_errors(
            'error1', {'field1': 'error2'},
        )

    def test_merging_string_and_dict_with_schema_error(self):
        assert {'_schema': ['error1', 'error2'], 'field1': 'error3'} == merge_errors(
            'error1', {'_schema': 'error2', 'field1': 'error3'},
        )

    def test_merging_custom_error_and_list(self):
        assert [CustomError(123, 'error1'), 'error2'] == merge_errors(
            CustomError(123, 'error1'), ['error2'],
        )

    def test_merging_custom_error_and_dict(self):
        assert {'_schema': CustomError(123, 'error1'), 'field1': 'error2'} == merge_errors(
            CustomError(123, 'error1'), {'field1': 'error2'},
        )

    def test_merging_custom_error_and_dict_with_schema_error(self):
        assert {
            '_schema': [CustomError(123, 'error1'), 'error2'],
            'field1': 'error3',
        } == merge_errors(
            CustomError(123, 'error1'), {'_schema': 'error2', 'field1': 'error3'},
        )

    def test_merging_list_and_string(self):
        assert ['error1', 'error2'] == merge_errors(['error1'], 'error2')

    def test_merging_list_and_custom_error(self):
        assert ['error1', CustomError(123, 'error2')] == merge_errors(
            ['error1'], CustomError(123, 'error2'),
        )

    def test_merging_list_and_list(self):
        assert ['error1', 'error2'] == merge_errors(['error1'], ['error2'])

    def test_merging_list_and_dict(self):
        assert {'_schema': ['error1'], 'field1': 'error2'} == merge_errors(
            ['error1'], {'field1': 'error2'},
        )

    def test_merging_list_and_dict_with_schema_error(self):
        assert {'_schema': ['error1', 'error2'], 'field1': 'error3'} == merge_errors(
            ['error1'], {'_schema': 'error2', 'field1': 'error3'},
        )

    def test_merging_dict_and_string(self):
        assert {'_schema': 'error2', 'field1': 'error1'} == merge_errors(
            {'field1': 'error1'}, 'error2',
        )

    def test_merging_dict_and_custom_error(self):
        assert {'_schema': CustomError(123, 'error2'), 'field1': 'error1'} == merge_errors(
            {'field1': 'error1'}, CustomError(123, 'error2'),
        )

    def test_merging_dict_and_list(self):
        assert {'_schema': ['error2'], 'field1': 'error1'} == merge_errors(
            {'field1': 'error1'}, ['error2'],
        )

    def test_merging_dict_and_dict(self):
        assert {
            'field1': 'error1',
            'field2': ['error2', 'error3'],
            'field3': 'error4',
        } == merge_errors(
            {'field1': 'error1', 'field2': 'error2'},
            {'field2': 'error3', 'field3': 'error4'},
        )

    def test_deep_merging_dicts(self):
        assert {'field1': {'field2': ['error1', 'error2']}} == merge_errors(
            {'field1': {'field2': 'error1'}},
            {'field1': {'field2': 'error2'}},
        )
