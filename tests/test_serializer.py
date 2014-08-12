#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import pytest

from marshmallow import Serializer, fields, utils
from marshmallow.exceptions import MarshallingError
from marshmallow.compat import unicode, binary_type

from tests.base import *  # noqa

# Run tests with both verbose serializer and "meta" option serializer
@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_serializing_basic_object(SerializerClass, user):
    s = SerializerClass(user)
    assert s.data['name'] == user.name
    assert_almost_equal(s.data['age'], 42.3)
    assert s.data['registered']

def test_serializer_dump(user):
    s = UserSerializer()
    result, errors = s.dump(user)
    assert result['name'] == user.name
    # Change strict mode
    s.strict = True
    bad_user = User(name='Monty', email='invalid')
    with pytest.raises(MarshallingError):
        s.dump(bad_user)

def test_dump_returns_dict_of_errors():
    s = UserSerializer()
    bad_user = User(name='Monty', email='invalidemail', homepage='badurl')
    result, errors = s.dump(bad_user)
    assert 'email' in errors
    assert 'homepage' in errors

def test_serializing_none():
    s = UserSerializer(None)
    assert s.data['name'] == ''
    assert s.data['age'] == 0

def test_factory(user):
    serialize_user = UserSerializer.factory()

    data, errors = serialize_user(user)
    assert data['name'] == user.name
    assert data['age'] == user.age

def test_factory_saves_args(user):
    serialize_user = UserSerializer.factory(strict=True)
    user.homepage = 'invalid-url'
    with pytest.raises(MarshallingError):
        serialize_user(user)

def test_factory_doc_is_same_as_dump_doc():
    serialize_user = UserSerializer.factory(strict=True)
    assert serialize_user.__doc__ == UserSerializer.dump.__doc__


@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_fields_are_not_copies(SerializerClass):
    s = SerializerClass(User('Monty', age=42))
    s2 = SerializerClass(User('Monty', age=43))
    assert s.fields is not s2.fields


def test_dumps_returns_json(user):
    ser = UserSerializer()
    serialized, errors = ser.dump(user)
    json_data, errors = ser.dumps(user)
    expected = binary_type(json.dumps(serialized).encode("utf-8"))
    assert json_data == expected


def test_dumps_returns_bytestring(user):
    s = UserSerializer()
    result, errors = s.dumps(user)
    assert isinstance(result, binary_type)


def test_naive_datetime_field(serialized_user):
    assert serialized_user.data['created'] == 'Sun, 10 Nov 2013 14:20:58 -0000'

def test_datetime_formatted_field(user, serialized_user):
    result = serialized_user.data['created_formatted']
    assert result == user.created.strftime("%Y-%m-%d")

def test_datetime_iso_field(user, serialized_user):
    assert serialized_user.data['created_iso'] == utils.isoformat(user.created)

def test_tz_datetime_field(serialized_user):
    # Datetime is corrected back to GMT
    assert serialized_user.data['updated'] == 'Sun, 10 Nov 2013 20:20:58 -0000'

def test_local_datetime_field(serialized_user):
    assert serialized_user.data['updated_local'] == 'Sun, 10 Nov 2013 14:20:58 -0600'

def test_class_variable(serialized_user):
    assert serialized_user.data['species'] == 'Homo sapiens'

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_serialize_many(SerializerClass):
    user1 = User(name="Mick", age=123)
    user2 = User(name="Keith", age=456)
    users = [user1, user2]
    serialized = SerializerClass(users, many=True)
    assert len(serialized.data) == 2
    assert serialized.data[0]['name'] == "Mick"
    assert serialized.data[1]['name'] == "Keith"

def test_no_implicit_list_handling(recwarn):
    users = [User(name='Mick'), User(name='Keith')]
    with pytest.raises(TypeError):
        UserSerializer(users)
    w = recwarn.pop()
    assert issubclass(w.category, DeprecationWarning)

def test_inheriting_serializer(user):
    serialized = ExtendedUserSerializer(user)
    assert serialized.data['name'] == user.name
    assert not serialized.data['is_old']

def test_custom_field(serialized_user, user):
    assert serialized_user.data['uppername'] == user.name.upper()

