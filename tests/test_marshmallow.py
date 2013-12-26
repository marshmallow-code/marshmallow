#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2 as unittest
import json
import datetime as dt
import uuid
import warnings

from nose.tools import *  # PEP8 asserts
import pytz

from marshmallow import Serializer, fields, validate, pprint, utils
from marshmallow.exceptions import MarshallingError
from marshmallow.compat import LINUX, unicode, PY26, binary_type, total_seconds

if PY26:
    def assert_in(obj, cont):
        assert obj in cont, "{0} not in {1}".format(obj, cont)
    def assert_not_in(obj, cont):
        assert obj not in cont, "{0} found in {1}".format(obj, cont)

central = pytz.timezone("US/Central")

##### Models #####

class User(object):
    SPECIES = "Homo sapiens"

    def __init__(self, name, age=0, id_=None, homepage=None,
                email=None, registered=True, time_registered=None,
                birthdate=None, balance=100, sex='male', employer=None):
        self.name = name
        self.age = age
        # A naive datetime
        self.created = dt.datetime(2013, 11, 10, 14, 20, 58)
        # A TZ-aware datetime
        self.updated = central.localize(dt.datetime(2013, 11, 10, 14, 20, 58), is_dst=False)
        self.id = id_
        self.homepage = homepage
        self.email = email
        self.balance = balance
        self.registered = True
        self.hair_colors = ['black', 'brown', 'blond', 'redhead']
        self.sex_choices = ('male', 'female')
        self.finger_count = 10
        self.uid = uuid.uuid1()
        self.time_registered = time_registered or dt.time(1, 23, 45, 6789)
        self.birthdate = birthdate or dt.date(2013, 1, 23)
        self.sex = sex
        self.employer = employer
        self.relatives = []


    @property
    def since_created(self):
        return dt.datetime(2013, 11, 24) - self.created

    def __repr__(self):
        return "<User {0}>".format(self.name)


class Blog(object):

    def __init__(self, title, user, collaborators=None, categories=None, id_=None):
        self.title = title
        self.user = user
        self.collaborators = collaborators  # List/tuple of users
        self.categories = categories
        self.id = id_

###### Serializers #####

class Uppercased(fields.Raw):
    '''Custom field formatting example.'''
    def format(self, value):
        return value.upper()


class UserSerializer(Serializer):
    name = fields.String()
    age = fields.Float()
    created = fields.DateTime()
    created_formatted = fields.DateTime(format="%Y-%m-%d", attribute="created")
    created_iso = fields.DateTime(format="iso", attribute="created")
    updated = fields.DateTime()
    updated_local = fields.LocalDateTime(attribute="updated")
    species = fields.String(attribute="SPECIES")
    id = fields.String(default="no-id")
    uppername = Uppercased(attribute='name')
    homepage = fields.Url()
    email = fields.Email()
    balance = fields.Price()
    is_old = fields.Method("get_is_old")
    lowername = fields.Function(lambda obj: obj.name.lower())
    registered = fields.Boolean()
    hair_colors = fields.List(fields.Raw)
    sex_choices = fields.List(fields.Raw)
    finger_count = fields.Integer()
    uid  = fields.UUID()
    time_registered = fields.Time()
    birthdate = fields.Date()
    since_created = fields.TimeDelta()
    sex = fields.Select(['male', 'female'])


    def get_is_old(self, obj):
        try:
            return obj.age > 80
        except TypeError as te:
            raise MarshallingError(te)

