.. module:: marshmallow

Quickstart
==========

This guide will walk you through the basics of creating schemas for serializing and deserializing data.

Declaring Schemas
-----------------

Let's start with a basic user "model".

.. code-block:: python

    import datetime as dt


    class User:
        def __init__(self, name, email):
            self.name = name
            self.email = email
            self.created_at = dt.datetime.now()

        def __repr__(self):
            return "<User(name={self.name!r})>".format(self=self)


Create a schema by defining a class with variables mapping attribute names to :class:`Field <fields.Field>` objects.

.. code-block:: python

    from marshmallow import Schema, fields


    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()
        created_at = fields.DateTime()

.. seealso::

    For a full reference on the available field classes, see the :ref:`API Docs <api_fields>`.


Serializing Objects ("Dumping")
-------------------------------

Serialize objects by passing them to your schema's :meth:`dump <marshmallow.Schema.dump>` method, which returns the formatted result (or raises a :exc:`ValidationError <marshmallow.exceptions.ValidationError>` with a dictionary of validation errors, which we'll :ref:`revisit later <validation>`).

.. code-block:: python

    from marshmallow import pprint

    user = User(name="Monty", email="monty@python.org")
    schema = UserSchema()
    result = schema.dump(user)
    pprint(result)
    # {"name": "Monty",
    #  "email": "monty@python.org",
    #  "created_at": "2014-08-17T14:54:16.049594+00:00"}

You can also serialize to a JSON-encoded string using :meth:`dumps <marshmallow.Schema.dumps>`.

.. code-block:: python

    json_result = schema.dumps(user)
    pprint(json_result)
    # '{"name": "Monty", "email": "monty@python.org", "created_at": "2014-08-17T14:54:16.049594+00:00"}'

Filtering output
++++++++++++++++

You may not need to output all declared fields every time you use a schema. You can specify which fields to output with the ``only`` parameter.

.. code-block:: python

    summary_schema = UserSchema(only=("name", "email"))
    summary_schema.dump(user)
    # {"name": "Monty Python", "email": "monty@python.org"}

You can also exclude fields by passing in the ``exclude`` parameter.


Deserializing Objects ("Loading")
---------------------------------

The opposite of the :meth:`dump <Schema.dump>` method is the :meth:`load <Schema.load>` method, which deserializes an input dictionary to an application-level data structure.

By default, :meth:`load <Schema.load>` will return a dictionary of field names mapped to the deserialized values.

.. code-block:: python

    from pprint import pprint

    user_data = {
        "created_at": "2014-08-11T05:26:03.869245",
        "email": u"ken@yahoo.com",
        "name": u"Ken",
    }
    schema = UserSchema()
    result = schema.load(user_data)
    pprint(result)
    # {'name': 'Ken',
    #  'email': 'ken@yahoo.com',
    #  'created_at': datetime.datetime(2014, 8, 11, 5, 26, 3, 869245)},

Notice that the datetime string was converted to a `datetime` object.

Deserializing to Objects
++++++++++++++++++++++++

In order to deserialize to an object, define a method of your :class:`Schema` and decorate it with `post_load <marshmallow.decorators.post_load>`. The method receives a dictionary of deserialized data as its only parameter.

.. code-block:: python
    :emphasize-lines: 8-10

    from marshmallow import Schema, fields, post_load


    class UserSchema(Schema):
        name = fields.Str()
        email = fields.Email()
        created_at = fields.DateTime()

        @post_load
        def make_user(self, data, **kwargs):
            return User(**data)

Now, the :meth:`load <Schema.load>` method will return a ``User`` object.

.. code-block:: python

    user_data = {"name": "Ronnie", "email": "ronnie@stones.com"}
    schema = UserSchema()
    result = schema.load(user_data)
    result  # => <User(name='Ronnie')>

Handling Collections of Objects
-------------------------------

Iterable collections of objects are also serializable and deserializable. Just set ``many=True``.

.. code-block:: python
    :emphasize-lines: 3,4

    user1 = User(name="Mick", email="mick@stones.com")
    user2 = User(name="Keith", email="keith@stones.com")
    users = [user1, user2]
    schema = UserSchema(many=True)
    result = schema.dump(users)  # OR UserSchema().dump(users, many=True)
    result
    # [{'name': u'Mick',
    #   'email': u'mick@stones.com',
    #   'created_at': '2014-08-17T14:58:57.600623+00:00'}
    #  {'name': u'Keith',
    #   'email': u'keith@stones.com',
    #   'created_at': '2014-08-17T14:58:57.600623+00:00'}]