def test_url_field(serialized_user, user):
    assert serialized_user.data['homepage'] == user.homepage

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_url_field_validation(SerializerClass):
    invalid = User("John", age=42, homepage="/john")
    s = SerializerClass(invalid)
    assert s.is_valid(["homepage"]) is False

def test_relative_url_field():
    u = User("John", age=42, homepage="/john")
    serialized = UserRelativeUrlSerializer(u)
    assert serialized.is_valid()

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_stores_invalid_url_error(SerializerClass):
    user = User(name="John Doe", homepage="www.foo.com")
    serialized = SerializerClass(user)
    assert "homepage" in serialized.errors
    expected = '"www.foo.com" is not a valid URL. Did you mean: "http://www.foo.com"?'
    assert serialized.errors['homepage'] == expected

def test_default():
    user = User("John")  # No ID set
    serialized = UserSerializer(user)
    assert serialized.data['id'] == "no-id"

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_email_field(SerializerClass):
    u = User("John", email="john@example.com")
    s = SerializerClass(u)
    assert s.data['email'] == "john@example.com"

def test_stored_invalid_email():
    u = User("John", email="johnexample.com")
    s = UserSerializer(u)
    assert "email" in s.errors
    assert s.errors['email'] == '"johnexample.com" is not a valid email address.'

def test_integer_field():
    u = User("John", age=42.3)
    serialized = UserIntSerializer(u)
    assert type(serialized.data['age']) == int
    assert serialized.data['age'] == 42

def test_integer_default():
    user = User("John", age=None)
    serialized = UserIntSerializer(user)
    assert type(serialized.data['age']) == int
    assert serialized.data['age'] == 0

def test_fixed_field():
    u = User("John", age=42.3)
    serialized = UserFixedSerializer(u)
    assert serialized.data['age'] == "42.30"

def test_as_string():
    u = User("John", age=42.3)
    serialized = UserFloatStringSerializer(u)
    assert type(serialized.data['age']) == str
    assert_almost_equal(float(serialized.data['age']), 42.3)

def test_decimal_field():
    u = User("John", age=42.3)
    s = UserDecimalSerializer(u)
    assert type(s.data['age']) == unicode
    assert_almost_equal(float(s.data['age']), 42.3)

def test_price_field(serialized_user):
    assert serialized_user.data['balance'] == "100.00"

def test_validate():
    valid = User("Joe", email="joe@foo.com")
    invalid = User("John", email="johnexample.com")
    assert UserSerializer(valid).is_valid()
    assert UserSerializer(invalid).is_valid() is False

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_validate_field(SerializerClass):
    invalid = User("John", email="johnexample.com")
    assert SerializerClass(invalid).is_valid(["name"]) is True
    assert SerializerClass(invalid).is_valid(["email"]) is False

def test_validating_nonexistent_field_raises_error(serialized_user):
    with pytest.raises(KeyError):
        serialized_user.is_valid(["foobar"])

def test_fields_param_must_be_list_or_tuple():
    invalid = User("John", email="johnexample.com")
    with pytest.raises(ValueError):
        UserSerializer(invalid).is_valid("name")

def test_extra():
    user = User("Joe", email="joe@foo.com")
    s = UserSerializer(user, extra={"fav_color": "blue"})
    assert s.data['fav_color'] == "blue"

def test_extra_many():
    users = [User('Fred'), User('Brian')]
    s = UserSerializer(users, many=True, extra={'band': 'Queen'})
    data = s.data
    assert data[0]['band'] == 'Queen'

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_method_field(SerializerClass, serialized_user):
    assert serialized_user.data['is_old'] is False
    u = User("Joe", age=81)
    assert SerializerClass(u).data['is_old'] is True

def test_function_field(serialized_user, user):
    assert serialized_user.data['lowername'] == user.name.lower()

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_prefix(SerializerClass, user):
    s = SerializerClass(user, prefix="usr_")
    assert s.data['usr_name'] == user.name

def test_fields_must_be_declared_as_instances(user):
    class BadUserSerializer(Serializer):
        name = fields.String
    with pytest.raises(TypeError):
        BadUserSerializer(user)

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_serializing_generator(SerializerClass):
    users = [User("Foo"), User("Bar")]
    user_gen = (u for u in users)
    s = SerializerClass(user_gen, many=True)
    assert len(s.data) == 2
    assert s.data[0] == SerializerClass(users[0]).data


