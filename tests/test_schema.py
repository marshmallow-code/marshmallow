#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
from collections import namedtuple

import pytest

from marshmallow import Schema, fields, utils, MarshalResult, UnmarshalResult
from marshmallow.exceptions import ValidationError
from marshmallow.compat import unicode, OrderedDict

from tests.base import *  # noqa


random.seed(1)

# Run tests with both verbose serializer and "meta" option serializer
@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_serializing_basic_object(SchemaClass, user):
    s = SchemaClass()
    data, errors = s.dump(user)
    assert data['name'] == user.name
    assert_almost_equal(data['age'], 42.3)
    assert data['registered']

def test_serializer_dump(user):
    s = UserSchema()
    result, errors = s.dump(user)
    assert result['name'] == user.name
    # Change strict mode
    s.strict = True
    bad_user = User(name='Monty', age='badage')
    with pytest.raises(ValidationError):
        s.dump(bad_user)

def test_dump_returns_dict_of_errors():
    s = UserSchema()
    bad_user = User(name='Monty', age='badage')
    result, errors = s.dump(bad_user)
    assert 'age' in errors


@pytest.mark.parametrize('SchemaClass',
[
    UserSchema, UserMetaSchema
])
def test_dump_with_strict_mode_raises_error(SchemaClass):
    s = SchemaClass(strict=True)
    bad_user = User(name='Monty', homepage='http://www.foo.bar', email='invalid-email')
    with pytest.raises(ValidationError) as excinfo:
        s.dump(bad_user)
    exc = excinfo.value
    assert type(exc.fields[0]) == fields.Email
    assert exc.field_names[0] == 'email'

    assert type(exc.messages) == dict
    assert exc.messages == {'email': ['Invalid email address.']}

def test_dump_resets_errors():
    class MySchema(Schema):
        email = fields.Email()

    schema = MySchema()
    result = schema.dump(User('Joe', email='notvalid'))
    assert len(result.errors['email']) == 1
    assert 'Invalid email address.' in result.errors['email'][0]
    result = schema.dump(User('Steve', email='__invalid'))
    assert len(result.errors['email']) == 1
    assert 'Invalid email address.' in result.errors['email'][0]

def test_load_resets_errors():
    class MySchema(Schema):
        email = fields.Email()

    schema = MySchema()
    result = schema.load({'name': 'Joe', 'email': 'notvalid'})
    assert len(result.errors['email']) == 1
    assert 'Invalid email address.' in result.errors['email'][0]
    result = schema.load({'name': 'Joe', 'email': '__invalid'})
    assert len(result.errors['email']) == 1
    assert 'Invalid email address.' in result.errors['email'][0]

def test_dump_resets_error_fields():
    class MySchema(Schema):
        email = fields.Email()

    schema = MySchema(strict=True)
    with pytest.raises(ValidationError) as excinfo:
        schema.dump(User('Joe', email='notvalid'))
    exc = excinfo.value
    assert len(exc.fields) == 1
    assert len(exc.field_names) == 1

    with pytest.raises(ValidationError) as excinfo:
        schema.dump(User('Joe', email='__invalid'))

    assert len(exc.fields) == 1
    assert len(exc.field_names) == 1

def test_load_resets_error_fields():
    class MySchema(Schema):
        email = fields.Email()

    schema = MySchema(strict=True)
    with pytest.raises(ValidationError) as excinfo:
        schema.load({'name': 'Joe', 'email': 'not-valid'})
    exc = excinfo.value
    assert len(exc.fields) == 1
    assert len(exc.field_names) == 1

    with pytest.raises(ValidationError) as excinfo:
        schema.load({'name': 'Joe', 'email': '__invalid'})

    assert len(exc.fields) == 1
    assert len(exc.field_names) == 1

def test_errored_fields_do_not_appear_in_output():

    class MyField(fields.Field):
        # Make sure validation fails during serialization
        def _serialize(self, val, attr, obj):
            raise ValidationError('oops')

    class MySchema(Schema):
        foo = MyField(validate=lambda x: False)

    sch = MySchema()
    data, errors = sch.load({'foo': 2})

    assert 'foo' in errors
    assert 'foo' not in data

    data, errors = sch.dump({'foo': 2})

    assert 'foo' in errors
    assert 'foo' not in data

def test_load_many_stores_error_indices():
    s = UserSchema()
    data = [
        {'name': 'Mick', 'email': 'mick@stones.com'},
        {'name': 'Keith', 'email': 'invalid-email', 'homepage': 'invalid-homepage'},
    ]
    _, errors = s.load(data, many=True)
    assert 0 not in errors
    assert 1 in errors
    assert 'email' in errors[1]
    assert 'homepage' in errors[1]

def test_dump_many():
    s = UserSchema()
    u1, u2 = User('Mick'), User('Keith')
    data, errors = s.dump([u1, u2], many=True)
    assert len(data) == 2
    assert data[0] == s.dump(u1).data


def test_multiple_errors_can_be_stored_for_a_given_index():
    class MySchema(Schema):
        foo = fields.Str(validate=lambda x: len(x) > 3)
        bar = fields.Int(validate=lambda x: x > 3)

    sch = MySchema()
    valid = {'foo': 'loll', 'bar': 42}
    invalid = {'foo': 'lol', 'bar': 3}
    errors = sch.validate([valid, invalid], many=True)

    assert 1 in errors
    assert len(errors[1]) == 2
    assert 'foo' in errors[1]
    assert 'bar' in errors[1]

def test_dump_many_stores_error_indices():
    s = UserSchema()
    u1, u2 = User('Mick', email='mick@stones.com'), User('Keith', email='invalid')

    _, errors = s.dump([u1, u2], many=True)
    assert 1 in errors
    assert len(errors[1]) == 1

    assert 'email' in errors[1]

def test_dump_many_doesnt_stores_error_indices_when_index_errors_is_false():
    class NoIndex(Schema):
        email = fields.Email()

        class Meta:
            index_errors = False

    s = NoIndex()
    u1, u2 = User('Mick', email='mick@stones.com'), User('Keith', email='invalid')

    _, errors = s.dump([u1, u2], many=True)
    assert 1 not in errors
    assert 'email' in errors

def test_dump_returns_a_marshalresult(user):
    s = UserSchema()
    result = s.dump(user)
    assert type(result) == MarshalResult
    data = result.data
    assert type(data) == dict
    errors = result.errors
    assert type(errors) == dict

def test_dumps_returns_a_marshalresult(user):
    s = UserSchema()
    result = s.dumps(user)
    assert type(result) == MarshalResult
    assert type(result.data) == str
    assert type(result.errors) == dict

def test_dumping_single_object_with_collection_schema():
    s = UserSchema(many=True)
    user = UserSchema('Mick')
    result = s.dump(user, many=False)
    assert type(result.data) == dict
    assert result.data == UserSchema().dump(user).data

def test_loading_single_object_with_collection_schema():
    s = UserSchema(many=True)
    in_data = {'name': 'Mick', 'email': 'mick@stones.com'}
    result = s.load(in_data, many=False)
    assert type(result.data) == User
    assert result.data.name == UserSchema().load(in_data).data.name

def test_dumps_many():
    s = UserSchema()
    u1, u2 = User('Mick'), User('Keith')
    json_result = s.dumps([u1, u2], many=True)
    data = json.loads(json_result.data)
    assert len(data) == 2
    assert data[0] == s.dump(u1).data


def test_load_returns_an_unmarshalresult():
    s = UserSchema()
    result = s.load({'name': 'Monty'})
    assert type(result) == UnmarshalResult
    assert type(result.data) == User
    assert type(result.errors) == dict

def test_load_many():
    s = UserSchema()
    in_data = [{'name': 'Mick'}, {'name': 'Keith'}]
    result = s.load(in_data, many=True)
    assert type(result.data) == list
    assert type(result.data[0]) == User
    assert result.data[0].name == 'Mick'

def test_loads_returns_an_unmarshalresult(user):
    s = UserSchema()
    result = s.loads(json.dumps({'name': 'Monty'}))
    assert type(result) == UnmarshalResult
    assert type(result.data) == User
    assert type(result.errors) == dict

def test_loads_many():
    s = UserSchema()
    in_data = [{'name': 'Mick'}, {'name': 'Keith'}]
    in_json_data = json.dumps(in_data)
    result = s.loads(in_json_data, many=True)
    assert type(result.data) == list
    assert result.data[0].name == 'Mick'

def test_loads_deserializes_from_json():
    user_dict = {'name': 'Monty', 'age': '42.3'}
    user_json = json.dumps(user_dict)
    result, errors = UserSchema().loads(user_json)
    assert isinstance(result, User)
    assert result.name == 'Monty'
    assert_almost_equal(result.age, 42.3)

