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
        def slugify_name(self, in_data):
            in_data['slug'] = in_data['slug'].lower().strip().replace(' ', '-')
            return in_data

    schema = UserSchema()
    result, errors = schema.load({'name': 'Steve', 'slug': 'Steve Loria '})
    result['slug']  # => 'steve-loria'


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
        __envelope__ = {
            'single': None,
            'many': None
        }
        __model__ = User

        def get_envelope_key(self, many):
            """Helper to get the envelope key."""
            key = self.__envelope__['many'] if many else self.__envelope__['single']
            assert key is not None, "Envelope key undefined"
            return key

        @pre_load(pass_many=True)
        def unwrap_envelope(self, data, many):
            key = self.get_envelope_key(many)
            return data[key]

        @post_dump(pass_many=True)
        def wrap_with_envelope(self, data, many):
            key = self.get_envelope_key(many)
            return {key: data}

        @post_load
        def make_object(self, data):
            return self.__model__(**data)

    class UserSchema(BaseSchema):
        __envelope__ = {
            'single': 'user',
            'many': 'users',
        }
        __model__ = User
        name = fields.Str()
        email = fields.Email()

    user_schema = UserSchema()

    user = User('Mick', email='mick@stones.org')
    user_data = user_schema.dump(user).data
    # {'user': {'email': 'mick@stones.org', 'name': 'Mick'}}

    users = [User('Keith', email='keith@stones.org'),
            User('Charlie', email='charlie@stones.org')]
    users_data = user_schema.dump(users, many=True).data
    # {'users': [{'email': 'keith@stones.org', 'name': 'Keith'},
    #            {'email': 'charlie@stones.org', 'name': 'Charlie'}]}

    user_objs = user_schema.load(users_data, many=True).data
    # [<User(name='Keith Richards')>, <User(name='Charlie Watts')>]


Raising Errors in Pre-/Post-processor Methods
+++++++++++++++++++++++++++++++++++++++++++++

Pre- and post-processing methods may raise a `ValidationError <marshmallow.exceptions.ValidationError>`. By default, errors will be stored on the ``"_schema"`` key in the errors dictionary.

.. code-block:: python

    from marshmallow import Schema, fields, ValidationError, pre_load

    class BandSchema(Schema):
        name = fields.Str()

        @pre_load
        def unwrap_envelope(self, data):
            if 'data' not in data:
                raise ValidationError('Input data must have a "data" key.')
            return data['data']

    sch = BandSchema()
    sch.load({'name': 'The Band'}).errors
    # {'_schema': ['Input data must have a "data" key.']}

If you want to store and error on a different key, pass the key name as the second argument to `ValidationError <marshmallow.exceptions.ValidationError>`.

.. code-block:: python
    :emphasize-lines: 9

    from marshmallow import Schema, fields, ValidationError, pre_load

    class BandSchema(Schema):
        name = fields.Str()

        @pre_load
        def unwrap_envelope(self, data):
            if 'data' not in data:
                raise ValidationError('Input data must have a "data" key.', '_preprocessing')
            return data['data']

    sch = BandSchema()
    sch.load({'name': 'The Band'}).errors
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
            def preprocess(self, data):
                step1_data = self.step1(data)
                step2_data = self.step2(step1_data)
                return step2_data

            def step1(self, data):
                # ...

            # Depends on step1
            def step2(self, data):
                # ...

        # NO
        class MySchema(Schema):
            field_a = fields.Field()

            @pre_load
            def step1(self, data):
                # ...

            # Depends on step1
            @pre_load
            def step2(self, data):
                # ...


Handling Errors
---------------

By default, :meth:`Schema.dump` and :meth:`Schema.load` will return validation errors as a dictionary (unless ``strict`` mode is enabled).

You can specify a custom error-handling function for a :class:`Schema` by overriding the `handle_error <marshmallow.Schema.handle_error>`  method. The method receives the `ValidationError <marshmallow.exceptions.ValidationError>` and the original object (or input data if deserializing) to be (de)serialized.

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
            raise AppError('An error occurred with input: {0}'.format(data))

    schema = UserSchema()
    schema.load({'email': 'invalid-email'})  # raises AppError

.. _schemavalidation:

Schema-level Validation
-----------------------

You can register schema-level validation functions for a :class:`Schema` using the :meth:`marshmallow.validates_schema <marshmallow.decorators.validates_schema>` decorator. Schema-level validation errors will be stored on the ``_schema`` key of the errors dictonary.

.. code-block:: python
    :emphasize-lines: 7

    from marshmallow import Schema, fields, validates_schema, ValidationError

    class NumberSchema(Schema):
        field_a = fields.Integer()
        field_b = fields.Integer()

        @validates_schema
        def validate_numbers(self, data):
            if data['field_b'] >= data['field_a']:
                raise ValidationError('field_a must be greater than field_b')

    schema = NumberSchema()
    result, errors = schema.load({'field_a': 1, 'field_b': 2})
    errors['_schema'] # => ["field_a must be greater than field_b"]


Validating Original Input Data
++++++++++++++++++++++++++++++

Normally, unspecified field names are ignored by the validator. If you would like access to the original, raw input (e.g. to fail validation if an unknown field name is sent), add ``pass_original=True`` to your call to `validates_schema <marshmallow.decorators.validates_schema>`.

.. code-block:: python
    :emphasize-lines: 7

    from marshmallow import Schema, fields, validates_schema, ValidationError

    class MySchema(Schema):
        foo = fields.Int()
        bar = fields.Int()

        @validates_schema(pass_original=True)
        def check_unknown_fields(self, data, original_data):
            unknown = set(original_data) - set(self.fields)
            if unknown:
                raise ValidationError('Unknown field', unknown)

    schema = MySchema()
    errors = schema.load({'foo': 1, 'bar': 2, 'baz': 3, 'bu': 4}).errors
    # {'baz': 'Unknown field', 'bu': 'Unknown field'}


Storing Errors on Specific Fields
+++++++++++++++++++++++++++++++++

If you want to store schema-level validation errors on a specific field, you can pass a field name (or multiple field names) to the :exc:`ValidationError <marshmallow.exceptions.ValidationError>`.

.. code-block:: python
    :emphasize-lines: 10

    class NumberSchema(Schema):
        field_a = fields.Integer()
        field_b = fields.Integer()

        @validates_schema
        def validate_numbers(self, data):
            if data['field_b'] >= data['field_a']:
                raise ValidationError(
                    'field_a must be greater than field_b',
                    'field_a'
                )

    schema = NumberSchema()
    result, errors = schema.load({'field_a': 2, 'field_b': 1})
    errors['field_a'] # => ["field_a must be greater than field_b"]

Overriding how attributes are accessed
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
        def get_attribute(self, key, obj, default):
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
        def __init__(self, meta):
            SchemaOpts.__init__(self, meta)
            self.name = getattr(meta, 'name', None)
            self.plural_name = getattr(meta, 'plural_name', self.name)


Then we create a custom :class:`Schema` that uses our options class.

.. code-block:: python
    :emphasize-lines: 1,2

    class NamespacedSchema(Schema):
        OPTIONS_CLASS = NamespaceOpts

        @pre_load(pass_many=True)
        def unwrap_envelope(self, data, many):
            key = self.opts.plural_name if many else self.opts.name
            return data[key]

        @post_dump(pass_many=True)
        def wrap_with_envelope(self, data, many):
            key = self.opts.plural_name if many else self.opts.name
            return {key: data}


Our application schemas can now inherit from our custom schema class.

.. code-block:: python
    :emphasize-lines: 1,6,7

    class UserSchema(NamespacedSchema):
        name = fields.String()
        email = fields.Email()

        class Meta:
            name = 'user'
            plural_name = 'users'

    ser = UserSchema()
    user = User('Keith', email='keith@stones.com')
    result = ser.dump(user)
    result.data  # {"user": {"name": "Keith", "email": "keith@stones.com"}}

Using Context
-------------

The ``context`` attribute of a `Schema` is a general-purpose store for extra information that may be needed for (de)serialization. It may be used in both ``Schema`` and ``Field`` methods.

.. code-block:: python

    schema = UserSchema()
    # Make current HTTP request available to
    # custom fields, schema methods, schema validators, etc.
    schema.context['request'] = request
    schema.dump(user)