def test_serializing_empty_list_returns_empty_list():
    assert UserSerializer([], many=True).data == []
    assert UserMetaSerializer([], many=True).data == []


def test_serializing_dict(user):
    user = {"name": "foo", "email": "foo", "age": 42.3}
    s = UserSerializer(user)
    assert s.data['name'] == "foo"
    assert s.data['age'] == 42.3
    assert s.is_valid(['email']) is False

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_exclude_in_init(SerializerClass, user):
    s = SerializerClass(user, exclude=('age', 'homepage'))
    assert 'homepage' not in s.data
    assert 'age' not in s.data
    assert 'name' in s.data

@pytest.mark.parametrize('SerializerClass',
    [UserSerializer, UserMetaSerializer])
def test_only_in_init(SerializerClass, user):
    s = SerializerClass(user, only=('name', 'age'))
    assert 'homepage' not in s.data
    assert 'name' in s.data
    assert 'age' in s.data

def test_invalid_only_param(user):
    with pytest.raises(AttributeError):
        UserSerializer(user, only=("_invalid", "name"))

def test_strict_init():
    invalid = User("Foo", email="foo.com")
    with pytest.raises(MarshallingError):
        UserSerializer(invalid, strict=True)

def test_strict_meta_option():
    class StrictUserSerializer(UserSerializer):
        class Meta:
            strict = True
    invalid = User("Foo", email="foo.com")
    with pytest.raises(MarshallingError):
        StrictUserSerializer(invalid)

def test_can_serialize_uuid(serialized_user, user):
    assert serialized_user.data['uid'] == str(user.uid)

def test_can_serialize_time(user, serialized_user):
    expected = user.time_registered.isoformat()[:12]
    assert serialized_user.data['time_registered'] == expected

def test_invalid_time():
    u = User('Joe', time_registered='foo')
    s = UserSerializer(u)
    assert s.is_valid(['time_registered']) is False
    assert s.errors['time_registered'] == "'foo' cannot be formatted as a time."

def test_invalid_date():
    u = User("Joe", birthdate='foo')
    s = UserSerializer(u)
    assert s.is_valid(['birthdate']) is False
    assert s.errors['birthdate'] == "'foo' cannot be formatted as a date."

def test_invalid_selection():
    u = User('Jonhy')
    u.sex = 'hybrid'
    s = UserSerializer(u)
    assert s.is_valid(['sex']) is False
    assert s.errors['sex'] == "'hybrid' is not a valid choice for this field."

def test_custom_json():
    class UserJSONSerializer(Serializer):
        name = fields.String()

        class Meta:
            json_module = mockjson

    user = User('Joe')
    s = UserJSONSerializer(user)
    result, errors = s.dumps(user)
    assert result == mockjson.dumps('val')


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


def test_meta_serializer_fields():
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


def test_meta_fields_mapping(user):
    s = UserMetaSerializer(user)
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
    class BadUserSerializer(Serializer):
        class Meta:
            fields = ('name', 'notfound')
    with pytest.raises(AttributeError):
        BadUserSerializer(user)

def test_exclude_fields(user):
    s = UserExcludeSerializer(user)
    assert "created" not in s.data
    assert "updated" not in s.data
    assert "name" in s.data

def test_fields_option_must_be_list_or_tuple(user):
    class BadFields(Serializer):
        class Meta:
            fields = "name"
    with pytest.raises(ValueError):
        BadFields(user)

def test_exclude_option_must_be_list_or_tuple(user):
    class BadExclude(Serializer):
        class Meta:
            exclude = "name"
    with pytest.raises(ValueError):
        BadExclude(user)

def test_dateformat_option(user):
    fmt = '%Y-%m'

    class DateFormatSerializer(Serializer):
        updated = fields.DateTime("%m-%d")

        class Meta:
            fields = ('created', 'updated')
            dateformat = fmt
    serialized = DateFormatSerializer(user)
    assert serialized.data['created'] == user.created.strftime(fmt)
    assert serialized.data['updated'] == user.updated.strftime("%m-%d")