def test_serializing_none():
    class MySchema(Schema):
        id = fields.Str(default='no-id')
        num = fields.Int()
        name = fields.Str()
    s = UserSchema().dump(None)
    assert s.data == {'id': 'no-id'}
    assert s.errors == {}

def test_default_many_symmetry():
    """The dump/load(s) methods should all default to the many value of the schema."""
    s_many = UserSchema(many=True, only=('name',))
    s_single = UserSchema(only=('name',))
    u1, u2 = User('King Arthur'), User('Sir Lancelot')
    s_single.load(s_single.dump(u1).data)
    s_single.loads(s_single.dumps(u1).data)
    s_many.load(s_many.dump([u1, u2]).data)
    s_many.loads(s_many.dumps([u1, u2]).data)


class TestValidate:

    def test_validate_returns_errors_dict(self):
        s = UserSchema()
        errors = s.validate({'email': 'bad-email', 'name': 'Valid Name'})
        assert type(errors) is dict
        assert 'email' in errors
        assert 'name' not in errors

        valid_data = {'name': 'Valid Name', 'email': 'valid@email.com'}
        errors = s.validate(valid_data)
        assert errors == {}

    def test_validate_many(self):
        s = UserSchema(many=True)
        in_data = [
            {'name': 'Valid Name', 'email': 'validemail@hotmail.com'},
            {'name': 'Valid Name2', 'email': 'invalid'}
        ]
        errors = s.validate(in_data, many=True)
        assert 1 in errors
        assert 'email' in errors[1]

    def test_validate_many_doesnt_store_index_if_index_errors_option_is_false(self):
        class NoIndex(Schema):
            email = fields.Email()

            class Meta:
                index_errors = False
        s = NoIndex()
        in_data = [
            {'name': 'Valid Name', 'email': 'validemail@hotmail.com'},
            {'name': 'Valid Name2', 'email': 'invalid'}
        ]
        errors = s.validate(in_data, many=True)
        assert 1 not in errors
        assert 'email' in errors

    def test_validate_strict(self):
        s = UserSchema(strict=True)
        with pytest.raises(ValidationError) as excinfo:
            s.validate({'email': 'bad-email'})
        exc = excinfo.value
        assert exc.messages == {'email': ['Invalid email address.']}
        assert type(exc.fields[0]) == fields.Email

    def test_validate_required(self):
        class MySchema(Schema):
            foo = fields.Field(required=True)

        s = MySchema()
        errors = s.validate({'bar': 42})
        assert 'foo' in errors
        assert 'required' in errors['foo'][0]

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_fields_are_not_copies(SchemaClass):
    s = SchemaClass(User('Monty', age=42))
    s2 = SchemaClass(User('Monty', age=43))
    assert s.fields is not s2.fields


def test_dumps_returns_json(user):
    ser = UserSchema()
    serialized, errors = ser.dump(user)
    json_data, errors = ser.dumps(user)
    assert type(json_data) == str
    expected = json.dumps(serialized)
    assert json_data == expected

def test_naive_datetime_field(user, serialized_user):
    expected = utils.isoformat(user.created)
    assert serialized_user.data['created'] == expected

def test_datetime_formatted_field(user, serialized_user):
    result = serialized_user.data['created_formatted']
    assert result == user.created.strftime("%Y-%m-%d")

def test_datetime_iso_field(user, serialized_user):
    assert serialized_user.data['created_iso'] == utils.isoformat(user.created)

def test_tz_datetime_field(user, serialized_user):
    # Datetime is corrected back to GMT
    expected = utils.isoformat(user.updated)
    assert serialized_user.data['updated'] == expected

def test_local_datetime_field(user, serialized_user):
    expected = utils.isoformat(user.updated, localtime=True)
    assert serialized_user.data['updated_local'] == expected

def test_class_variable(serialized_user):
    assert serialized_user.data['species'] == 'Homo sapiens'

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_serialize_many(SchemaClass):
    user1 = User(name="Mick", age=123)
    user2 = User(name="Keith", age=456)
    users = [user1, user2]
    serialized = SchemaClass(many=True).dump(users)
    assert len(serialized.data) == 2
    assert serialized.data[0]['name'] == "Mick"
    assert serialized.data[1]['name'] == "Keith"

def test_inheriting_schema(user):
    sch = ExtendedUserSchema()
    result = sch.dump(user)
    assert result.data['name'] == user.name
    user.is_old = True
    result = sch.dump(user)
    assert result.data['is_old'] is True

def test_custom_field(serialized_user, user):
    assert serialized_user.data['uppername'] == user.name.upper()

def test_url_field(serialized_user, user):
    assert serialized_user.data['homepage'] == user.homepage

def test_relative_url_field():
    u = {'name': 'John', 'homepage': '/foo'}
    result, errors = UserRelativeUrlSchema().load(u)
    assert 'homepage' not in errors

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_stores_invalid_url_error(SchemaClass):
    user = {'name': 'Steve', 'homepage': 'www.foo.com'}
    result = SchemaClass().load(user)
    assert "homepage" in result.errors
    expected = ['Invalid URL.']
    assert result.errors['homepage'] == expected

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_email_field(SchemaClass):
    u = User("John", email="john@example.com")
    s = SchemaClass().dump(u)
    assert s.data['email'] == "john@example.com"

def test_stored_invalid_email():
    u = {'name': 'John', 'email': 'johnexample.com'}
    s = UserSchema().load(u)
    assert "email" in s.errors
    assert s.errors['email'][0] == 'Invalid email address.'

def test_integer_field():
    u = User("John", age=42.3)
    serialized = UserIntSchema().dump(u)
    assert type(serialized.data['age']) == int
    assert serialized.data['age'] == 42

def test_fixed_field():
    u = User("John", age=42.3)
    serialized = UserFixedSchema().dump(u)
    assert serialized.data['age'] == "42.30"

def test_as_string():
    u = User("John", age=42.3)
    serialized = UserFloatStringSchema().dump(u)
    assert type(serialized.data['age']) == str
    assert_almost_equal(float(serialized.data['age']), 42.3)

def test_decimal_field():
    u = User("John", age=42.3)
    s = UserDecimalSchema().dump(u)
    assert type(s.data['age']) == unicode
    assert_almost_equal(float(s.data['age']), 42.3)

def test_price_field(serialized_user):
    assert serialized_user.data['balance'] == "100.00"

def test_extra():
    user = User("Joe", email="joe@foo.com")
    data, errors = UserSchema(extra={"fav_color": "blue"}).dump(user)
    assert data['fav_color'] == "blue"

def test_extra_many():
    users = [User('Fred'), User('Brian')]
    data, errs = UserSchema(many=True, extra={'band': 'Queen'}).dump(users)
    assert data[0]['band'] == 'Queen'

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_method_field(SchemaClass, serialized_user):
    assert serialized_user.data['is_old'] is False
    u = User("Joe", age=81)
    assert SchemaClass().dump(u).data['is_old'] is True

def test_function_field(serialized_user, user):
    assert serialized_user.data['lowername'] == user.name.lower()

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_prefix(SchemaClass, user):
    s = SchemaClass(prefix="usr_").dump(user)
    assert s.data['usr_name'] == user.name

def test_fields_must_be_declared_as_instances(user):
    class BadUserSchema(Schema):
        name = fields.String
    with pytest.raises(TypeError) as excinfo:
        BadUserSchema().dump(user)
    assert 'must be declared as a Field instance' in str(excinfo)

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_serializing_generator(SchemaClass):
    users = [User("Foo"), User("Bar")]
    user_gen = (u for u in users)
    s = SchemaClass(many=True).dump(user_gen)
    assert len(s.data) == 2
    assert s.data[0] == SchemaClass().dump(users[0]).data


def test_serializing_empty_list_returns_empty_list():
    assert UserSchema(many=True).dump([]).data == []
    assert UserMetaSchema(many=True).dump([]).data == []


def test_serializing_dict():
    user = {"name": "foo", "email": "foo@bar.com", "age": 'badage'}
    s = UserSchema().dump(user)
    assert s.data['name'] == "foo"
    assert 'age' in s.errors
    assert 'age' not in s.data


def test_serializing_dict_with_meta_fields():
    class MySchema(Schema):
        class Meta:
            fields = ('foo', 'bar')

    sch = MySchema()
    data, errors = sch.dump({'foo': 42, 'bar': 24, 'baz': 424})
    assert not errors
    assert data['foo'] == 42
    assert data['bar'] == 24
    assert 'baz' not in data

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_exclude_in_init(SchemaClass, user):
    s = SchemaClass(exclude=('age', 'homepage')).dump(user)
    assert 'homepage' not in s.data
    assert 'age' not in s.data
    assert 'name' in s.data