class UserMetaSerializer(Serializer):
    '''The equivalent of the UserSerializer, using the ``fields`` option.'''
    uppername = Uppercased(attribute='name')
    balance = fields.Price()
    is_old = fields.Method("get_is_old")
    lowername = fields.Function(lambda obj: obj.name.lower())
    updated_local = fields.LocalDateTime(attribute="updated")
    species = fields.String(attribute="SPECIES")
    homepage = fields.Url()
    email = fields.Email()

    def get_is_old(self, obj):
        try:
            return obj.age > 80
        except TypeError as te:
            raise MarshallingError(te)

    class Meta:
        fields = ('name', 'age', 'created', 'updated', 'id', 'homepage',
                   'uppername', 'email', 'balance', 'is_old', 'lowername',
                   "updated_local", "species", 'registered', 'hair_colors',
                   'sex_choices', "finger_count", 'uid', 'time_registered',
                   'birthdate', 'since_created')


class UserExcludeSerializer(UserSerializer):
    class Meta:
        exclude = ("created", "updated", "field_not_found_but_thats_ok")

class UserAdditionalSerializer(Serializer):
    lowername = fields.Function(lambda obj: obj.name.lower())
    class Meta:
        additional = ("name", "age", "created", "email")

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

class UserRelativeUrlSerializer(UserSerializer):
    homepage = fields.Url(relative=True)

class BlogSerializer(Serializer):
    title = fields.String()
    user = fields.Nested(UserSerializer)
    collaborators = fields.Nested(UserSerializer, many=True)
    categories = fields.List(fields.String)
    id = fields.String()

class BlogUserMetaSerializer(Serializer):
    user = fields.Nested(UserMetaSerializer)
    collaborators = fields.Nested(UserMetaSerializer, many=True)


class BlogSerializerMeta(Serializer):
    '''Same as BlogSerializer but using ``fields`` options.'''
    user = fields.Nested(UserSerializer)
    collaborators = fields.Nested(UserSerializer, many=True)

    class Meta:
        fields = ('title', 'user', 'collaborators', 'categories', "id")

class BlogSerializerOnly(Serializer):
    title = fields.String()
    user = fields.Nested(UserSerializer)
    collaborators = fields.Nested(UserSerializer, only=("id", ), many=True)

class BlogSerializerExclude(BlogSerializer):
    user = fields.Nested(UserSerializer, exclude=("uppername", "species"))

class BlogSerializerOnlyExclude(BlogSerializer):
    user = fields.Nested(UserSerializer, only=("name", ), exclude=("name", "species"))

class BlogSerializerPrefixedUser(BlogSerializer):
    user = fields.Nested(UserSerializer(prefix="usr_"))
    collaborators = fields.Nested(UserSerializer(prefix="usr_"), many=True)

##### The Tests #####