def test_default_dateformat(user):
    class DateFormatSerializer(Serializer):
        updated = fields.DateTime(format="%m-%d")

        class Meta:
            fields = ('created', 'updated')
    serialized = DateFormatSerializer(user)
    assert serialized.data['created'] == utils.rfcformat(user.created)
    assert serialized.data['updated'] == user.updated.strftime("%m-%d")

def test_inherit_meta(user):
    class InheritedMetaSerializer(UserMetaSerializer):
        pass
    result = InheritedMetaSerializer(user).data
    expected = UserMetaSerializer(user).data
    assert result == expected

def test_additional(user):
    s = UserAdditionalSerializer(user)
    assert s.data['lowername'] == user.name.lower()
    assert s.data['name'] == user.name

def test_cant_set_both_additional_and_fields(user):
    class BadSerializer(Serializer):
        name = fields.String()

        class Meta:
            fields = ("name", 'email')
            additional = ('email', 'homepage')
    with pytest.raises(ValueError):
        BadSerializer(user)

def test_serializing_none_meta():
    s = UserMetaSerializer(None)
    # Since meta fields are used, defaults to None
    assert s.data['name'] is None
    assert s.data['email'] is None


def test_serializer_with_custom_error_handler(user):

    class CustomError(Exception):
        pass

    class MySerializer(Serializer):
        name = fields.String()
        email = fields.Email()

    @MySerializer.error_handler
    def handle_errors(serializer, errors, obj):
        assert isinstance(serializer, MySerializer)
        assert 'email' in errors
        assert isinstance(obj, User)
        raise CustomError('Something bad happened')

    user.email = 'bademail'
    with pytest.raises(CustomError):
        MySerializer().dump(user)

    user.email = 'monty@python.org'
    assert MySerializer(user).data

def test_serializer_with_custom_data_handler(user):
    class CallbackSerializer(Serializer):
        name = fields.String()

    @CallbackSerializer.data_handler
    def add_meaning(serializer, data, obj):
        data['meaning'] = 42
        return data

    ser = CallbackSerializer()
    data, _ = ser.dump(user)
    assert data['meaning'] == 42

def test_serializer_with_multiple_data_handlers(user):
    class CallbackSerializer2(Serializer):
        name = fields.String()

    @CallbackSerializer2.data_handler
    def add_meaning(serializer, data, obj):
        data['meaning'] = 42
        return data

    @CallbackSerializer2.data_handler
    def upper_name(serializer, data, obj):
        data['name'] = data['name'].upper()
        return data

    ser = CallbackSerializer2()
    data, _ = ser.dump(user)
    assert data['meaning'] == 42
    assert data['name'] == user.name.upper()

def test_root_data_handler(user):
    class RootSerializer(Serializer):
        NAME = 'user'

        name = fields.String()

    @RootSerializer.data_handler
    def add_root(serializer, data, obj):
        return {
            serializer.NAME: data
        }

    s = RootSerializer()
    data, _ = s.dump(user)
    assert data['user']['name'] == user.name