@pytest.mark.parametrize('SchemaClass',
    [UserSchema, UserMetaSchema])
def test_only_in_init(SchemaClass, user):
    s = SchemaClass(only=('name', 'age')).dump(user)
    assert 'homepage' not in s.data
    assert 'name' in s.data
    assert 'age' in s.data

def test_invalid_only_param(user):
    with pytest.raises(AttributeError):
        UserSchema(only=("_invalid", "name")).dump(user)

def test_can_serialize_uuid(serialized_user, user):
    assert serialized_user.data['uid'] == str(user.uid)

def test_can_serialize_time(user, serialized_user):
    expected = user.time_registered.isoformat()[:12]
    assert serialized_user.data['time_registered'] == expected

def test_invalid_time():
    u = User('Joe', time_registered='foo')
    s = UserSchema().dump(u)
    assert "'foo' cannot be formatted as a time." in s.errors['time_registered']

def test_invalid_date():
    u = User("Joe", birthdate='foo')
    s = UserSchema().dump(u)
    assert "'foo' cannot be formatted as a date." in s.errors['birthdate']

def test_invalid_email():
    u = User('Joe', email='bademail')
    s = UserSchema().dump(u)
    assert 'email' in s.errors
    assert 'Invalid email address.' in s.errors['email'][0]

def test_invalid_url():
    u = User('Joe', homepage='badurl')
    s = UserSchema().dump(u)
    assert 'homepage' in s.errors
    assert 'Invalid URL.' in s.errors['homepage'][0]

def test_invalid_selection():
    u = User('Jonhy')
    u.sex = 'hybrid'
    s = UserSchema().dump(u)
    assert "'hybrid' is not a valid choice for this field." in s.errors['sex']

def test_custom_json():
    class UserJSONSchema(Schema):
        name = fields.String()

        class Meta:
            json_module = mockjson

    user = User('Joe')
    s = UserJSONSchema()
    result, errors = s.dumps(user)
    assert result == mockjson.dumps('val')


def test_custom_error_message():
    class ErrorSchema(Schema):
        email = fields.Email(error="Invalid email")
        homepage = fields.Url(error="Bad homepage.")
        balance = fields.Fixed(error="Bad balance.")

    u = {'email': 'joe.net', 'homepage': 'joe@example.com', 'balance': 'blah'}
    s = ErrorSchema()
    data, errors = s.load(u)
    assert "Bad balance." in errors['balance']
    assert "Bad homepage." in errors['homepage']
    assert "Invalid email" in errors['email']


def test_load_errors_with_many():
    class ErrorSchema(Schema):
        email = fields.Email()

    data = [
        {'email': 'bademail'},
        {'email': 'goo@email.com'},
        {'email': 'anotherbademail'},
    ]

    data, errors = ErrorSchema(many=True).load(data)
    assert 0 in errors
    assert 2 in errors
    assert 'Invalid email address.' in errors[0]['email'][0]
    assert 'Invalid email address.' in errors[2]['email'][0]

def test_error_raised_if_fields_option_is_not_list():
    with pytest.raises(ValueError):
        class BadSchema(Schema):
            name = fields.String()

            class Meta:
                fields = 'name'


def test_error_raised_if_additional_option_is_not_list():
    with pytest.raises(ValueError):
        class BadSchema(Schema):
            name = fields.String()

            class Meta:
                additional = 'email'


def test_only_and_exclude():
    class MySchema(Schema):
        foo = fields.Field()
        bar = fields.Field()
        baz = fields.Field()
    sch = MySchema(only=('foo', 'bar'), exclude=('bar', ))
    data = dict(foo=42, bar=24, baz=242)
    result = sch.dump(data)
    assert 'foo' in result.data
    assert 'bar' not in result.data


def test_only_with_invalid_attribute():
    class MySchema(Schema):
        foo = fields.Field()

    sch = MySchema(only=('bar', ))
    with pytest.raises(KeyError) as excinfo:
        sch.dump(dict(foo=42))
    assert '"bar" is not a valid field' in str(excinfo.value.args[0])


def test_nested_only_and_exclude():
    class Inner(Schema):
        foo = fields.Field()
        bar = fields.Field()
        baz = fields.Field()

    class Outer(Schema):
        inner = fields.Nested(Inner, only=('foo', 'bar'), exclude=('bar', ))

    sch = Outer()
    data = dict(inner=dict(foo=42, bar=24, baz=242))
    result = sch.dump(data)
    assert 'foo' in result.data['inner']
    assert 'bar' not in result.data['inner']


def test_nested_with_sets():
    class Inner(Schema):
        foo = fields.Field()

    class Outer(Schema):
        inners = fields.Nested(Inner, many=True)

    sch = Outer()

    DataClass = namedtuple('DataClass', ['foo'])
    data = dict(inners=set([DataClass(42), DataClass(2)]))
    result = sch.dump(data)
    assert len(result.data['inners']) == 2


def test_meta_serializer_fields():
    u = User("John", age=42.3, email="john@example.com",
             homepage="http://john.com")
    s = UserMetaSchema().dump(u)
    assert s.data['name'] == u.name
    assert s.data['balance'] == "100.00"
    assert s.data['uppername'] == "JOHN"
    assert s.data['is_old'] is False
    assert s.data['created'] == utils.isoformat(u.created)
    assert s.data['updated_local'] == utils.isoformat(u.updated, localtime=True)
    assert s.data['finger_count'] == 10


def test_meta_fields_mapping(user):
    s = UserMetaSchema()
    s.dump(user)  # need to call dump to update fields
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
    class BadUserSchema(Schema):
        class Meta:
            fields = ('name', 'notfound')
    with pytest.raises(AttributeError):
        BadUserSchema().dump(user)

def test_exclude_fields(user):
    s = UserExcludeSchema().dump(user)
    assert "created" not in s.data
    assert "updated" not in s.data
    assert "name" in s.data

def test_fields_option_must_be_list_or_tuple(user):
    with pytest.raises(ValueError):
        class BadFields(Schema):
            class Meta:
                fields = "name"

def test_exclude_option_must_be_list_or_tuple(user):
    with pytest.raises(ValueError):
        class BadExclude(Schema):
            class Meta:
                exclude = "name"

def test_dateformat_option(user):
    fmt = '%Y-%m'

    class DateFormatSchema(Schema):
        updated = fields.DateTime("%m-%d")

        class Meta:
            fields = ('created', 'updated')
            dateformat = fmt
    serialized = DateFormatSchema().dump(user)
    assert serialized.data['created'] == user.created.strftime(fmt)
    assert serialized.data['updated'] == user.updated.strftime("%m-%d")

def test_default_dateformat(user):
    class DateFormatSchema(Schema):
        updated = fields.DateTime(format="%m-%d")

        class Meta:
            fields = ('created', 'updated')
    serialized = DateFormatSchema().dump(user)
    assert serialized.data['created'] == utils.isoformat(user.created)
    assert serialized.data['updated'] == user.updated.strftime("%m-%d")

def test_inherit_meta(user):
    class InheritedMetaSchema(UserMetaSchema):
        pass
    result = InheritedMetaSchema().dump(user).data
    expected = UserMetaSchema().dump(user).data
    assert result == expected

def test_inherit_meta_override():
    class Parent(Schema):
        class Meta:
            strict = True
            fields = ('name', 'email')

    class Child(Schema):
        class Meta(Parent.Meta):
            strict = False

    child = Child()
    assert child.opts.fields == ('name', 'email')
    assert child.opts.strict is False


def test_additional(user):
    s = UserAdditionalSchema().dump(user)
    assert s.data['lowername'] == user.name.lower()
    assert s.data['name'] == user.name

def test_cant_set_both_additional_and_fields(user):
    with pytest.raises(ValueError):
        class BadSchema(Schema):
            name = fields.String()

            class Meta:
                fields = ("name", 'email')
                additional = ('email', 'homepage')

def test_serializing_none_meta():
    s = UserMetaSchema().dump(None)
    assert s.data == {}
    assert s.errors == {}


class CustomError(Exception):
    pass

class MySchema(Schema):
    name = fields.String()
    email = fields.Email()
    age = fields.Integer()

class MySchema2(Schema):
    homepage = fields.URL()

