.. module:: marshmallow

Extending Schemas
=================

Pre-processing and Post-processing Methods
------------------------------------------

Data pre-processing and post-processing methods can be registered using the `pre_load <marshmallow.decorators.pre_load>`, `post_load <marshmallow.decorators.post_load>`, `pre_dump <marshmallow.decorators.pre_dump>`, and `post_dump <marshmallow.decorators.post_dump>` decorators.


.. code-block:: python
    :emphasize-lines: 7

    from marshmallow import Schema, fields, pre_load


    class UserSchema(Schema):
        name = fields.Str()
        slug = fields.Str()

        @pre_load
        def slugify_name(self, in_data, **kwargs):
            in_data["slug"] = in_data["slug"].lower().strip().replace(" ", "-")
            return in_data


    schema = UserSchema()
    result = schema.load({"name": "Steve", "slug": "Steve Loria "})
    result["slug"]  # => 'steve-loria'


Passing "many"
++++++++++++++

By default, pre- and post-processing methods receive one object/datum at a time, transparently handling the ``many`` parameter passed to the schema at runtime.

In cases where your pre- and post-processing methods need to receive the input collection  when ``many=True``, add ``pass_many=True`` to the method decorators. The method will receive the input data (which may be a single datum or a collection) and the boolean value of ``many``.


Example: Enveloping
+++++++++++++++++++

One common use case is to wrap data in a namespace upon serialization and unwrap the data during deserialization.

.. code-block:: python
    :emphasize-lines: 17,18,22,23,27,28

    from marshmallow import Schema, fields, pre_load, post_load, post_dump


    class BaseSchema(Schema):
        # Custom options
        __envelope__ = {"single": None, "many": None}
        __model__ = User

        def get_envelope_key(self, many):
            """Helper to get the envelope key."""
            key = self.__envelope__["many"] if many else self.__envelope__["single"]
            assert key is not None, "Envelope key undefined"
            return key

        @pre_load(pass_many=True)
        def unwrap_envelope(self, data, many, **kwargs):
            key = self.get_envelope_key(many)
            return data[key]

        @post_dump(pass_many=True)
        def wrap_with_envelope(self, data, many, **kwargs):
            key = self.get_envelope_key(many)
            return {key: data}

        @post_load
        def make_object(self, data, **kwargs):
            return self.__model__(**data)


    class UserSchema(BaseSchema):
        __envelope__ = {"single": "user", "many": "users"}
        __model__ = User
        name = fields.Str()
        email = fields.Email()


    user_schema = UserSchema()

    user = User("Mick", email="mick@stones.org")
    user_data = user_schema.dump(user)
    # {'user': {'email': 'mick@stones.org', 'name': 'Mick'}}

    users = [
        User("Keith", email="keith@stones.org"),
        User("Charlie", email="charlie@stones.org"),
    ]
    users_data = user_schema.dump(users, many=True)
    # {'users': [{'email': 'keith@stones.org', 'name': 'Keith'},
    #            {'email': 'charlie@stones.org', 'name': 'Charlie'}]}

    user_objs = user_schema.load(users_data, many=True)
    # [<User(name='Keith Richards')>, <User(name='Charlie Watts')>]


Raising Errors in Pre-/Post-processor Methods
+++++++++++++++++++++++++++++++++++++++++++++

Pre- and post-processing methods may raise a `ValidationError <marshmallow.exceptions.ValidationError>`. By default, errors will be stored on the ``"_schema"`` key in the errors dictionary.

.. code-block:: python

    from marshmallow import Schema, fields, ValidationError, pre_load


    class BandSchema(Schema):
        name = fields.Str()

        @pre_load
        def unwrap_envelope(self, data, **kwargs):
            if "data" not in data:
                raise ValidationError('Input data must have a "data" key.')
            return data["data"]


    sch = BandSchema()
    try:
        sch.load({"name": "The Band"})
    except ValidationError as err:
        err.messages
    # {'_schema': ['Input data must have a "data" key.']}

If you want to store and error on a different key, pass the key name as the second argument to `ValidationError <marshmallow.exceptions.ValidationError>`.

.. code-block:: python
    :emphasize-lines: 9

    from marshmallow import Schema, fields, ValidationError, pre_load


    class BandSchema(Schema):
        name = fields.Str()

        @pre_load
        def unwrap_envelope(self, data, **kwargs):
            if "data" not in data:
                raise ValidationError(
                    'Input data must have a "data" key.', "_preprocessing"
                )
            return data["data"]


    sch = BandSchema()
    try:
        sch.load({"name": "The Band"})
    except ValidationError as err:
        err.messages
    # {'_preprocessing': ['Input data must have a "data" key.']}


Pre-/Post-processor Invocation Order
++++++++++++++++++++++++++++++++++++

In summary, the processing pipeline for deserialization is as follows:

1. ``@pre_load(pass_many=True)`` methods
2. ``@pre_load(pass_many=False)`` methods
3. ``load(in_data, many)`` (validation and deserialization)
4. ``@post_load(pass_many=True)`` methods
5. ``@post_load(pass_many=False)`` methods

The pipeline for serialization is similar, except that the "pass_many" processors are invoked *after* the "non-raw" processors.

1. ``@pre_dump(pass_many=False)`` methods
2. ``@pre_dump(pass_many=True)`` methods
3. ``dump(obj, many)`` (serialization)
4. ``@post_dump(pass_many=False)`` methods
5. ``@post_dump(pass_many=True)`` methods


.. warning::

    You may register multiple processor methods on a Schema. Keep in mind, however, that **the invocation order of decorated methods of the same type is not guaranteed**. If you need to guarantee order of processing steps, you should put them in the same method.


    .. code-block:: python

        from marshmallow import Schema, fields, pre_load

        # YES
        class MySchema(Schema):
            field_a = fields.Field()

            @pre_load
            def preprocess(self, data, **kwargs):
                step1_data = self.step1(data)
                step2_data = self.step2(step1_data)
                return step2_data

            def step1(self, data):
                do_step1(data)

            # Depends on step1
            def step2(self, data):
                do_step2(data)


        # NO
        class MySchema(Schema):
            field_a = fields.Field()

            @pre_load
            def step1(self, data, **kwargs):
                do_step1(data)

            # Depends on step1
            @pre_load
            def step2(self, data, **kwargs):
                do_step2(data)


Handling Errors
---------------

By default, :meth:`Schema.dump` and :meth:`Schema.load` will raise a :exc:`ValidationError <marshmallow.exceptions.ValidationError>`.

You can specify a custom error-handling function for a :class:`Schema` by overriding the `handle_error <marshmallow.Schema.handle_error>`  method. The method receives the :exc:`ValidationError <marshmallow.exceptions.ValidationError>` and the original object (or input data if deserializing) to be (de)serialized.

.. code-block:: python
    :emphasize-lines: 10-13

    import logging
    from marshmallow import Schema, fields


    class AppError(Exception):
        pass


    class UserSchema(Schema):
        email = fields.Email()

        def handle_error(self, exc, data):
            """Log and raise our custom exception when (de)serialization fails."""
            logging.error(exc.messages)
            raise AppError("An error occurred with input: {0}".format(data))


    schema = UserSchema()
    schema.load({"email": "invalid-email"})  # raises AppError

.. _schemavalidation:

Schema-level Validation
-----------------------

You can register schema-level validation functions for a :class:`Schema` using the `marshmallow.validates_schema <marshmallow.decorators.validates_schema>` decorator. By default, schema-level validation errors will be stored on the ``_schema`` key of the errors dictonary.

.. code-block:: python
    :emphasize-lines: 7

    from marshmallow import Schema, fields, validates_schema, ValidationError


    class NumberSchema(Schema):
        field_a = fields.Integer()
        field_b = fields.Integer()

        @validates_schema
        def validate_numbers(self, data, **kwargs):
            if data["field_b"] >= data["field_a"]:
                raise ValidationError("field_a must be greater than field_b")


    schema = NumberSchema()
    try:
        schema.load({"field_a": 1, "field_b": 2})
    except ValidationError as err:
        err.messages["_schema"]
    # => ["field_a must be greater than field_b"]

Storing Errors on Specific Fields
+++++++++++++++++++++++++++++++++

It is possible to report errors on fields and subfields using a `dict`.

When multiple schema-leval validator return errors, the error structures are merged together in the :exc:`ValidationError <marshmallow.exceptions.ValidationError>` raised at the end of the validation.

.. code-block:: python
    :emphasize-lines: 17,27

    from marshmallow import Schema, fields, validates_schema, ValidationError


    class NumberSchema(Schema):
        field_a = fields.Integer()
        field_b = fields.Integer()
        field_c = fields.Integer()
        field_d = fields.Integer()

        @validates_schema
        def validate_lower_bound(self, data, **kwargs):
            errors = {}
            if data["field_b"] <= data["field_a"]:
                errors["field_b"] = ["field_b must be greater than field_a"]
            if data["field_c"] <= data["field_a"]:
                errors["field_c"] = ["field_c must be greater than field_a"]
            if errors:
                raise ValidationError(errors)

        @validates_schema
        def validate_upper_bound(self, data, **kwargs):
            errors = {}
            if data["field_b"] >= data["field_d"]:
                errors["field_b"] = ["field_b must be lower than field_d"]
            if data["field_c"] >= data["field_d"]:
                errors["field_c"] = ["field_c must be lower than field_d"]
            if errors:
                raise ValidationError(errors)


    schema = NumberSchema()
    try:
        schema.load({"field_a": 3, "field_b": 2, "field_c": 1, "field_d": 0})
    except ValidationError as err:
        err.messages
    # => {
    #     'field_b': [
    #         'field_b must be greater than field_a',
    #         'field_b must be lower than field_d'
    #     ],
    #     'field_c': [
    #         'field_c must be greater than field_a',
    #         'field_c must be lower than field_d'
    #     ]
    #    }