class TestNestedSerializer:

    def setup_method(self, method):
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
        s = FlatBlogSerializer()
        data, _ = s.dump(self.blog)
        assert data['user'] == self.blog.user.name
        assert data['collaborators'][0] == self.blog.collaborators[0].name

    def test_flat_nested2(self):
        class FlatBlogSerializer(Serializer):
            name = fields.String()
            collaborators = fields.Nested(UserSerializer, many=True, only='uid')

        s = FlatBlogSerializer()
        data, _ = s.dump(self.blog)
        assert data['collaborators'][0] == str(self.blog.collaborators[0].uid)

    def test_nested(self):
        blog_serializer = BlogSerializer()
        serialized_blog, _ = blog_serializer.dump(self.blog)
        user_serializer = UserSerializer()
        serialized_user, _ = user_serializer.dump(self.user)
        assert serialized_blog['user'] == serialized_user

    def test_nested_many_fields(self):
        serialized_blog, _ = BlogSerializer().dump(self.blog)
        expected = [UserSerializer().dump(col)[0] for col in self.blog.collaborators]
        assert serialized_blog['collaborators'] == expected

    def test_nested_meta_many(self):
        serialized_blog = BlogUserMetaSerializer().dump(self.blog)[0]
        assert len(serialized_blog['collaborators']) == 2
        expected = [UserMetaSerializer().dump(col)[0] for col in self.blog.collaborators]
        assert serialized_blog['collaborators'] == expected

    def test_nested_only(self):
        col1 = User(name="Mick", age=123, id_="abc")
        col2 = User(name="Keith", age=456, id_="def")
        self.blog.collaborators = [col1, col2]
        serialized_blog = BlogSerializerOnly().dump(self.blog)[0]
        assert serialized_blog['collaborators'] == [{"id": col1.id}, {"id": col2.id}]

    def test_exclude(self):
        serialized = BlogSerializerExclude().dump(self.blog)[0]
        assert "uppername" not in serialized['user'].keys()

    def test_only_takes_precedence_over_exclude(self):
        serialized = BlogSerializerOnlyExclude().dump(self.blog)[0]
        assert serialized['user']['name'] == self.user.name

    def test_list_field(self):
        serialized = BlogSerializer().dump(self.blog)[0]
        assert serialized['categories'] == ["humor", "violence"]

    def test_nested_errors(self):
        invalid_user = User("Monty", email="foo")
        blog = Blog("Monty's blog", user=invalid_user)
        serialized_blog, errors = BlogSerializer().dump(blog)
        assert "email" in errors['user']
        expected_msg = "\"{0}\" is not a valid email address.".format(invalid_user.email)
        assert errors['user']['email'] == expected_msg
        # No problems with collaborators
        assert "collaborators" not in errors

    def test_nested_method_field(self):
        data = BlogSerializer().dump(self.blog)[0]
        assert data['user']['is_old']
        assert data['collaborators'][0]['is_old']

    def test_nested_function_field(self):
        data = BlogSerializer().dump(self.blog)[0]
        assert data['user']['lowername'] == self.user.name.lower()
        expected = self.blog.collaborators[0].name.lower()
        assert data['collaborators'][0]['lowername'] == expected

    def test_nested_prefixed_field(self):
        data = BlogSerializerPrefixedUser().dump(self.blog)[0]
        assert data['user']['usr_name'] == self.user.name
        assert data['user']['usr_lowername'] == self.user.name.lower()

    def test_nested_prefixed_many_field(self):
        data = BlogSerializerPrefixedUser().dump(self.blog)[0]
        assert data['collaborators'][0]['usr_name'] == self.blog.collaborators[0].name

    def test_invalid_float_field(self):
        user = User("Joe", age="1b2")
        _, errors = UserSerializer().dump(user)
        assert "age" in errors

    def test_serializer_meta_with_nested_fields(self):
        data = BlogSerializerMeta().dump(self.blog)[0]
        assert data['title'] == self.blog.title
        assert data['user'] == UserSerializer(self.user).data
        assert data['collaborators'] == [UserSerializer(c).data
                                               for c in self.blog.collaborators]
        assert data['categories'] == self.blog.categories

    def test_serializer_with_nested_meta_fields(self):
        # Serializer has user = fields.Nested(UserMetaSerializer)
        s = BlogUserMetaSerializer(self.blog)
        assert s.data['user'] == UserMetaSerializer(self.blog.user).data

    def test_nested_fields_must_be_passed_a_serializer(self):
        class BadNestedFieldSerializer(BlogSerializer):
            user = fields.Nested(fields.String)
        with pytest.raises(ValueError):
            BadNestedFieldSerializer().dump(self.blog)