class TestErrorHandler:

    def test_dump_with_custom_error_handler(self, user):
        @MySchema.error_handler
        def handle_errors(serializer, errors, obj):
            assert isinstance(serializer, MySchema)
            assert 'age' in errors
            assert isinstance(obj, User)
            raise CustomError('Something bad happened')

        user.age = 'notavalidage'
        with pytest.raises(CustomError):
            MySchema().dump(user)

    def test_load_with_custom_error_handler(self):
        @MySchema.error_handler
        def handle_errors(serializer, errors, data):
            assert isinstance(serializer, MySchema)
            assert 'email' in errors
            assert isinstance(data, dict)
            raise CustomError('Something bad happened')
        with pytest.raises(CustomError):
            MySchema().load({'email': 'invalid'})

    def test_validate_with_custom_error_handler(self):
        @MySchema.error_handler
        def handle_errors(schema, errors, data):
            raise CustomError('Something bad happened')

        with pytest.raises(CustomError):
            MySchema().validate({'email': 'invalid'})

    def test_multiple_serializers_with_same_error_handler(self, user):

        @MySchema.error_handler
        @MySchema2.error_handler
        def handle_errors(serializer, errors, obj):
            raise CustomError('Something bad happened')
        user.email = 'bademail'
        user.homepage = 'foo'

        user = {'email': 'bademail', 'homepage': 'foo'}
        with pytest.raises(CustomError):
            MySchema().load(user)
        with pytest.raises(CustomError):
            MySchema2().load(user)

    def test_setting_error_handler_class_attribute(self):
        def handle_errors(serializer, errors, obj):
            raise CustomError('Something bad happened')

        class ErrorSchema(Schema):
            email = fields.Email()
            __error_handler__ = handle_errors

        class ErrorSchemaSub(ErrorSchema):
            pass

        user = {'email': 'invalid'}

        ser = ErrorSchema()
        with pytest.raises(CustomError):
            ser.load(user)

        subser = ErrorSchemaSub()
        with pytest.raises(CustomError):
            subser.load(user)

class TestSchemaValidator:

    def test_validator_decorator_is_deprecated(self):

        def deprecated():
            class MySchema(Schema):
                pass

            @MySchema.validator
            def f(*args, **kwargs):
                pass

        pytest.deprecated_call(deprecated)

    def test_validator_defined_on_class(self):
        def validate_schema(instance, input_vals):
            assert isinstance(instance, Schema)
            return input_vals['field_b'] > input_vals['field_a']

        class ValidatingSchema(Schema):
            __validators__ = [validate_schema]
            field_a = fields.Field()
            field_b = fields.Field()

        schema = ValidatingSchema()
        _, errors = schema.load({'field_a': 2, 'field_b': 1})
        assert '_schema' in errors
        assert len(errors['_schema']) == 1

    def test_validator_that_raises_error_with_dict(self):
        def validate_schema(instance, input_vals):
            raise ValidationError({'code': 'Invalid schema'})

        class MySchema(Schema):
            __validators__ = [validate_schema]

        schema = MySchema()
        errors = schema.validate({})
        assert errors['_schema'] == [{'code': 'Invalid schema'}]

    def test_validator_that_raises_error_with_list(self):
        def validate_schema(instance, input_vals):
            raise ValidationError(['error1', 'error2'])

        class MySchema(Schema):
            __validators__ = [validate_schema]

        schema = MySchema()
        errors = schema.validate({})
        assert errors['_schema'] == ['error1', 'error2']

    def test_mixed_schema_validators(self):
        def validate_with_list(schema, in_vals):
            raise ValidationError(['err1'])

        def validate_with_dict(schema, in_vals):
            raise ValidationError({'code': 'err2'})

        def validate_with_str(schema, in_vals):
            raise ValidationError('err3')

        class MySchema(Schema):
            __validators__ = [
                validate_with_list,
                validate_with_dict,
                validate_with_str,
            ]

        schema = MySchema()
        errors = schema.validate({})
        assert errors['_schema'] == [
            'err1',
            {'code': 'err2'},
            'err3',
        ]

    def test_registered_validators_are_not_shared_with_ancestors(self):
        class ParentSchema(Schema):
            pass

        class ChildSchema(ParentSchema):
            pass

        @ParentSchema.validator
        def validate_parent(schema, in_data):
            raise ValidationError('Parent validator called')

        @ChildSchema.validator
        def validate_child(schema, in_data):
            assert False, 'Child validator should not be called'

        parent = ParentSchema()
        errors = parent.validate({})
        assert 'Parent validator called' in errors['_schema']

    def test_registered_validators_are_not_shared_with_children(self):
        class ParentSchema(Schema):
            pass

        class ChildSchema(ParentSchema):
            pass

        @ParentSchema.validator
        def validate_parent(schema, in_data):
            assert False, 'Parent validator should not be called'

        @ChildSchema.validator
        def validate_child(schema, in_data):
            raise ValidationError('Child validator called')

        child = ChildSchema()
        errors = child.validate({})
        assert 'Child validator called' in errors['_schema']

    def test_inheriting_then_registering_validator(self):
        def validate_parent(schema, data):
            raise ValidationError('Parent validator called')

        class ParentSchema(Schema):
            __validators__ = [validate_parent]
            pass

        class ChildSchema(ParentSchema):
            pass

        @ChildSchema.validator
        def validate_child(schema, data):
            raise ValidationError('Child validator called')

        child = ChildSchema()
        errors = child.validate({})
        assert len(errors['_schema']) == 2
        assert 'Parent validator called' in errors['_schema']
        assert 'Child validator called' in errors['_schema']

    def test_multiple_schema_errors_can_be_stored(self):
        def validate_with_bool(schema, in_vals):
            return False

        def validate_with_err(schema, inv_vals):
            raise ValidationError('Something went wrong.')

        class ValidatingSchema(Schema):
            __validators__ = [validate_with_err, validate_with_bool]
            field_a = fields.Field()
            field_b = fields.Field()

        schema = ValidatingSchema()
        _, errors = schema.load({'field_a': 2, 'field_b': 1})
        assert '_schema' in errors
        assert len(errors['_schema']) == 2
        assert errors['_schema'][0] == 'Something went wrong.'

    def test_schema_validation_error_with_stict_stores_correct_field_name(self):
        def validate_with_bool(schema, in_vals):
            raise ValidationError('oops')

        class ValidatingSchema(Schema):
            __validators__ = [validate_with_bool]
            field_a = fields.Field()

        schema = ValidatingSchema(strict=True)
        with pytest.raises(ValidationError) as excinfo:
            schema.load({'field_a': 1})
        exc = excinfo.value
        assert exc.fields == []
        assert exc.field_names == ['_schema']
        assert exc.messages == {'_schema': ['oops']}

    def test_schema_validation_error_with_strict_when_field_is_specified(self):
        def validate_with_err(schema, inv_vals):
            raise ValidationError('Something went wrong.', 'field_a')

        class ValidatingSchema(Schema):
            __validators__ = [validate_with_err]
            field_a = fields.Str()
            field_b = fields.Field()

        schema = ValidatingSchema(strict=True)
        with pytest.raises(ValidationError) as excinfo:
            schema.load({'field_a': 1})
        exc = excinfo.value
        assert type(exc.fields[0]) == fields.Str
        assert exc.field_names[0] == 'field_a'

    def test_schema_validation_error_stored_on_multiple_fields(self):
        def validate_with_err(schema, inv_vals):
            raise ValidationError('Something went wrong.', ['field_a', 'field_b'])

        class ValidatingSchema(Schema):
            __validators__ = [validate_with_err]
            field_a = fields.Str()
            field_b = fields.Field()

        schema = ValidatingSchema()
        result = schema.load({'field_a': 1})
        assert 'field_a' in result.errors
        assert 'field_b' in result.errors
        assert result.errors['field_a'] == ['Something went wrong.']
        assert result.errors['field_b'] == ['Something went wrong.']

        schema = ValidatingSchema(strict=True)
        with pytest.raises(ValidationError) as excinfo:
            schema.load({'field_a': 1})
        err = excinfo.value
        assert type(err.fields[0]) == fields.Str
        assert type(err.fields[1]) == fields.Field
        assert err.field_names == ['field_a', 'field_b']
        assert err.messages == {
            'field_a': ['Something went wrong.'],
            'field_b': ['Something went wrong.']
        }

    def test_validator_with_strict(self):
        def validate_schema(instance, input_vals):
            assert isinstance(instance, Schema)
            return input_vals['field_b'] > input_vals['field_a']

        class ValidatingSchema(Schema):
            __validators__ = [validate_schema]
            field_a = fields.Field()
            field_b = fields.Field()

        schema = ValidatingSchema(strict=True)
        in_data = {'field_a': 2, 'field_b': 1}
        with pytest.raises(ValidationError) as excinfo:
            schema.load(in_data)
        assert 'Schema validator' in str(excinfo)
        assert 'is False' in str(excinfo)

        # underlying exception is a ValidationError
        exc = excinfo.value
        assert isinstance(exc, ValidationError)

    def test_validator_defined_by_decorator(self):
        class ValidatingSchema(Schema):
            field_a = fields.Field()
            field_b = fields.Field()

        @ValidatingSchema.validator
        def validate_schema(instance, input_vals):
            assert isinstance(instance, Schema)
            return input_vals['field_b'] > input_vals['field_a']

        schema = ValidatingSchema()
        _, errors = schema.load({'field_a': 2, 'field_b': 1})
        assert '_schema' in errors

    def test_validators_are_inherited(self):
        def validate_schema(instance, input_vals):
            return input_vals['field_b'] > input_vals['field_a']

        class ValidatingSchema(Schema):
            __validators__ = [validate_schema]
            field_a = fields.Field()
            field_b = fields.Field()

        class ValidatingSchemaChild(ValidatingSchema):
            pass

        schema = ValidatingSchema()
        _, errors = schema.load({'field_a': 2, 'field_b': 1})
        assert '_schema' in errors

    def test_uncaught_validation_errors_are_stored(self):
        def validate_schema(schema, input_vals):
            raise ValidationError('Something went wrong')

        class MySchema(Schema):
            __validators__ = [validate_schema]

        schema = MySchema()
        _, errors = schema.load({'foo': 42})
        assert errors['_schema'] == ['Something went wrong']

    def test_validation_error_with_error_parameter(self):
        def validate_schema(schema, input_vals):
            raise ValidationError('Something went wrong')

        class MySchema(Schema):
            __validators__ = [validate_schema]
            foo = fields.String(error="This message isn't used")

        schema = MySchema()
        _, errors = schema.load({'foo': 42})
        assert errors['_schema'] == ['Something went wrong']

    def test_store_schema_validation_errors_on_specified_field(self):
        def validate_schema(schema, input_vals):
            raise ValidationError('Something went wrong with field bar', 'bar')

        class MySchema(Schema):
            __validators__ = [validate_schema]
            foo = fields.String()
            bar = fields.Field()

        schema = MySchema()
        _, errors = schema.load({'bar': 42, 'foo': 123})
        assert '_schema' not in errors
        assert 'Something went wrong with field bar' in errors['bar']

    def test_errors_are_cleared_on_load(self):
        class MySchema(Schema):
            foo = fields.Str(validate=lambda x: False)

        schema = MySchema()
        _, errors = schema.load({'foo': 'bar'})
        assert len(errors['foo']) == 1
        _, errors2 = schema.load({'foo': 'bar'})
        assert len(errors2['foo']) == 1

    def test_errors_are_cleared_after_loading_collection(self):
        class MySchema(Schema):
            foo = fields.Str(validate=lambda x: False)

        schema = MySchema()
        _, errors = schema.load([
            {'foo': 'bar'},
            {'foo': 'baz'}
        ], many=True)
        assert len(errors[0]['foo']) == 1
        assert len(errors[1]['foo']) == 1
        _, errors2 = schema.load({'foo': 'bar'})
        assert len(errors2['foo']) == 1

    def test_raises_error_with_list(self):
        def validator(val):
            raise ValidationError(['err1', 'err2'])

        class MySchema(Schema):
            foo = fields.Field(validate=validator)

        s = MySchema()
        errors = s.validate({'foo': 42})
        assert errors['foo'] == ['err1', 'err2']

    # https://github.com/marshmallow-code/marshmallow/issues/110
    def test_raises_error_with_dict(self):
        def validator(val):
            raise ValidationError({'code': 'invalid_foo'})

        class MySchema(Schema):
            foo = fields.Field(validate=validator)

        s = MySchema()
        errors = s.validate({'foo': 42})
        assert errors['foo'] == [{'code': 'invalid_foo'}]

    # https://github.com/marshmallow-code/marshmallow/issues/144
    def test_nested_schema_validators(self):

        class ThirdLevel(Schema):
            name = fields.String()

        class SecondLevel(Schema):
            third = fields.Nested(ThirdLevel)

        @SecondLevel.validator
        def validate_third(schema, in_data):
            raise ValidationError('from second level', 'third')

        class FirstLevel(Schema):
            second = fields.Nested(SecondLevel)

        @FirstLevel.validator
        def validate_second(schema, in_data):
            raise ValidationError('from first level', 'second')

        schema = FirstLevel()

        bad_data = {'second': {'third': {}}}
        _, errors = schema.load(bad_data)
        expected = {
            'second': {
                'third': ['from second level'],
                '_schema': ['from first level'],
            }
        }
        assert errors == expected


