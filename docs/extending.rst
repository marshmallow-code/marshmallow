.. _extending:
.. module:: marshmallow

Extending Schemas
=================

Handling Errors
---------------

By default, :meth:`Schema.dump` and :meth:`Schema.load` will return validation errors as a dictionary (unless ``strict`` mode is enabled).

You can register a custom error-handling function for a :class:`Schema` using the :meth:`Schema.error_handler` decorator. The function receives the schema instance, the errors dictionary, and the original object to be serialized.


.. code-block:: python

    import logging
    from marshmallow import Schema, fields

    class AppError(Exception):
        pass

    class UserSchema(Schema):
        email = fields.Email()

    # Log and raise our custom exception when serialization
    # or deserialization fails
    @UserSchema.error_handler
    def handle_errors(schema, errors, obj):
        logging.error(errors)
        raise AppError('An error occurred while serializing {0}'.format(obj))

    invalid = User('Foo Bar', email='invalid-email')
    schema = UserSchema()
    schema.dump(invalid)  # raises AppError
    schema.load({'email': 'invalid-email'})  # raises AppError

.. _schemavalidation:

Schema-level Validation
-----------------------

You can register schema-level validation functions for a :class:`Schema` using the :meth:`Schema.validator` decorator. The function receives the schema instance and the input data
as arguments. Schema-level validation errors will be stored on the ``_schema`` key of the errors dictonary.

.. code-block:: python

    from marshmallow import Schema, fields, ValidationError

    class NumberSchema(Schema):
        field_a = fields.Integer()
        field_b = fields.Integer()

    @NumberSchema.validator
    def validate_numbers(schema, input_data):
        if input_data['field_b'] >= input_data['field_a']:
            raise ValidationError('field_a must be greater than field_b')

    schema = NumberSchema()
    result, errors = schema.load({'field_a': 2, 'field_b': 1})
    errors['_schema'] # => ["field_a must be greater than field_b"]


Storing Errors on Specific Fields
+++++++++++++++++++++++++++++++++

If you want to store schema-level validation errors on a specific field, you can pass a field name to the :exc:`ValidationError`.

.. code-block:: python

    @NumberSchema.validator
    def validate_numbers(schema, input_data):
        if input_data['field_b'] >= input_data['field_a']:
            # Store error on field_a
            raise ValidationError('field_a must be greater than field_b', 'field_a')

    schema = NumberSchema()
    result, errors = schema.load({'field_a': 2, 'field_b': 1})
    errors['field_a'] # => ["field_a must be greater than field_b"]

Pre-processing Input Data
-------------------------

Data pre-processing functions can be registered using :meth:`Schema.preprocessor`. A pre-processing function receives the schema instace and the input data as arguments and must return the dictionary of processed data.


.. code-block:: python

    from marshmallow import Schema, fields

    class UserSchema(Schema):
        name = fields.String()
        slug = fields.String()

    @UserSchema.preprocessor
    def slugify_name(schema, in_data):
        in_data['slug'] = in_data['slug'].lower().strip().replace(' ', '-')
        return in_data

    schema = UserSchema()
    result, errors = schema.load({'name': 'Steve', 'slug': 'Steve Loria '})
    result['slug']  # => 'steve-loria'


Transforming Data
-----------------

The :meth:`Schema.data_handler` decorator can be used to register data post-processing functions for transforming serialized data. The function receives the serializer instance, the serialized data dictionary, and the original object to be serialized. It should return the transformed data.

One use case might be to add a "root" namespace for a serialized object.

.. code-block:: python

    from marshmallow import Schema, fields

    class UserSchema(Schema):
        NAME = 'user'
        name = fields.String()
        email = fields.Email()

    @UserSchema.data_handler
    def add_root(serializer, data, obj):
        return {
            serializer.NAME: data
        }

    user = User('Monty Python', email='monty@python.org')
    UserSchema().dump(user).data
    # {
    #     'user': {
    #         'name': 'Monty Python',
    #         'email': 'monty@python.org'
    #     }
    # }

.. note::

    It is possible to register multiple data handlers for a single serializer.


Overriding how attributes are accessed
--------------------------------------

By default, marshmallow uses the `utils.get_value` function to pull attributes from various types of objects for serialization. This will work for *most* use cases.

However, if you want to specify how values are accessed from an object, you can use the :meth:`Schema.accessor` decorator.

.. code-block:: python

    class UserDictSchema(Schema):
        name = fields.Str()
        email = fields.Email()

    # If we know we're only serializing dictionaries, we can
    # override the accessor function
    @UserDictSchema.accessor
    def get_from_dict(schema, key, obj, default=None):
        return obj.get(key, default)


Handler Functions as Class Members
----------------------------------

You can register error handlers, validators, and data handlers as optional class members. This might be useful for defining an abstract `Schema` class.

.. code-block:: python

    class BaseSchema(Schema):
        __error_handler__ = handle_errors  # A function
        __data_handlers__ = [add_root]      # List of functions
        __validators__ = [validate_schema]  # List of functions
        __preprocessors__ = [preprocess_data]  # List of functions
        __accessor__ = get_from_dict  # A function


Extending "class Meta" Options
--------------------------------

``class Meta`` options are a way to configure and modify a :class:`Schema's <Schema>` behavior. See the :class:`API docs <Schema>` for a listing of available options.

You can add custom ``class Meta`` options by subclassing :class:`SchemaOpts`.

Example: Adding a Namespace to Serialized Output
++++++++++++++++++++++++++++++++++++++++++++++++

Let's build upon the example above for adding a root namespace to serialized output. This time, we will create a custom base serializer with additional ``class Meta`` options.

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
        "plural_name" options for namespacing.
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

        def _postprocess(self, data, many, obj):
            """Execute any postprocessing steps, including adding a namespace to the final
            output.
            """
            data = Schema._postprocess(self, data, many, obj)
            if self.opts.name:   # Add namespace
                namespace = self.opts.name
                if many:
                    namespace = self.opts.plural_name
                data = {namespace: data}
            return data


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