Using Original Input Data
-------------------------

If you want to use the original, unprocessed input, you can add ``pass_original=True`` to
`post_load <marshmallow.decorators.post_load>` or `validates_schema <marshmallow.decorators.validates_schema>`.

.. code-block:: python
    :emphasize-lines: 7

    from marshmallow import Schema, fields, post_load, ValidationError


    class MySchema(Schema):
        foo = fields.Int()
        bar = fields.Int()

        @post_load(pass_original=True)
        def add_baz_to_bar(self, data, original_data, **kwargs):
            baz = original_data.get("baz")
            if baz:
                data["bar"] = data["bar"] + baz
            return data


    schema = MySchema()
    schema.load({"foo": 1, "bar": 2, "baz": 3})
    # {'foo': 1, 'bar': 5}

.. seealso::

   The default behavior for unspecified fields can be controlled with the ``unknown`` option, see :ref:`Handling Unknown Fields <unknown>` for more information.

Overriding How Attributes Are Accessed
--------------------------------------

By default, marshmallow uses the `utils.get_value` function to pull attributes from various types of objects for serialization. This will work for *most* use cases.

However, if you want to specify how values are accessed from an object, you can override the :meth:`get_attribute <marshmallow.Schema.get_attribute>` method.

.. code-block:: python
    :emphasize-lines: 7-8

    class UserDictSchema(Schema):
        name = fields.Str()
        email = fields.Email()

        # If we know we're only serializing dictionaries, we can
        # use dict.get for all input objects
        def get_attribute(self, obj, key, default):
            return obj.get(key, default)

Custom "class Meta" Options
---------------------------

``class Meta`` options are a way to configure and modify a :class:`Schema's <Schema>` behavior. See the :class:`API docs <Schema.Meta>` for a listing of available options.

You can add custom ``class Meta`` options by subclassing :class:`SchemaOpts`.

Example: Enveloping, Revisited
++++++++++++++++++++++++++++++

Let's build upon the example above for adding an envelope to serialized output. This time, we will allow the envelope key to be customizable with ``class Meta`` options.

::

    # Example outputs
    {
        'user': {
            'name': 'Keith',
            'email': 'keith@stones.com'
        }
    }
    # List output
    {
        'users': [{'name': 'Keith'}, {'name': 'Mick'}]
    }


First, we'll add our namespace configuration to a custom options class.

.. code-block:: python
    :emphasize-lines: 3

    from marshmallow import Schema, SchemaOpts


    class NamespaceOpts(SchemaOpts):
        """Same as the default class Meta options, but adds "name" and
        "plural_name" options for enveloping.
        """

        def __init__(self, meta, **kwargs):
            SchemaOpts.__init__(self, meta, **kwargs)
            self.name = getattr(meta, "name", None)
            self.plural_name = getattr(meta, "plural_name", self.name)


Then we create a custom :class:`Schema` that uses our options class.

.. code-block:: python
    :emphasize-lines: 1,2

    class NamespacedSchema(Schema):
        OPTIONS_CLASS = NamespaceOpts

        @pre_load(pass_many=True)
        def unwrap_envelope(self, data, many, **kwargs):
            key = self.opts.plural_name if many else self.opts.name
            return data[key]

        @post_dump(pass_many=True)
        def wrap_with_envelope(self, data, many, **kwargs):
            key = self.opts.plural_name if many else self.opts.name
            return {key: data}


Our application schemas can now inherit from our custom schema class.

.. code-block:: python
    :emphasize-lines: 1,6,7

    class UserSchema(NamespacedSchema):
        name = fields.String()
        email = fields.Email()

        class Meta:
            name = "user"
            plural_name = "users"


    ser = UserSchema()
    user = User("Keith", email="keith@stones.com")
    result = ser.dump(user)
    result  # {"user": {"name": "Keith", "email": "keith@stones.com"}}

Using Context
-------------

The ``context`` attribute of a `Schema` is a general-purpose store for extra information that may be needed for (de)serialization. It may be used in both ``Schema`` and ``Field`` methods.

.. code-block:: python

    schema = UserSchema()
    # Make current HTTP request available to
    # custom fields, schema methods, schema validators, etc.
    schema.context["request"] = request
    schema.dump(user)

Custom Error Messages
---------------------

You can customize the error messages that `dump <marshmallow.Schema.dump>` and `dumps <marshmallow.Schema.dumps>` uses when raising a `ValidationError <marshmallow.exceptions.ValidationError>`.
You do this by overriding the ``error_messages`` class variable:

.. code-block:: python

    class MySchema(Schema):
        error_messages = {
            "unknown": "Custom unknown field error message.",
            "type": "Custom invalid type error message.",
        }