class TestPreprocessors:

    def test_preprocessor_decorator_is_deprecated(self):

        def deprecated():
            class MySchema(Schema):
                pass

            @MySchema.preprocessor
            def f(*args, **kwargs):
                pass

        pytest.deprecated_call(deprecated)

    def test_preprocessors_defined_on_class(self):
        def preprocess_data(schema, in_vals):
            assert isinstance(schema, Schema)
            in_vals['field_a'] += 1
            return in_vals

        class PreprocessingSchema(Schema):
            __preprocessors__ = [preprocess_data]
            field_a = fields.Integer()

        schema = PreprocessingSchema()
        result, errors = schema.load({'field_a': 10})
        assert result['field_a'] == 11

    def test_registered_preprocessors_are_not_shared_with_ancestors(self):
        class ParentSchema(Schema):
            foo = fields.Field()

        class ChildSchema(ParentSchema):
            pass

        @ParentSchema.preprocessor
        def parent_preprocessor(schema, data):
            data['sentinel'] = True
            return data

        @ChildSchema.preprocessor
        def child_preprocessor(schema, data):
            assert False, 'Child preprocessor should not be called'

        parent = ParentSchema()
        result = parent.load({})
        assert result.data['sentinel'] is True

    def test_registered_preprocessors_are_not_shared_with_children(self):
        class ParentSchema(Schema):
            pass

        class ChildSchema(ParentSchema):
            pass

        @ParentSchema.preprocessor
        def parent_preprocessor(schema, data):
            assert False, 'Parent preprocessor should not be called'

        @ChildSchema.preprocessor
        def child_preprocessor(schema, data):
            data['sentinel'] = True
            return data

        child = ChildSchema()
        result = child.load({})
        assert result.data['sentinel'] is True

    def test_preprocessors_defined_by_decorator(self):

        class PreprocessingSchema(Schema):
            field_a = fields.Integer()

        @PreprocessingSchema.preprocessor
        def preprocess_data(schema, in_vals):
            in_vals['field_a'] += 1
            return in_vals

        schema = PreprocessingSchema()
        result, errors = schema.load({'field_a': 10})
        assert result['field_a'] == 11


class TestDataHandler:

    def test_data_handler_is_deprecated(self):

        def deprecated():
            class MySchema(Schema):
                pass

            @MySchema.data_handler
            def f(*args, **kwargs):
                pass

        pytest.deprecated_call(deprecated)

    def test_schema_with_custom_data_handler(self, user):
        class CallbackSchema(Schema):
            name = fields.String()

        @CallbackSchema.data_handler
        def add_meaning(serializer, data, obj):
            data['meaning'] = 42
            return data

        ser = CallbackSchema()
        data, _ = ser.dump(user)
        assert data['meaning'] == 42

    def test_registered_data_handlers_are_not_shared_with_ancestors(self):
        class ParentSchema(Schema):
            foo = fields.Field()

        class ChildSchema(ParentSchema):
            pass

        @ParentSchema.data_handler
        def parent_handler(schema, data, obj):
            data['sentinel'] = True
            return data

        @ChildSchema.data_handler
        def child_handler(schema, data, obj):
            assert False, 'Child data handler should not be called'

        parent = ParentSchema()
        result = parent.dump({'foo': 42})
        assert result.data['sentinel'] is True

    def test_registered_data_handlers_are_not_shared_with_children(self):
        class ParentSchema(Schema):
            pass

        class ChildSchema(ParentSchema):
            pass

        @ParentSchema.data_handler
        def parent_handler(schema, data, obj):
            assert False, 'Parent data handler should not be called'

        @ChildSchema.data_handler
        def child_handler(schema, data, obj):
            data['sentinel'] = True
            return data

        child = ChildSchema()
        assert child.dump({}).data['sentinel'] is True

    def test_serializer_with_multiple_data_handlers(self, user):
        class CallbackSchema2(Schema):
            name = fields.String()

        @CallbackSchema2.data_handler
        def add_meaning(serializer, data, obj):
            data['meaning'] = 42
            return data

        @CallbackSchema2.data_handler
        def upper_name(serializer, data, obj):
            data['name'] = data['name'].upper()
            return data

        ser = CallbackSchema2()
        data, _ = ser.dump(user)
        assert data['meaning'] == 42
        assert data['name'] == user.name.upper()

    def test_setting_data_handlers_class_attribute(self, user):
        def add_meaning(serializer, data, obj):
            data['meaning'] = 42
            return data

        class CallbackSchema3(Schema):
            __data_handlers__ = [add_meaning]

            name = fields.String()

        ser = CallbackSchema3()
        data, _ = ser.dump(user)
        assert data['meaning'] == 42

    def test_root_data_handler(self, user):
        class RootSchema(Schema):
            NAME = 'user'

            name = fields.String()

        @RootSchema.data_handler
        def add_root(serializer, data, obj):
            return {
                serializer.NAME: data
            }

        s = RootSchema()
        data, _ = s.dump(user)
        assert data['user']['name'] == user.name