.. _validation:

Validation
----------

:meth:`Schema.load` (and its JSON-decoding counterpart, :meth:`Schema.loads`) raises a :exc:`ValidationError <marshmallow.exceptions.ValidationError>` error when invalid data are passed in. You can access the dictionary of validation errors from the `ValidationError.messages <marshmallow.exceptions.ValidationError.messages>` attribute. The data that was correctly serialized / deserialized is accessible in `ValidationError.valid_data <marshmallow.exceptions.ValidationError.valid_data>`. Some fields, such as the :class:`Email <fields.Email>` and :class:`URL <fields.URL>` fields, have built-in validation.

.. code-block:: python

    from marshmallow import ValidationError

    try:
        result = UserSchema().load({"name": "John", "email": "foo"})
    except ValidationError as err:
        err.messages  # => {'email': ['"foo" is not a valid email address.']}
        valid_data = err.valid_data  # => {'name': 'John'}


When validating a collection, the errors dictionary will be keyed on the indices of invalid items.

.. code-block:: python

    from marshmallow import ValidationError


    class BandMemberSchema(Schema):
        name = fields.String(required=True)
        email = fields.Email()


    user_data = [
        {"email": "mick@stones.com", "name": "Mick"},
        {"email": "invalid", "name": "Invalid"},  # invalid email
        {"email": "keith@stones.com", "name": "Keith"},
        {"email": "charlie@stones.com"},  # missing "name"
    ]

    try:
        BandMemberSchema(many=True).load(user_data)
    except ValidationError as err:
        err.messages
    # {1: {'email': ['"invalid" is not a valid email address.']},
    #  3: {'name': ['Missing data for required field.']}}

You can perform additional validation for a field by passing it a ``validate`` callable (function, lambda, or object with ``__call__`` defined).

.. code-block:: python
    :emphasize-lines: 6

    from marshmallow import ValidationError


    class ValidatedUserSchema(UserSchema):
        # NOTE: This is a contrived example.
        # You could use marshmallow.validate.Range instead of an anonymous function here
        age = fields.Number(validate=lambda n: 18 <= n <= 40)


    in_data = {"name": "Mick", "email": "mick@stones.com", "age": 71}
    try:
        result = ValidatedUserSchema().load(in_data)
    except ValidationError as err:
        err.messages  # => {'age': ['Validator <lambda>(71.0) is False']}


If validation fails, validation functions raise a :exc:`ValidationError <marshmallow.exceptions.ValidationError>` with an error message.

.. code-block:: python
    :emphasize-lines: 7,10,14

    from marshmallow import Schema, fields, ValidationError


    def validate_quantity(n):
        if n < 0:
            raise ValidationError("Quantity must be greater than 0.")
        if n > 30:
            raise ValidationError("Quantity must not be greater than 30.")


    class ItemSchema(Schema):
        quantity = fields.Integer(validate=validate_quantity)


    in_data = {"quantity": 31}
    try:
        result = ItemSchema().load(in_data)
    except ValidationError as err:
        err.messages  # => {'quantity': ['Quantity must not be greater than 30.']}

.. note::

    If you have multiple validations to perform, you may also pass a collection (list, tuple, generator) of callables.

.. note::

    :meth:`Schema.dump` also returns a dictionary of errors, which will include any ``ValidationErrors`` raised during serialization. However, ``required``, ``allow_none``, ``validate``, `@validates <marshmallow.decorators.validates>`, and `@validates_schema <marshmallow.decorators.validates_schema>` only apply during deserialization.

.. seealso::

    You can register a custom error handler function for a schema by overriding the :func:`handle_error <Schema.handle_error>` method. See the :doc:`Extending Schemas <extending>` page for more info.

.. seealso::

    Need schema-level validation? See the :ref:`Extending Schemas <schemavalidation>` page.


Field Validators as Methods
+++++++++++++++++++++++++++

It is often convenient to write validators as methods. Use the `validates <marshmallow.decorators.validates>` decorator to register field validator methods.

.. code-block:: python

    from marshmallow import fields, Schema, validates, ValidationError


    class ItemSchema(Schema):
        quantity = fields.Integer()

        @validates("quantity")
        def validate_quantity(self, value):
            if value < 0:
                raise ValidationError("Quantity must be greater than 0.")
            if value > 30:
                raise ValidationError("Quantity must not be greater than 30.")