class TestSerializer(unittest.TestCase):

    def setUp(self):
        self.obj = User(name="Monty", age=42.3, homepage="http://monty.python.org/")
        self.serialized = UserSerializer(self.obj)

    def test_serializing_basic_object(self):
        assert_equal(self.serialized.data['name'], "Monty")
        assert_almost_equal(self.serialized.data['age'], 42.3)
        assert_true(self.serialized.data['registered'])

    def test_fields_are_copies(self):
        s = UserSerializer(User("Monty", age=42))
        s2 = UserSerializer(User("Monty", age=43))
        assert_true(s.fields is not s2.fields)

    def test_json(self):
        json_data = self.serialized.json
        expected = binary_type(json.dumps(self.serialized.data).encode("utf-8"))
        assert_equal(json_data, expected)

    def test_to_json_returns_bytestring(self):
        assert_true(isinstance(self.serialized.to_json(), binary_type))

    def test_naive_datetime_field(self):
        assert_equal(self.serialized.data['created'],
                    'Sun, 10 Nov 2013 14:20:58 -0000')

    def test_datetime_formatted_field(self):
        assert_equal(self.serialized.data['created_formatted'],
            self.obj.created.strftime("%Y-%m-%d"))

    def test_datetime_iso_field(self):
        assert_equal(self.serialized.data['created_iso'],
            utils.isoformat(self.obj.created))

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
        serialized = UserSerializer(users, many=True)
        assert_equal(len(serialized.data), 2)
        assert_equal(serialized.data[0]['name'], "Mick")
        assert_equal(serialized.data[1]['name'], "Keith")

    def test_no_implicit_list_handling(self):
        users = [User(name='Mick'), User(name='Keith')]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            assert_raises(TypeError, lambda: UserSerializer(users))
        assert_true(issubclass(w[-1].category, DeprecationWarning))

    def test_serialize_many_with_meta(self):
        user1 = User(name="Mick", age=123)
        user2 = User(name="Keith", age=456)
        users = [user1, user2]
        s = UserMetaSerializer(users, many=True)
        assert_equal(len(s.data), 2)
        assert_equal(s.data[0]['name'], "Mick")
        assert_equal(s.data[0]['created'], utils.rfcformat(user1.created))
        assert_equal(s.data[1]['name'], "Keith")

    def test_inheriting_serializer(self):
        serialized = ExtendedUserSerializer(self.obj)
        assert_equal(serialized.data['name'], self.obj.name)
        assert_false(serialized.data['is_old'])

    def test_custom_field(self):
        assert_equal(self.serialized.data['uppername'], "MONTY")

    def test_url_field(self):
        assert_equal(self.serialized.data['homepage'], "http://monty.python.org/")

    def test_url_field_validation(self):
        invalid = User("John", age=42, homepage="/john")
        s = UserSerializer(invalid)
        assert_false(s.is_valid(["homepage"]))

    def test_relative_url_field(self):
        u = User("John", age=42, homepage="/john")
        serialized = UserRelativeUrlSerializer(u)
        assert_true(serialized.is_valid())

    def test_stores_invalid_url_error(self):
        user = User(name="John Doe", homepage="www.foo.com")
        serialized = UserSerializer(user)
        assert_in("homepage", serialized.errors)
        assert_equal(serialized.errors['homepage'],
            '"www.foo.com" is not a valid URL. Did you mean: "http://www.foo.com"?')

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
        assert_equal(s.errors['email'], '"johnexample.com" is not a valid email address.')

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
        assert_equal(type(serialized.data['age']), str)
        assert_almost_equal(float(serialized.data['age']), 42.3)

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

    def test_validating_nonexistent_field_raises_error(self):
        assert_raises(KeyError, lambda: self.serialized.is_valid(["foobar"]))

    def test_fields_param_must_be_list_or_tuple(self):
        invalid = User("John", email="johnexample.com")
        assert_raises(ValueError, lambda: UserSerializer(invalid).is_valid("name"))

    def test_extra(self):
        user = User("Joe", email="joe@foo.com")
        s = UserSerializer(user, extra={"fav_color": "blue"})
        assert_equal(s.data['fav_color'], "blue")

    def test_method_field(self):
        assert_false(self.serialized.data['is_old'])
        u = User("Joe", age=81)
        assert_true(UserSerializer(u).data['is_old'])

    def test_function_field(self):
        assert_equal(self.serialized.data['lowername'], self.obj.name.lower())

    def test_prefix(self):
        s = UserSerializer(self.obj, prefix="usr_")
        assert_equal(s.data['usr_name'], self.obj.name)

    def test_fields_must_be_declared_as_instances(self):
        class BadUserSerializer(Serializer):
            name = fields.String
        assert_raises(TypeError, lambda: BadUserSerializer(self.obj))

    def test_serializing_generator(self):
        users = [User("Foo"), User("Bar")]
        user_gen = (u for u in users)
        s = UserSerializer(user_gen, many=True)
        assert_equal(len(s.data), 2)
        assert_equal(s.data[0], UserSerializer(users[0]).data)

    def test_serializing_generator_with_meta_fields(self):
        users = [User("Foo"), User("Bar")]
        user_gen = (u for u in users)
        s = UserMetaSerializer(user_gen, many=True)
        assert_equal(len(s.data), 2)
        assert_equal(s.data[0], UserMetaSerializer(users[0]).data)

    def test_serializing_empty_list_returns_empty_list(self):
        assert_equal(UserSerializer([], many=True).data, [])
        assert_equal(UserMetaSerializer([], many=True).data, [])

    def test_serializing_dict(self):
        user = {"name": "foo", "email": "foo", "age": 42.3}
        s = UserSerializer(user)
        assert_equal(s.data['name'], "foo")
        assert_equal(s.data['age'], 42.3)
        assert_false(s.is_valid(['email']))

    def test_exclude_in_init(self):
        s = UserSerializer(self.obj, exclude=('age', 'homepage'))
        assert_not_in('homepage', s.data)
        assert_not_in('age', s.data)
        assert_in('name', s.data)

    def test_only_in_init(self):
        s = UserSerializer(self.obj, only=('name', 'age'))
        assert_not_in('homepage', s.data)
        assert_in('name', s.data)
        assert_in('age', s.data)

    def test_invalid_only_param(self):
        assert_raises(AttributeError,
            lambda: UserSerializer(self.obj, only=("_invalid", "name")))

    def test_strict_init(self):
        invalid = User("Foo", email="foo.com")
        assert_raises(MarshallingError, lambda: UserSerializer(invalid, strict=True))

    def test_strict_meta_option(self):
        class StrictUserSerializer(UserSerializer):
            class Meta:
                strict = True
        invalid = User("Foo", email="foo.com")
        assert_raises(MarshallingError, lambda: StrictUserSerializer(invalid))

    def test_can_serialize_uuid(self):
        assert_equal(self.serialized.data['uid'], str(self.obj.uid))

    def test_can_serialize_time(self):
        assert_equal(self.serialized.data['time_registered'],
            self.obj.time_registered.isoformat()[:12])

    def test_invalid_time(self):
        u = User('Joe', time_registered='foo')
        s = UserSerializer(u)
        assert_false(s.is_valid(['time_registered']))
        assert_equal(s.errors['time_registered'],
            "'foo' cannot be formatted as a time.")

    def test_invalid_date(self):
        u = User("Joe", birthdate='foo')
        s = UserSerializer(u)
        assert_false(s.is_valid(['birthdate']))
        assert_equal(s.errors['birthdate'],
            "'foo' cannot be formatted as a date.")

    def test_invalid_selection(self):
        u = User('Jonhy')
        u.sex = 'hybrid'
        s = UserSerializer(u)
        assert_false(s.is_valid(['sex']))
        assert_equal(s.errors['sex'],
            "'hybrid' is not a valid choice for this field.")