def test_schema_repr():
    class MySchema(Schema):
        name = fields.String()

    ser = MySchema(many=True, strict=True)
    rep = repr(ser)
    assert 'MySchema' in rep
    assert 'strict=True' in rep
    assert 'many=True' in rep


class TestNestedSchema:

    @pytest.fixture
    def user(self):
        return User(name="Monty", age=81)

    @pytest.fixture
    def blog(self, user):
        col1 = User(name="Mick", age=123)
        col2 = User(name="Keith", age=456)
        blog = Blog("Monty's blog", user=user, categories=["humor", "violence"],
                         collaborators=[col1, col2])
        return blog

    def test_flat_nested(self, blog):
        class FlatBlogSchema(Schema):
            name = fields.String()
            user = fields.Nested(UserSchema, only='name')
            collaborators = fields.Nested(UserSchema, only='name', many=True)
        s = FlatBlogSchema()
        data, _ = s.dump(blog)
        assert data['user'] == blog.user.name
        for i, name in enumerate(data['collaborators']):
            assert name == blog.collaborators[i].name

    # regression test for https://github.com/marshmallow-code/marshmallow/issues/64
    def test_nested_many_with_missing_attribute(self, user):
        class SimpleBlogSchema(Schema):
            title = fields.Str()
            wat = fields.Nested(UserSchema, many=True)
        blog = Blog('Simple blog', user=user, collaborators=None)
        schema = SimpleBlogSchema()
        result = schema.dump(blog)
        assert 'wat' not in result.data

    def test_nested_with_attribute_none(self):
        class InnerSchema(Schema):
            bar = fields.Field()

        class MySchema(Schema):
            foo = fields.Nested(InnerSchema)

        class MySchema2(Schema):
            foo = fields.Nested(InnerSchema)

        s = MySchema()
        result = s.dump({'foo': None})
        assert result.data['foo'] is None

        s2 = MySchema2()
        result2 = s2.dump({'foo': None})
        assert result2.data['foo'] is None

    def test_flat_nested2(self, blog):
        class FlatBlogSchema(Schema):
            name = fields.String()
            collaborators = fields.Nested(UserSchema, many=True, only='uid')

        s = FlatBlogSchema()
        data, _ = s.dump(blog)
        assert data['collaborators'][0] == str(blog.collaborators[0].uid)

    def test_nested_field_does_not_validate_required(self):
        class BlogRequiredSchema(Schema):
            user = fields.Nested(UserSchema, required=True)

        b = Blog('Authorless blog', user=None)
        _, errs = BlogRequiredSchema().dump(b)
        assert 'user' not in errs

    def test_nested_none(self):
        class BlogDefaultSchema(Schema):
            user = fields.Nested(UserSchema, default=0)

        b = Blog('Just the default blog', user=None)
        data, _ = BlogDefaultSchema().dump(b)
        assert data['user'] is None

    def test_nested(self, user, blog):
        blog_serializer = BlogSchema()
        serialized_blog, _ = blog_serializer.dump(blog)
        user_serializer = UserSchema()
        serialized_user, _ = user_serializer.dump(user)
        assert serialized_blog['user'] == serialized_user

    def test_nested_many_fields(self, blog):
        serialized_blog, _ = BlogSchema().dump(blog)
        expected = [UserSchema().dump(col)[0] for col in blog.collaborators]
        assert serialized_blog['collaborators'] == expected

    def test_nested_meta_many(self, blog):
        serialized_blog = BlogUserMetaSchema().dump(blog)[0]
        assert len(serialized_blog['collaborators']) == 2
        expected = [UserMetaSchema().dump(col)[0] for col in blog.collaborators]
        assert serialized_blog['collaborators'] == expected

    def test_nested_only(self, blog):
        col1 = User(name="Mick", age=123, id_="abc")
        col2 = User(name="Keith", age=456, id_="def")
        blog.collaborators = [col1, col2]
        serialized_blog = BlogOnlySchema().dump(blog)[0]
        assert serialized_blog['collaborators'] == [{"id": col1.id}, {"id": col2.id}]

    def test_exclude(self, blog):
        serialized = BlogSchemaExclude().dump(blog)[0]
        assert "uppername" not in serialized['user'].keys()

    def test_list_field(self, blog):
        serialized = BlogSchema().dump(blog)[0]
        assert serialized['categories'] == ["humor", "violence"]

    def test_list_field_parent(self):
        schema = BlogSchema()
        assert schema.fields['categories'].parent == schema
        assert schema.fields['categories'].name == 'categories'
        assert type(schema.fields['categories'].container.parent) is BlogSchema
        assert schema.fields['categories'].container.name == 'categories'

    def test_nested_load_many(self):
        in_data = {'title': 'Shine A Light', 'collaborators': [
            {'name': 'Mick', 'email': 'mick@stones.com'},
            {'name': 'Keith', 'email': 'keith@stones.com'}
        ]}
        data, errors = BlogSchema().load(in_data)
        collabs = data['collaborators']
        assert len(collabs) == 2
        assert all(type(each) == User for each in collabs)
        assert collabs[0].name == in_data['collaborators'][0]['name']

    def test_nested_errors(self):
        _, errors = BlogSchema().load(
            {'title': "Monty's blog", 'user': {'name': 'Monty', 'email': 'foo'}}
        )
        assert "email" in errors['user']
        assert len(errors['user']['email']) == 1
        assert "Invalid email address." in errors['user']['email'][0]
        # No problems with collaborators
        assert "collaborators" not in errors

    def test_nested_strict(self):
        with pytest.raises(ValidationError) as excinfo:
            _, errors = BlogSchema(strict=True).load(
                {'title': "Monty's blog", 'user': {'name': 'Monty', 'email': 'foo'}}
            )
        assert 'email' in str(excinfo)

    def test_nested_method_field(self, blog):
        data = BlogSchema().dump(blog)[0]
        assert data['user']['is_old']
        assert data['collaborators'][0]['is_old']

    def test_nested_function_field(self, blog, user):
        data = BlogSchema().dump(blog)[0]
        assert data['user']['lowername'] == user.name.lower()
        expected = blog.collaborators[0].name.lower()
        assert data['collaborators'][0]['lowername'] == expected

    def test_nested_prefixed_field(self, blog, user):
        data = BlogSchemaPrefixedUser().dump(blog)[0]
        assert data['user']['usr_name'] == user.name
        assert data['user']['usr_lowername'] == user.name.lower()

    def test_nested_prefixed_many_field(self, blog):
        data = BlogSchemaPrefixedUser().dump(blog)[0]
        assert data['collaborators'][0]['usr_name'] == blog.collaborators[0].name

    def test_invalid_float_field(self):
        user = User("Joe", age="1b2")
        _, errors = UserSchema().dump(user)
        assert "age" in errors

    def test_serializer_meta_with_nested_fields(self, blog, user):
        data = BlogSchemaMeta().dump(blog)[0]
        assert data['title'] == blog.title
        assert data['user'] == UserSchema().dump(user).data
        assert data['collaborators'] == [UserSchema().dump(c).data
                                               for c in blog.collaborators]
        assert data['categories'] == blog.categories

    def test_serializer_with_nested_meta_fields(self, blog):
        # Schema has user = fields.Nested(UserMetaSerializer)
        s = BlogUserMetaSchema().dump(blog)
        assert s.data['user'] == UserMetaSchema().dump(blog.user).data

    def test_nested_fields_must_be_passed_a_serializer(self, blog):
        class BadNestedFieldSchema(BlogSchema):
            user = fields.Nested(fields.String)
        with pytest.raises(ValueError):
            BadNestedFieldSchema().dump(blog)

    # regression test for https://github.com/marshmallow-code/marshmallow/issues/188
    def test_invalid_type_passed_to_nested_field(self):
        class InnerSchema(Schema):
            foo = fields.Field()

        class MySchema(Schema):
            inner = fields.Nested(InnerSchema, many=True)

        sch = MySchema()

        result = sch.load({'inner': [{'foo': 42}]})
        assert not result.errors

        result = sch.load({'inner': 'invalid'})
        assert 'inner' in result.errors
        assert result.errors['inner'] == ['Expected a collection of dicts, got a str.']

        class OuterSchema(Schema):
            inner = fields.Nested(InnerSchema)

        schema = OuterSchema()
        _, errors = schema.load({'inner': 1})
        assert errors['inner']['_schema'] == ['Data must be a dict, got a int']

    def test_missing_required_nested_field(self):
        class Inner(Schema):
            inner_req = fields.Field(required='Oops')
            inner_not_req = fields.Field()
            inner_bad = fields.Integer(required='Int plz')

        class Middle(Schema):
            middle_req = fields.Nested(Inner, required=True)
            middle_req_2 = fields.Nested(Inner, required=True)
            middle_not_req = fields.Nested(Inner)
            middle_field = fields.Field(required='middlin')

        class Outer(Schema):
            outer_req = fields.Nested(Middle, required=True)
            outer_many_req = fields.Nested(Middle, required=True, many=True)
            outer_not_req = fields.Nested(Middle)
            outer_many_not_req = fields.Nested(Middle, many=True)

        outer = Outer()
        expected = {
            'outer_many_req': {0: {'middle_req': {'inner_bad': ['Int plz'],
                                                   'inner_req': ['Oops']},
                                    'middle_req_2': {'inner_bad': ['Int plz'],
                                                     'inner_req': ['Oops']}},
                                'middle_field': ['middlin']},
             'outer_req': {'middle_field': ['middlin'],
                           'middle_req': {'inner_bad': ['Int plz'],
                                          'inner_req': ['Oops']},
                           'middle_req_2': {'inner_bad': ['Int plz'],
                                            'inner_req': ['Oops']}}}
        data, errors = outer.load({})
        assert errors == expected