Required Fields
+++++++++++++++

You can make a field required by passing ``required=True``. An error will be stored if the the value is missing from the input to :meth:`Schema.load`.

To customize the error message for required fields, pass a `dict` with a ``required`` key as the ``error_messages`` argument for the field.

.. code-block:: python

    from marshmallow import ValidationError


    class UserSchema(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True, error_messages={"required": "Age is required."})
        city = fields.String(
            required=True,
            error_messages={"required": {"message": "City required", "code": 400}},
        )
        email = fields.Email()


    try:
        result = UserSchema().load({"email": "foo@bar.com"})
    except ValidationError as err:
        err.messages
    # {'name': ['Missing data for required field.'],
    #  'age': ['Age is required.'],
    #  'city': {'message': 'City required', 'code': 400}}

Partial Loading
+++++++++++++++

When using the same schema in multiple places, you may only want to check required fields some of the time when deserializing by specifying them in ``partial``.

.. code-block:: python
    :emphasize-lines: 5,6

    class UserSchema(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True)


    result = UserSchema().load({"age": 42}, partial=("name",))
    # OR UserSchema(partial=('name',)).load({'age': 42})
    result  # => ({'age': 42}, {})

Or you can ignore missing fields entirely by setting ``partial=True``.

.. code-block:: python
    :emphasize-lines: 5,6

    class UserSchema(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True)


    result = UserSchema().load({"age": 42}, partial=True)
    # OR UserSchema(partial=True).load({'age': 42})
    result  # => ({'age': 42}, {})

.. _unknown:

Handling Unknown Fields
+++++++++++++++++++++++

By default, :meth:`load <Schema.load>` will raise a :exc:`ValidationError <marshmallow.exceptions.ValidationError>` if it encounters a key with no matching ``Field`` in the schema.

This behavior can be modified with the ``unknown`` option, which accepts one of the following:

- `EXCLUDE <marshmallow.utils.EXCLUDE>`: exclude unknown fields
- `INCLUDE <marshmallow.utils.INCLUDE>`: accept and include the unknown fields
- `RAISE <marshmallow.utils.RAISE>`: raise a :exc:`ValidationError <marshmallow.exceptions.ValidationError>`
  if there are any unknown fields

You can specify ``unknown`` in the *class Meta* of your `Schema`,

.. code-block:: python

    from marshmallow import Schema, INCLUDE


    class UserSchema(Schema):
        class Meta:
            unknown = INCLUDE

at instantiation time,

.. code-block:: python

    schema = UserSchema(unknown=INCLUDE)

or pass it to `load <Schema.load>`.

.. code-block:: python

    UserSchema().load(data, unknown=INCLUDE)

The ``unknown`` option value set in :meth:`load <Schema.load>` will always override the value applied at instantiation time, which itself will override the value defined in the *class Meta*.

This order of precedence allows you to change the behavior of a schema for different contexts.


Schema.validate
+++++++++++++++

If you only need to validate input data (without deserializing to an object), you can use :meth:`Schema.validate`.

.. code-block:: python

    errors = UserSchema().validate({"name": "Ronnie", "email": "invalid-email"})
    errors  # {'email': ['"invalid-email" is not a valid email address.']}


Specifying Attribute Names
--------------------------

By default, `Schemas` will marshal the object attributes that are identical to the schema's field names. However, you may want to have different field and attribute names. In this case, you can explicitly specify which attribute names to use.

.. code-block:: python
    :emphasize-lines: 3,4,11,12

    class UserSchema(Schema):
        name = fields.String()
        email_addr = fields.String(attribute="email")
        date_created = fields.DateTime(attribute="created_at")


    user = User("Keith", email="keith@stones.com")
    ser = UserSchema()
    result = ser.dump(user)
    pprint(result)
    # {'name': 'Keith',
    #  'email_addr': 'keith@stones.com',
    #  'date_created': '2014-08-17T14:58:57.600623+00:00'}


Specifying Serialization/Deserialization Keys
---------------------------------------------

By default `Schemas` will marshal/unmarshal an input dictionary from/to an output dictionary whose keys are identical to the field names.  However, if you are producing/consuming data that does not exactly match your schema, you can specify additional keys to dump/load values by passing the `data_key` argument.