def test_custom_error_message():
    class ErrorSerializer(Serializer):
        email = fields.Email(error="Invalid email")
        homepage = fields.Url(error="Bad homepage.")
        balance = fields.Fixed(error="Bad balance.")


    u = User("Joe", email="joe.net", homepage="joe@example.com", balance="blah")
    s = ErrorSerializer(u)
    assert_false(s.is_valid())
    assert_equal(s.errors['email'], "Invalid email")
    assert_equal(s.errors['homepage'], "Bad homepage.")
    assert_equal(s.errors['balance'], "Bad balance.")


class TestMetaOptions(unittest.TestCase):
    def setUp(self):
        self.obj = User(name="Monty", age=42.3, homepage="http://monty.python.org/")
        self.serialized = UserSerializer(self.obj)

    def test_meta_serializer_fields(self):
        u = User("John", age=42.3, email="john@example.com",
                homepage="http://john.com")
        s = UserMetaSerializer(u)
        assert_equal(s.data['name'], u.name)
        assert_equal(s.data['balance'], "100.00")
        assert_equal(s.data['uppername'], "JOHN")
        assert_false(s.data['is_old'])
        assert_equal(s.data['created'], utils.rfcformat(u.created))
        assert_equal(s.data['updated_local'], utils.rfcformat(u.updated, localtime=True))
        assert_equal(s.data['finger_count'], 10)

    def test_meta_fields_mapping(self):
        s = UserMetaSerializer(self.obj)
        assert_equal(type(s.fields['name']), fields.String)
        assert_equal(type(s.fields['created']), fields.DateTime)
        assert_equal(type(s.fields['updated']), fields.DateTime)
        assert_equal(type(s.fields['updated_local']), fields.LocalDateTime)
        assert_equal(type(s.fields['age']), fields.Float)
        assert_equal(type(s.fields['balance']), fields.Price)
        assert_equal(type(s.fields['registered']), fields.Boolean)
        assert_equal(type(s.fields['sex_choices']), fields.Raw)
        assert_equal(type(s.fields['hair_colors']), fields.Raw)
        assert_equal(type(s.fields['finger_count']), fields.Integer)
        assert_equal(type(s.fields['uid']), fields.UUID)
        assert_equal(type(s.fields['time_registered']), fields.Time)
        assert_equal(type(s.fields['birthdate']), fields.Date)
        assert_equal(type(s.fields['since_created']), fields.TimeDelta)

    def test_meta_field_not_on_obj_raises_attribute_error(self):
        class BadUserSerializer(Serializer):
            class Meta:
                fields = ('name', 'notfound')
        assert_raises(AttributeError, lambda: BadUserSerializer(self.obj))

    def test_exclude_fields(self):
        s = UserExcludeSerializer(self.obj)
        assert_not_in("created", s.data)
        assert_not_in("updated", s.data)
        assert_in("name", s.data)

    def test_fields_option_must_be_list_or_tuple(self):
        class BadFields(Serializer):
            class Meta:
                fields = "name"
        assert_raises(ValueError, lambda: BadFields(self.obj))

    def test_exclude_option_must_be_list_or_tuple(self):
        class BadExclude(Serializer):
            class Meta:
                exclude = "name"
        assert_raises(ValueError, lambda: BadExclude(self.obj))

    def test_dateformat_option(self):
        format = '%Y-%m'
        class DateFormatSerializer(Serializer):
            updated = fields.DateTime("%m-%d")
            class Meta:
                fields = ('created', 'updated')
                dateformat = format
        serialized = DateFormatSerializer(self.obj)
        assert_equal(serialized.data['created'], self.obj.created.strftime(format))
        assert_equal(serialized.data['updated'], self.obj.updated.strftime("%m-%d"))

    def test_default_dateformat(self):
        class DateFormatSerializer(Serializer):
            updated = fields.DateTime(format="%m-%d")
            class Meta:
                fields = ('created', 'updated')
        serialized = DateFormatSerializer(self.obj)
        assert_equal(serialized.data['created'], utils.rfcformat(self.obj.created))
        assert_equal(serialized.data['updated'], self.obj.updated.strftime("%m-%d"))

    def test_inherit_meta(self):
        class InheritedMetaSerializer(UserMetaSerializer):
            pass

        assert_equal(InheritedMetaSerializer(self.obj).data,
                    UserMetaSerializer(self.obj).data)

    def test_additional(self):
        s = UserAdditionalSerializer(self.obj)
        assert_equal(s.data['lowername'], self.obj.name.lower())
        assert_equal(s.data['name'], self.obj.name)

    def test_cant_set_both_additional_and_fields(self):
        class BadSerializer(Serializer):
            name = fields.String()
            class Meta:
                fields = ("name", 'email')
                additional = ('email', 'homepage')
        assert_raises(ValueError, lambda: BadSerializer(self.obj))

    def test_serializing_none(self):
        s = UserMetaSerializer(None)
        assert_equal(s.data['name'], None)
        assert_equal(s.data['email'], None)