class TestSelfReference:

    @pytest.fixture
    def employer(self):
        return User(name="Joe", age=59)

    @pytest.fixture
    def user(self, employer):
        return User(name="Tom", employer=employer, age=28)

    def test_nesting_schema_within_itself(self, user, employer):
        class SelfSchema(Schema):
            name = fields.String()
            age = fields.Integer()
            employer = fields.Nested('self', exclude=('employer', ))

        data, errors = SelfSchema().dump(user)
        assert not errors
        assert data['name'] == user.name
        assert data['employer']['name'] == employer.name
        assert data['employer']['age'] == employer.age

    def test_nesting_schema_by_passing_class_name(self, user, employer):
        class SelfReferencingSchema(Schema):
            name = fields.Str()
            age = fields.Int()
            employer = fields.Nested('SelfReferencingSchema', exclude=('employer',))
        data, errors = SelfReferencingSchema().dump(user)
        assert not errors
        assert data['name'] == user.name
        assert data['employer']['name'] == employer.name
        assert data['employer']['age'] == employer.age

    def test_nesting_within_itself_meta(self, user, employer):
        class SelfSchema(Schema):
            employer = fields.Nested("self", exclude=('employer', ))

            class Meta:
                additional = ('name', 'age')

        data, errors = SelfSchema().dump(user)
        assert not errors
        assert data['name'] == user.name
        assert data['age'] == user.age
        assert data['employer']['name'] == employer.name
        assert data['employer']['age'] == employer.age

    def test_nested_self_with_only_param(self, user, employer):
        class SelfSchema(Schema):
            employer = fields.Nested('self', only=('name', ))

            class Meta:
                fields = ('name', 'employer')

        data = SelfSchema().dump(user)[0]
        assert data['name'] == user.name
        assert data['employer']['name'] == employer.name
        assert 'age' not in data['employer']

    def test_multiple_nested_self_fields(self, user):
        class MultipleSelfSchema(Schema):
            emp = fields.Nested('self', only='name', attribute='employer')
            rels = fields.Nested('self', only='name',
                                    many=True, attribute='relatives')

            class Meta:
                fields = ('name', 'emp', 'rels')

        schema = MultipleSelfSchema()
        user.relatives = [User(name="Bar", age=12), User(name='Baz', age=34)]
        data, errors = schema.dump(user)
        assert not errors
        assert len(data['rels']) == len(user.relatives)
        relative = data['rels'][0]
        assert relative == user.relatives[0].name

    def test_nested_many(self):
        class SelfManySchema(Schema):
            relatives = fields.Nested('self', many=True)

            class Meta:
                additional = ('name', 'age')

        person = User(name='Foo')
        person.relatives = [User(name="Bar", age=12), User(name='Baz', age=34)]
        data = SelfManySchema().dump(person)[0]
        assert data['name'] == person.name
        assert len(data['relatives']) == len(person.relatives)
        assert data['relatives'][0]['name'] == person.relatives[0].name
        assert data['relatives'][0]['age'] == person.relatives[0].age

class RequiredUserSchema(Schema):
    name = fields.Field(required=True)

def test_serialization_with_required_field():
    user = User(name=None)
    data, errors = RequiredUserSchema().dump(user)
    # Does not validate required
    assert 'name' not in errors

def test_deserialization_with_required_field():
    in_data = {}
    data, errors = RequiredUserSchema().load(in_data)
    assert 'name' in errors
    assert 'Missing data for required field.' in errors['name']
    # field value should also not be in output data
    assert 'name' not in data

def test_deserialization_with_required_field_and_custom_validator():
    class ValidatingSchema(Schema):
        color = fields.String(required=True,
                        validate=lambda x: x.lower() == 'red' or x.lower() == 'blue',
                        error="Color must be red or blue")

    data, errors = ValidatingSchema().load({'name': 'foo'})
    assert errors
    assert 'color' in errors
    assert "Missing data for required field." in errors['color']

    _, errors = ValidatingSchema().load({'color': 'green'})
    assert 'color' in errors
    assert "Color must be red or blue" in errors['color']


class UserContextSchema(Schema):
    is_owner = fields.Method('get_is_owner')
    is_collab = fields.Function(lambda user, ctx: user in ctx['blog'])

    def get_is_owner(self, user):
        return self.context['blog'].user.name == user.name


class TestContext:

    def test_context_method(self):
        owner = User('Joe')
        blog = Blog(title='Joe Blog', user=owner)
        context = {'blog': blog}
        serializer = UserContextSchema()
        serializer.context = context
        data = serializer.dump(owner)[0]
        assert data['is_owner'] is True
        nonowner = User('Fred')
        data = serializer.dump(nonowner)[0]
        assert data['is_owner'] is False

    def test_context_method_function(self):
        owner = User('Fred')
        blog = Blog('Killer Queen', user=owner)
        collab = User('Brian')
        blog.collaborators.append(collab)
        context = {'blog': blog}
        serializer = UserContextSchema()
        serializer.context = context
        data = serializer.dump(collab)[0]
        assert data['is_collab'] is True
        noncollab = User('Foo')
        data = serializer.dump(noncollab)[0]
        assert data['is_collab'] is False

    def test_function_field_raises_error_when_context_not_available(self):
        # only has a function field
        class UserFunctionContextSchema(Schema):
            is_collab = fields.Function(lambda user, ctx: user in ctx['blog'])

        owner = User('Joe')
        serializer = UserFunctionContextSchema(strict=True)
        # no context
        serializer.context = None
        with pytest.raises(ValidationError) as excinfo:
            serializer.dump(owner)
        msg = 'No context available for Function field {0!r}'.format('is_collab')
        assert msg in str(excinfo)

    def test_fields_context(self):
        class CSchema(Schema):
            name = fields.String()

        ser = CSchema()
        ser.context['foo'] = 42

        assert ser.fields['name'].context == {'foo': 42}

    def test_nested_fields_inherit_context(self):
        class InnerSchema(Schema):
            likes_bikes = fields.Function(lambda obj, ctx: 'bikes' in ctx['info'])

        class CSchema(Schema):
            inner = fields.Nested(InnerSchema)

        ser = CSchema(strict=True)
        ser.context['info'] = 'i like bikes'
        obj = {
            'inner': {}
        }
        result = ser.dump(obj)
        assert result.data['inner']['likes_bikes'] is True