.. code-block:: python
    :emphasize-lines: 3,9,13,17,21

    class UserSchema(Schema):
        name = fields.String()
        email = fields.Email(data_key="emailAddress")


    s = UserSchema()

    data = {"name": "Mike", "email": "foo@bar.com"}
    result = s.dump(data)
    # {'name': u'Mike',
    # 'emailAddress': 'foo@bar.com'}

    data = {"name": "Mike", "emailAddress": "foo@bar.com"}
    result = s.load(data)
    # {'name': u'Mike',
    # 'email': 'foo@bar.com'}

.. _meta_options:

Refactoring: Implicit Field Creation
------------------------------------

When your model has many attributes, specifying the field type for every attribute can get repetitive, especially when many of the attributes are already native Python datatypes.

The *class Meta* paradigm allows you to specify which attributes you want to serialize. Marshmallow will choose an appropriate field type based on the attribute's type.

Let's refactor our User schema to be more concise.

.. code-block:: python
    :emphasize-lines: 4,5

    # Refactored schema
    class UserSchema(Schema):
        uppername = fields.Function(lambda obj: obj.name.upper())

        class Meta:
            fields = ("name", "email", "created_at", "uppername")

Note that ``name`` will be automatically formatted as a :class:`String <marshmallow.fields.String>` and ``created_at`` will be formatted as a :class:`DateTime <marshmallow.fields.DateTime>`.

.. note::

    If instead you want to specify which field names to include *in addition* to the explicitly declared fields, you can use the ``additional`` option.

    The schema below is equivalent to above:

    .. code-block:: python

        class UserSchema(Schema):
            uppername = fields.Function(lambda obj: obj.name.upper())

            class Meta:
                # No need to include 'uppername'
                additional = ("name", "email", "created_at")

Ordering Output
---------------

For some use cases, it may be useful to maintain field ordering of serialized output. To enable ordering, set the ``ordered`` option to `True`. This will instruct marshmallow to serialize data to a `collections.OrderedDict`.

.. code-block:: python
    :emphasize-lines: 7

    from collections import OrderedDict


    class UserSchema(Schema):
        uppername = fields.Function(lambda obj: obj.name.upper())

        class Meta:
            fields = ("name", "email", "created_at", "uppername")
            ordered = True


    u = User("Charlie", "charlie@stones.com")
    schema = UserSchema()
    result = schema.dump(u)
    assert isinstance(result, OrderedDict)
    # marshmallow's pprint function maintains order
    pprint(result, indent=2)
    # {
    #   "name": "Charlie",
    #   "email": "charlie@stones.com",
    #   "created_at": "2014-10-30T08:27:48.515735+00:00",
    #   "uppername": "CHARLIE"
    # }


"Read-only" and "Write-only" Fields
-----------------------------------

In the context of a web API, the ``dump_only`` and ``load_only`` parameters are conceptually equivalent to "read-only" and "write-only" fields, respectively.

.. code-block:: python

    class UserSchema(Schema):
        name = fields.Str()
        # password is "write-only"
        password = fields.Str(load_only=True)
        # created_at is "read-only"
        created_at = fields.DateTime(dump_only=True)

.. warning::

    When loading, dump_only fields are considered unknown. If the ``unknown`` option is set to ``INCLUDE``, values with keys corresponding to those fields are therefore loaded with no validation.


Specify Default Serialization/Deserialization Values
----------------------------------------------------

Default values can be provided to a :class:`Field <fields.Field>` for both serialization and deserialization.

`missing` is used for deserialization if the field is not found in the input data. Likewise, `default` is used for serialization if the input value is missing.

.. code-block:: python

    class UserSchema(Schema):
        id = fields.UUID(missing=uuid.uuid1)
        birthdate = fields.DateTime(default=dt.datetime(2017, 9, 29))


    UserSchema().load({})
    # {'id': UUID('337d946c-32cd-11e8-b475-0022192ed31b')}
    UserSchema().dump({})
    # {'birthdate': '2017-09-29T00:00:00+00:00'}


Next Steps
----------

- Need to represent relationships between objects? See the :doc:`Nesting Schemas <nesting>` page.
- Want to create your own field type? See the :doc:`Custom Fields <custom_fields>` page.
- Need to add schema-level validation, post-processing, or error handling behavior? See the :doc:`Extending Schemas <extending>` page.
- For example applications using marshmallow, check out the :doc:`Examples <examples>` page.