class TestNestedSerializer(unittest.TestCase):

    def setUp(self):
        self.user = User(name="Monty", age=81)
        col1 = User(name="Mick", age=123)
        col2 = User(name="Keith", age=456)
        self.blog = Blog("Monty's blog", user=self.user, categories=["humor", "violence"],
                        collaborators=[col1, col2])

    def test_nested(self):
        serialized_blog = BlogSerializer(self.blog)
        serialized_user = UserSerializer(self.user)
        assert_equal(serialized_blog.data['user'], serialized_user.data)

    def test_nested_many_fields(self):
        serialized_blog = BlogSerializer(self.blog)
        assert_equal(serialized_blog.data['collaborators'],
            [UserSerializer(col).data for col in self.blog.collaborators])

    def test_nested_meta_many(self):
        serialized_blog = BlogUserMetaSerializer(self.blog)
        assert_equal(len(serialized_blog.data['collaborators']), 2)
        assert_equal(serialized_blog.data['collaborators'],
            [UserMetaSerializer(col).data for col in self.blog.collaborators])

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
        assert_in("email", serialized_blog.errors['user'])
        assert_equal(serialized_blog.errors['user']['email'],
            "\"{0}\" is not a valid email address.".format(invalid_user.email))
        # No problems with collaborators
        assert_not_in("collaborators", serialized_blog.errors)

    def test_nested_method_field(self):
        s = BlogSerializer(self.blog)
        assert_true(s.data['user']['is_old'])
        assert_true(s.data['collaborators'][0]['is_old'])

    def test_nested_function_field(self):
        s = BlogSerializer(self.blog)
        assert_equal(s.data['user']['lowername'], self.user.name.lower())
        assert_equal(s.data['collaborators'][0]['lowername'],
                    self.blog.collaborators[0].name.lower())

    def test_nested_prefixed_field(self):
        s = BlogSerializerPrefixedUser(self.blog)
        assert_equal(s.data['user']['usr_name'], self.user.name)
        assert_equal(s.data['user']['usr_lowername'], self.user.name.lower())

    def test_nested_prefixed_many_field(self):
        s = BlogSerializerPrefixedUser(self.blog)
        assert_equal(s.data['collaborators'][0]['usr_name'],
                     self.blog.collaborators[0].name)

    def test_invalid_float_field(self):
        user = User("Joe", age="1b2")
        s = UserSerializer(user)
        assert_false(s.is_valid(["age"]))
        assert_in("age", s.errors)

    def test_serializer_meta_with_nested_fields(self):
        s = BlogSerializerMeta(self.blog)
        assert_equal(s.data['title'], self.blog.title)
        assert_equal(s.data['user'], UserSerializer(self.user).data)
        assert_equal(s.data['collaborators'], [UserSerializer(c).data
                                                for c in self.blog.collaborators])
        assert_equal(s.data['categories'], self.blog.categories)

    def test_serializer_with_nested_meta_fields(self):
        # Serializer has user = fields.Nested(UserMetaSerializer)
        s = BlogUserMetaSerializer(self.blog)
        assert_equal(s.data['user'], UserMetaSerializer(self.blog.user).data)

    def test_nested_fields_must_be_passed_a_serializer(self):
        class BadNestedFieldSerializer(BlogSerializer):
            user = fields.Nested(fields.String)
        assert_raises(ValueError, lambda: BadNestedFieldSerializer(self.blog))