def test_serializer_can_specify_nested_object_as_attribute(blog):
    class BlogUsernameSchema(Schema):
        author_name = fields.String(attribute='user.name')
    ser = BlogUsernameSchema()
    result = ser.dump(blog)
    assert result.data['author_name'] == blog.user.name


class TestFieldInheritance:

    def test_inherit_fields_from_schema_subclass(self):
        expected = OrderedDict([
            ('field_a', fields.Number()),
            ('field_b', fields.Number()),
        ])

        class SerializerA(Schema):
            field_a = expected['field_a']

        class SerializerB(SerializerA):
            field_b = expected['field_b']
        assert SerializerB._declared_fields == expected

    def test_inherit_fields_from_non_schema_subclass(self):
        expected = OrderedDict([
            ('field_a', fields.Number()),
            ('field_b', fields.Number()),
        ])

        class PlainBaseClass(object):
            field_a = expected['field_a']

        class SerializerB1(Schema, PlainBaseClass):
            field_b = expected['field_b']

        class SerializerB2(PlainBaseClass, Schema):
            field_b = expected['field_b']
        assert SerializerB1._declared_fields == expected
        assert SerializerB2._declared_fields == expected

    def test_inheritance_follows_mro(self):
        expected = OrderedDict([
            ('field_a', fields.String()),
            ('field_c', fields.String()),
            ('field_b', fields.String()),
            ('field_d', fields.String()),
        ])
        # Diamond inheritance graph
        # MRO: D -> B -> C -> A

        class SerializerA(Schema):
            field_a = expected['field_a']

        class SerializerB(SerializerA):
            field_b = expected['field_b']

        class SerializerC(SerializerA):
            field_c = expected['field_c']

        class SerializerD(SerializerB, SerializerC):
            field_d = expected['field_d']
        assert SerializerD._declared_fields == expected

def get_from_dict(schema, key, obj, default=None):
    return obj.get('_' + key, default)

class TestAccessor:

    def test_accessor_is_used(self):
        class UserDictSchema(Schema):
            __accessor__ = get_from_dict
            name = fields.Str()
            email = fields.Email()
        user_dict = {'_name': 'joe', '_email': 'joe@shmoe.com'}
        schema = UserDictSchema()
        result = schema.dump(user_dict)
        assert result.data['name'] == user_dict['_name']
        assert result.data['email'] == user_dict['_email']
        assert not result.errors
        # can't serialize User object
        user = User(name='joe', email='joe@shmoe.com')
        with pytest.raises(AttributeError):
            schema.dump(user)

    def test_accessor_with_many(self):
        class UserDictSchema(Schema):
            __accessor__ = get_from_dict
            name = fields.Str()
            email = fields.Email()

        user_dicts = [{'_name': 'joe', '_email': 'joe@shmoe.com'},
                      {'_name': 'jane', '_email': 'jane@shmane.com'}]
        schema = UserDictSchema(many=True)
        results = schema.dump(user_dicts)
        for result, user_dict in zip(results.data, user_dicts):
            assert result['name'] == user_dict['_name']
            assert result['email'] == user_dict['_email']
        assert not results.errors
        # can't serialize User object
        users = [User(name='joe', email='joe@shmoe.com'),
                 User(name='jane', email='jane@shmane.com')]
        with pytest.raises(AttributeError):
            schema.dump(users)

    def test_accessor_decorator(self):
        class UserDictSchema(Schema):
            name = fields.Str()
            email = fields.Email()

        @UserDictSchema.accessor
        def get_from_dict2(schema, key, obj, default=None):
            return obj.get('_' + key, default)
        user_dict = {'_name': 'joe', '_email': 'joe@shmoe.com'}
        schema = UserDictSchema()
        result = schema.dump(user_dict)
        assert result.data['name'] == user_dict['_name']
        assert result.data['email'] == user_dict['_email']
        assert not result.errors
        # can't serialize User object
        user = User(name='joe', email='joe@shmoe.com')
        with pytest.raises(AttributeError):
            schema.dump(user)

class TestRequiredFields:

    class StringSchema(Schema):
        required_field = fields.Str(required=True)
        allow_none_field = fields.Str(allow_none=True)
        allow_none_required_field = fields.Str(required=True, allow_none=True)

    @pytest.fixture()
    def string_schema(self):
        return self.StringSchema()

    @pytest.fixture()
    def data(self):
        return dict(
            required_field='foo',
            allow_none_field='bar',
            allow_none_required_field='one',
        )

    def test_required_string_field_missing(self, string_schema, data):
        del data['required_field']
        errors = string_schema.validate(data)
        assert errors['required_field'] == ['Missing data for required field.']

    def test_required_string_field_failure(self, string_schema, data):
        data['required_field'] = None
        errors = string_schema.validate(data)
        assert errors['required_field'] == ['Field may not be null.']

    def test_allow_none_param(self, string_schema, data):
        data['allow_none_field'] = None
        errors = string_schema.validate(data)
        assert 'allow_none_field' not in errors

        data['allow_none_required_field'] = None
        errors = string_schema.validate(data)
        assert 'allow_none_required_field' not in errors

        del data['allow_none_required_field']
        errors = string_schema.validate(data)
        assert 'allow_none_required_field' in errors

    def test_allow_none_custom_message(self, data):
        class MySchema(Schema):
            allow_none_field = fields.Field(allow_none='<custom>')

        schema = MySchema()
        errors = schema.validate({'allow_none_field': None})
        assert errors['allow_none_field'][0] == '<custom>'


class TestDefaults:

    class MySchema(Schema):
        int_no_default = fields.Int(allow_none=True)
        str_no_default = fields.Str(allow_none=True)
        list_no_default = fields.List(fields.Str, allow_none=True)
        nested_no_default = fields.Nested(UserSchema, many=True, allow_none=True)

        int_with_default = fields.Int(allow_none=True, default=42)
        str_with_default = fields.Str(allow_none=True, default='foo')

    @pytest.fixture()
    def schema(self):
        return self.MySchema()

    @pytest.fixture()
    def data(self):
        return dict(
            int_no_default=None,
            str_no_default=None,
            list_no_default=None,
            nested_no_default=None,
            int_with_default=None,
            str_with_default=None,
        )

    def test_missing_inputs_are_excluded_from_dump_output(self, schema, data):
        for key in ['int_no_default', 'str_no_default',
                    'list_no_default', 'nested_no_default']:
            d = data.copy()
            del d[key]
            result = schema.dump(d)
            # the missing key is not in the serialized result
            assert key not in result.data
            # the rest of the keys are in the result.data
            assert all(k in result.data for k in d.keys())

    def test_none_is_serialized_to_none(self, schema, data):
        assert schema.validate(data) == {}
        result = schema.dump(data)
        for key in data.keys():
            msg = 'result.data[{0!r}] should be None'.format(key)
            assert result.data[key] is None, msg

    def test_default_and_value_missing(self, schema, data):
        del data['int_with_default']
        del data['str_with_default']
        result = schema.dump(data)
        assert result.data['int_with_default'] == 42
        assert result.data['str_with_default'] == 'foo'

    def test_loading_none(self, schema, data):
        result = schema.load(data)
        assert not result.errors
        for key in data.keys():
            result.data[key] is None

    def test_missing_inputs_are_excluded_from_load_output(self, schema, data):
        for key in ['int_no_default', 'str_no_default',
                    'list_no_default', 'nested_no_default']:
            d = data.copy()
            del d[key]
            result = schema.load(d)
            # the missing key is not in the deserialized result
            assert key not in result.data
            # the rest of the keys are in the result.data
            assert all(k in result.data for k in d.keys())


class TestLoadOnly:

    class MySchema(Schema):
        class Meta:
            load_only = ('str_load_only',)
            dump_only = ('str_dump_only',)

        str_dump_only = fields.String()
        str_load_only = fields.String()
        str_regular = fields.String()

    @pytest.fixture()
    def schema(self):
        return self.MySchema()

    @pytest.fixture()
    def data(self):
        return dict(
            str_dump_only='Dump Only',
            str_load_only='Load Only',
            str_regular='Regular String')

    def test_load_only(self, schema, data):
        result = schema.dump(data)
        assert not result.errors
        assert 'str_load_only' not in result.data
        assert 'str_dump_only' in result.data
        assert 'str_regular' in result.data

    def test_dump_only(self, schema, data):
        result = schema.load(data)
        assert not result.errors
        assert 'str_dump_only' not in result.data
        assert 'str_load_only' in result.data
        assert 'str_regular' in result.data