class TestSelfReference:

    def setup_method(self, method):
        self.employer = User(name="Joe", age=59)
        self.user = User(name="Tom", employer=self.employer, age=28)

    def test_nesting_serializer_within_itself(self):
        class SelfSerializer(Serializer):
            name = fields.String()
            age = fields.Integer()
            employer = fields.Nested("self")

        data, errors = SelfSerializer().dump(self.user)
        assert not errors
        assert data['name'] == self.user.name
        assert data['employer']['name'] == self.employer.name
        assert data['employer']['age'] == self.employer.age

    def test_nesting_within_itself_meta(self):
        class SelfSerializer(Serializer):
            employer = fields.Nested("self")

            class Meta:
                additional = ('name', 'age')

        data, errors = SelfSerializer().dump(self.user)
        assert not errors
        assert data['name'] == self.user.name
        assert data['age'] == self.user.age
        assert data['employer']['name'] == self.employer.name
        assert data['employer']['age'] == self.employer.age

    def test_nested_self_with_only_param(self):
        class SelfSerializer(Serializer):
            employer = fields.Nested('self', only=('name', ))

            class Meta:
                fields = ('name', 'employer')

        data = SelfSerializer().dump(self.user)[0]
        assert data['name'] == self.user.name
        assert data['employer']['name'] == self.employer.name
        assert 'age' not in data['employer']

    def test_nested_many(self):
        class SelfManySerializer(Serializer):
            relatives = fields.Nested('self', many=True)

            class Meta:
                additional = ('name', 'age')

        person = User(name='Foo')
        person.relatives = [User(name="Bar", age=12), User(name='Baz', age=34)]
        data = SelfManySerializer().dump(person)[0]
        assert data['name'] == person.name
        assert len(data['relatives']) == len(person.relatives)
        assert data['relatives'][0]['name'] == person.relatives[0].name
        assert data['relatives'][0]['age'] == person.relatives[0].age


def test_serialization_with_required_field():
    class RequiredUserSerializer(Serializer):
        name = fields.String(required=True)

    user = User(name=None)
    data, errors = RequiredUserSerializer().dump(user)
    assert 'name' in errors
    assert errors['name'] == 'Missing data for required field.'


def test_serialization_with_required_field_and_custom_validator():
    class RequiredGenderSerializer(Serializer):
        gender = fields.String(required=True,
                               validate=lambda x: x.lower() == 'f' or x.lower() == 'm',
                               error="Gender must be 'f' or 'm'.")

    user = dict(gender=None)
    data, errors = RequiredGenderSerializer().dump(user)
    assert errors
    assert 'gender' in errors
    assert errors['gender'] == "Missing data for required field."

    user = dict(gender='Unkown')
    s = RequiredGenderSerializer(user)
    assert s.is_valid() is False
    assert 'gender' in s.errors
    assert s.errors['gender'] == "Gender must be 'f' or 'm'."


class UserContextSerializer(Serializer):
    is_owner = fields.Method('get_is_owner')
    is_collab = fields.Function(lambda user, ctx: user in ctx['blog'])

    def get_is_owner(self, user, context):
        return context['blog'].user.name == user.name


class TestContext:

    def test_context_method(self):
        owner = User('Joe')
        blog = Blog(title='Joe Blog', user=owner)
        context = {'blog': blog}
        data = UserContextSerializer(context=context).dump(owner)[0]
        assert data['is_owner'] is True
        nonowner = User('Fred')
        data = UserContextSerializer(context=context).dump(nonowner)[0]
        assert data['is_owner'] is False

    def test_context_method_function(self):
        owner = User('Fred')
        blog = Blog('Killer Queen', user=owner)
        collab = User('Brian')
        blog.collaborators.append(collab)
        context = {'blog': blog}
        data = UserContextSerializer(context=context).dump(collab)[0]
        assert data['is_collab'] is True
        noncollab = User('Foo')
        data = UserContextSerializer(context=context).dump(noncollab)[0]
        assert data['is_collab'] is False

    def test_function_field_raises_error_when_context_not_available(self):
        owner = User('Joe')
        # no context
        with pytest.raises(MarshallingError):
            UserContextSerializer(strict=True).dump(owner)

def raise_marshalling_value_error():
    try:
        raise ValueError('Foo bar')
    except ValueError as error:
        raise MarshallingError(error)

class TestMarshallingError:

    def test_saves_underlying_exception(self):
        with pytest.raises(MarshallingError) as excinfo:
            raise_marshalling_value_error()
        assert 'Foo bar' in str(excinfo)
        error = excinfo.value
        assert isinstance(error.underlying_exception, ValueError)


def test_error_gets_raised_if_many_is_omitted(user):
    class BadSerializer(Serializer):
        # forgot to set many=True
        class Meta:
            fields = ('name', 'relatives')
        relatives = fields.Nested(UserSerializer)

    user.relatives = [User('Joe'), User('Mike')]

    with pytest.raises(TypeError) as excinfo:
        BadSerializer().dump(user)
        # Exception includes message about setting many argument
        assert 'many=True' in str(excinfo)