class TestSelfReference(unittest.TestCase):

    def setUp(self):
        self.employer = User(name="Joe", age=59)
        self.user = User(name="Tom", employer=self.employer, age=28)

    def test_nesting_serializer_within_itself(self):
        class SelfSerializer(Serializer):
            name = fields.String()
            age = fields.Integer()
            employer = fields.Nested("self")

        s = SelfSerializer(self.user)
        assert_true(s.is_valid())
        assert_equal(s.data['name'], self.user.name)
        assert_equal(s.data['employer']['name'], self.employer.name)
        assert_equal(s.data['employer']['age'], self.employer.age)

    def test_nesting_within_itself_meta(self):
        class SelfSerializer(Serializer):
            employer = fields.Nested("self")
            class Meta:
                additional = ('name', 'age')

        s = SelfSerializer(self.user)
        assert_true(s.is_valid())
        assert_equal(s.data['name'], self.user.name)
        assert_equal(s.data['age'], self.user.age)
        assert_equal(s.data['employer']['name'], self.employer.name)
        assert_equal(s.data['employer']['age'], self.employer.age)

    def test_nested_self_with_only_param(self):
        class SelfSerializer(Serializer):
            employer = fields.Nested('self', only=('name', ))
            class Meta:
                fields = ('name', 'employer')

        s = SelfSerializer(self.user)
        assert_equal(s.data['name'], self.user.name)
        assert_equal(s.data['employer']['name'], self.employer.name)
        assert_not_in('age', s.data['employer'])

    def test_nested_many(self):
        class SelfManySerializer(Serializer):
            relatives = fields.Nested('self', many=True)
            class Meta:
                additional = ('name', 'age')

        person = User(name='Foo')
        person.relatives = [User(name="Bar", age=12), User(name='Baz', age=34)]
        s = SelfManySerializer(person)
        assert_equal(s.data['name'], person.name)
        assert_equal(len(s.data['relatives']), len(person.relatives))
        assert_equal(s.data['relatives'][0]['name'], person.relatives[0].name)
        assert_equal(s.data['relatives'][0]['age'], person.relatives[0].age)


