#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest2 as unittest
import json
import datetime as dt
import uuid

from nose.tools import *  # PEP8 asserts
import pytz

from marshmallow import Serializer, fields, types, pprint, utils
from marshmallow.exceptions import MarshallingError
from marshmallow.compat import LINUX, unicode, PY26

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
                email=None, registered=True):
        self.name = name
        self.age = age
        # A naive datetime
        self.created = dt.datetime(2013, 11, 10, 14, 20, 58)
        # A TZ-aware datetime
        self.updated = central.localize(dt.datetime(2013, 11, 10, 14, 20, 58), is_dst=False)
        self.id = id_
        self.homepage = homepage
        self.email = email
        self.balance = 100
        self.registered = True
        self.hair_colors = ['black', 'brown', 'blond', 'redhead']
        self.sex_choices = ('male', 'female')
        self.finger_count = 10
        self.uid = uuid.uuid1()

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
                   'sex_choices', "finger_count", 'uid')


class UserExcludeSerializer(UserSerializer):
    class Meta:
        exclude = ("created", "updated", "field_not_found_but_thats_ok")

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
    collaborators = fields.Nested(UserSerializer)
    categories = fields.List(fields.String)
    id = fields.String()

class BlogUserMetaSerializer(Serializer):
    user = fields.Nested(UserMetaSerializer)
    collaborators = fields.Nested(UserMetaSerializer)


class BlogSerializerMeta(Serializer):
    '''Same as BlogSerializer but using ``fields`` options.'''
    user = fields.Nested(UserSerializer)
    collaborators = fields.Nested(UserSerializer)

    class Meta:
        fields = ('title', 'user', 'collaborators', 'categories', "id")

class BlogSerializerOnly(Serializer):
    title = fields.String()
    user = fields.Nested(UserSerializer)
    collaborators = fields.Nested(UserSerializer, only=("id", ))

class BlogSerializerExclude(BlogSerializer):
    user = fields.Nested(UserSerializer, exclude=("uppername", "species"))

class BlogSerializerOnlyExclude(BlogSerializer):
    user = fields.Nested(UserSerializer, only=("name", ), exclude=("name", "species"))

class BlogSerializerPrefixedUser(BlogSerializer):
    user = fields.Nested(UserSerializer(prefix="usr_"))
    collaborators = fields.Nested(UserSerializer(prefix="usr_"))

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
        assert_equal(json_data, json.dumps(self.serialized.data))

    def test_naive_datetime_field(self):
        assert_equal(self.serialized.data['created'],
                    'Sun, 10 Nov 2013 14:20:58 -0000')

    def test_datetime_formatted_field(self):
        assert_equal(self.serialized.data['created_formatted'],
            self.obj.created.strftime("%Y-%m-%d"))

    def test_datetime_iso_field(self):
        assert_equal(self.serialized.data['created_iso'],
            types.isoformat(self.obj.created))

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
        serialized = UserSerializer(users)
        assert_equal(len(serialized.data), 2)
        assert_equal(serialized.data[0]['name'], "Mick")
        assert_equal(serialized.data[1]['name'], "Keith")

    def test_serialize_many_with_meta(self):
        user1 = User(name="Mick", age=123)
        user2 = User(name="Keith", age=456)
        users = [user1, user2]
        s = UserMetaSerializer(users)
        assert_equal(len(s.data), 2)
        assert_equal(s.data[0]['name'], "Mick")
        assert_equal(s.data[0]['created'], types.rfcformat(user1.created))
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

    def test_serializing_empty_list_returns_empty_list(self):
        assert_equal(UserSerializer([]).data, [])
        assert_equal(UserMetaSerializer([]).data, [])

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
        assert_equal(s.data['created'], types.rfcformat(u.created))
        assert_equal(s.data['updated_local'], types.rfcformat(u.updated, localtime=True))
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
            updated = fields.DateTime(format="%m-%d")
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
        assert_equal(serialized.data['created'], types.rfcformat(self.obj.created))
        assert_equal(serialized.data['updated'], self.obj.updated.strftime("%m-%d"))


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
            types.rfcformat(self.user.created, localtime=False))

    def test_localdatetime_field(self):
        field = fields.LocalDateTime()
        assert_equal(field.output("created", self.user),
            types.rfcformat(self.user.created, localtime=True))

    def test_datetime_iso8601(self):
        field = fields.DateTime(format="iso")
        assert_equal(field.output("created", self.user),
            types.isoformat(self.user.created, localtime=False))

    def test_localdatetime_iso(self):
        field = fields.LocalDateTime(format="iso")
        assert_equal(field.output("created", self.user),
            types.isoformat(self.user.created, localtime=True))

    def test_datetime_format(self):
        format = "%Y-%m-%d"
        field = fields.DateTime(format=format)
        assert_equal(field.output("created", self.user),
            self.user.created.strftime(format))


class TestUtils(unittest.TestCase):

    def test_to_marshallable_type(self):
        u = User("Foo", "foo@bar.com")
        assert_equal(utils.to_marshallable_type(u), u.__dict__)
        assert_equal(utils.to_marshallable_type(None), None)

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


class TestTypes(unittest.TestCase):

    def test_rfcformat_gmt_naive(self):
        d = dt.datetime(2013, 11, 10, 1, 23, 45)
        assert_equal(types.rfcformat(d), "Sun, 10 Nov 2013 01:23:45 -0000")

    @unittest.skipIf(LINUX, "Skip due to different localtime behavior on Linux")
    def test_rfcformat_central(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
        assert_equal(types.rfcformat(d), 'Sun, 10 Nov 2013 07:23:45 -0000')

    @unittest.skipIf(LINUX, "Skip due to different localtime behavior on Linux")
    def test_rfcformat_central_localized(self):
        d = central.localize(dt.datetime(2013, 11, 10, 8, 23, 45), is_dst=False)
        assert_equal(types.rfcformat(d, localtime=True), "Sun, 10 Nov 2013 08:23:45 -0600")

    def test_invalid_email(self):
        invalid1 = "user@example"
        assert_raises(ValueError, lambda: types.email(invalid1))
        invalid2 = "example.com"
        assert_raises(ValueError, lambda: types.email(invalid2))
        invalid3 = "user"
        assert_raises(ValueError, lambda: types.email(invalid3))

    def test_isoformat(self):
        d = dt.datetime(2013, 11, 10, 1, 23, 45)
        assert_equal(types.isoformat(d), '2013-11-10T01:23:45+00:00')

    def test_isoformat_tzaware(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
        assert_equal(types.isoformat(d), "2013-11-10T07:23:45+00:00")

    def test_isoformat_localtime(self):
        d = central.localize(dt.datetime(2013, 11, 10, 1, 23, 45), is_dst=False)
        assert_equal(types.isoformat(d, localtime=True), "2013-11-10T01:23:45-06:00")

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
