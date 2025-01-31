Pre-processing and post-processing methods
==========================================

Decorator API
-------------

Data pre-processing and post-processing methods can be registered using the `pre_load <marshmallow.decorators.pre_load>`, `post_load <marshmallow.decorators.post_load>`, `pre_dump <marshmallow.decorators.pre_dump>`, and `post_dump <marshmallow.decorators.post_dump>` decorators.


.. code-block:: python

    from marshmallow import Schema, fields, post_load


    class UserSchema(Schema):
        name = fields.Str()
        slug = fields.Str()

        @post_load
        def slugify_name(self, in_data, **kwargs):
            in_data["slug"] = in_data["slug"].lower().strip().replace(" ", "-")
            return in_data


    schema = UserSchema()
    result = schema.load({"name": "Steve", "slug": "Steve Loria "})
    result["slug"]  # => 'steve-loria'

Passing "many"
--------------

By default, pre- and post-processing methods receive one object/datum at a time, transparently handling the ``many`` parameter passed to the ``Schema``'s `~marshmallow.Schema.dump`/`~marshmallow.Schema.load` method at runtime.

In cases where your pre- and post-processing methods needs to handle the input collection when processing multiple objects, add ``pass_many=True`` to the method decorators.

Your method will then receive the input data (which may be a single datum or a collection, depending on the dump/load call).

.. _enveloping_1:

Example: Enveloping
-------------------

One common use case is to wrap data in a namespace upon serialization and unwrap the data during deserialization.

.. code-block:: python

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

Raising errors in pre-/post-processor methods
---------------------------------------------

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

Pre-/post-processor invocation order
------------------------------------

In summary, the processing pipeline for deserialization is as follows:

1. ``@pre_load(pass_many=True)`` methods
2. ``@pre_load(pass_many=False)`` methods
3. ``load(in_data, many)`` (validation and deserialization)
4. ``@validates`` methods (field validators)
5. ``@validates_schema`` methods (schema validators)
6. ``@post_load(pass_many=True)`` methods
7. ``@post_load(pass_many=False)`` methods

The pipeline for serialization is similar, except that the ``pass_many=True`` processors are invoked *after* the ``pass_many=False`` processors and there are no validators.

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
            field_a = fields.Raw()

            @pre_load
            def preprocess(self, data, **kwargs):
                step1_data = self.step1(data)
                step2_data = self.step2(step1_data)
                return step2_data

            def step1(self, data): ...

            # Depends on step1
            def step2(self, data): ...


        # NO
        class MySchema(Schema):
            field_a = fields.Raw()

            @pre_load
            def step1(self, data, **kwargs): ...

            # Depends on step1
            @pre_load
            def step2(self, data, **kwargs): ...