class TestFields(unittest.TestCase):

    def setUp(self):
        self.user = User("Foo", "foo@bar.com")

    def test_repr(self):
        field = fields.String()
        assert_equal(repr(field), "<String Field>")

    def test_function_field(self):
        field = fields.Function(lambda obj: obj.name.upper())
        assert_equal("FOO", field.output("key", self.user))

    def test_function_with_uncallable_param(self):
        field = fields.Function("uncallable")
        assert_raises(MarshallingError, lambda: field.output("key", self.user))

    def test_datetime_field(self):
        field = fields.DateTime()
        assert_equal(field.output("created", self.user),
            utils.rfcformat(self.user.created, localtime=False))

    def test_localdatetime_field(self):
        field = fields.LocalDateTime()
        assert_equal(field.output("created", self.user),
            utils.rfcformat(self.user.created, localtime=True))

    def test_datetime_iso8601(self):
        field = fields.DateTime(format="iso")
        assert_equal(field.output("created", self.user),
            utils.isoformat(self.user.created, localtime=False))

    def test_localdatetime_iso(self):
        field = fields.LocalDateTime(format="iso")
        assert_equal(field.output("created", self.user),
            utils.isoformat(self.user.created, localtime=True))

    def test_datetime_format(self):
        format = "%Y-%m-%d"
        field = fields.DateTime(format=format)
        assert_equal(field.output("created", self.user),
            self.user.created.strftime(format))

    def test_string_field_defaults_to_empty_string(self):
        field = fields.String()
        assert_equal(field.output("notfound", self.user), '')

    def test_time_field(self):
        field = fields.Time()
        assert_equal(field.output("time_registered", self.user),
                self.user.time_registered.isoformat()[:12])

    def test_date_field(self):
        field = fields.Date()
        assert_equal(field.output('birthdate', self.user),
            self.user.birthdate.isoformat())

    def test_timedelta_field(self):
        field = fields.TimeDelta()
        assert_equal(field.output("since_created", self.user),
            total_seconds(self.user.since_created))

    def test_select_field(self):
        field = fields.Select(['male', 'female'])
        assert_equal(field.output("sex", self.user),
                     "male")

    def test_bad_list_field(self):
        assert_raises(MarshallingError, lambda: fields.List("string"))
        assert_raises(MarshallingError, lambda: fields.List(UserSerializer))


class TestUtils(unittest.TestCase):

    def test_to_marshallable_type(self):
        class Foo(object):
            CLASS_VAR = 'bar'
            def __init__(self):
                self.attribute = 'baz'
            @property
            def prop(self):
                return 42
        obj = Foo()
        u_dict = utils.to_marshallable_type(obj)
        assert_equal(u_dict['CLASS_VAR'], Foo.CLASS_VAR)
        assert_equal(u_dict['attribute'], obj.attribute)
        assert_equal(u_dict['prop'], obj.prop)

    def test_to_marshallable_type_none(self):
        assert_equal(utils.to_marshallable_type(None), None)

    def test_to_marshallable_type_list(self):
        assert_equal(utils.to_marshallable_type(['foo', 'bar']), ['foo', 'bar'])

    def test_to_marshallable_type_generator(self):
        gen = (e for e in ['foo', 'bar'])
        assert_equal(utils.to_marshallable_type(gen), ['foo', 'bar'])

    def test_marshallable(self):
        class ObjContainer(object):
            contained = {"foo": 1}
            def __marshallable__(self):
                return self.contained

        obj = ObjContainer()
        assert_equal(utils.to_marshallable_type(obj), {"foo": 1})


    def test_is_collection(self):
        assert_true(utils.is_collection([1, 'foo', {}]))
        assert_true(utils.is_collection(('foo', 2.3)))
        assert_false(utils.is_collection({'foo': 'bar'}))

    def test_rfcformat_gmt_naive(self):
        d = dt.datetime(2013, 11, 10, 1, 23, 45)
        assert_equal(utils.rfcformat(d), "Sun, 10 Nov 2013 01:23:45 -0000")

    @unittest.skipIf(LINUX, "Skip due to different localtime behavior on Linux")
    def test_rfcformat_central(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
        assert_equal(utils.rfcformat(d), 'Sun, 10 Nov 2013 07:23:45 -0000')

    @unittest.skipIf(LINUX, "Skip due to different localtime behavior on Linux")
    def test_rfcformat_central_localized(self):
        d = central.localize(dt.datetime(2013, 11, 10, 8, 23, 45), is_dst=False)
        assert_equal(utils.rfcformat(d, localtime=True), "Sun, 10 Nov 2013 08:23:45 -0600")

    def test_isoformat(self):
        d = dt.datetime(2013, 11, 10, 1, 23, 45)
        assert_equal(utils.isoformat(d), '2013-11-10T01:23:45+00:00')

    def test_isoformat_tzaware(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
        assert_equal(utils.isoformat(d), "2013-11-10T07:23:45+00:00")

    def test_isoformat_localtime(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
        assert_equal(utils.isoformat(d, localtime=True), "2013-11-10T01:23:45-06:00")


class TestValidators(unittest.TestCase):

    def test_invalid_email(self):
        invalid1 = "user@example"
        assert_raises(ValueError, lambda: validate.email(invalid1))
        invalid2 = "example.com"
        assert_raises(ValueError, lambda: validate.email(invalid2))
        invalid3 = "user"
        assert_raises(ValueError, lambda: validate.email(invalid3))


class TestMarshaller(unittest.TestCase):

    def test_stores_errors(self):
        u = User("Foo", email="foobar")
        marshal = fields.Marshaller()
        marshal(u, {"email": fields.Email()})
        assert_in("email", marshal.errors)

    def test_strict_mode_raises_errors(self):
        u = User("Foo", email="foobar")
        marshal = fields.Marshaller(strict=True)
        assert_raises(MarshallingError,
            lambda: marshal(u, {"email": fields.Email()}))

    def test_prefix(self):
        u = User("Foo", email="foo@bar.com")
        marshal = fields.Marshaller(prefix='usr_')
        result = marshal(u, {"email": fields.Email(), 'name': fields.String()})
        assert_equal(result['usr_name'], u.name)
        assert_equal(result['usr_email'], u.email)


if __name__ == '__main__':
    unittest.main()
