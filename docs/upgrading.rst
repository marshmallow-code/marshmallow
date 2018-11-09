Upgrading to Newer Releases
===========================

This section documents migration paths to new releases.

Upgrading to 2.3
++++++++++++++++

The ``func`` parameter of `fields.Function <marshmallow.fields.Function>` was renamed to ``serialize``.


.. code-block:: python

    # YES
    lowername = fields.Function(serialize=lambda obj: obj.name.lower())
    # or
    lowername = fields.Function(lambda obj: obj.name.lower())

    # NO
    lowername = fields.Function(func=lambda obj: obj.name.lower())

Similiarly, the ``method_name`` of `fields.Method <marshmallow.fields.Method>` was also renamed to ``serialize``.

.. code-block:: python

    # YES
    lowername = fields.Method(serialize='lowercase')
    # or
    lowername = fields.Method('lowercase')

    # NO
    lowername = fields.Method(method_name='lowercase')

The ``func`` parameter is still available for backwards-compatibility. It will be removed in marshmallow 3.0.

Both `fields.Function <marshmallow.fields.Function>` and `fields.Method <marshmallow.fields.Method>` will allow the serialize parameter to not be passed, in this case use the ``deserialize`` parameter by name.

.. code-block:: python

    lowername = fields.Function(deserialize=lambda name: name.lower())
    # or
    lowername = fields.Method(deserialize='lowername')

Upgrading to 2.0
++++++++++++++++

Deserializing `None`
********************

In 2.0, validation/deserialization of `None` is consistent across field types. If ``allow_none`` is `False` (the default), validation fails when the field's value is `None`. If ``allow_none`` is `True`, `None` is considered valid, and the field deserializes to `None`.


.. code-block:: python

    from marshmallow import fields

    # In 1.0, deserialization of None was inconsistent
    fields.Int().deserialize(None)  # 0
    fields.Str().deserialize(None)  # ''
    fields.DateTime().deserialize(None)  # error: Could not deserialize None to a datetime.


    # In 2.0, validation/deserialization of None is consistent
    fields.Int().deserialize(None)  # error: Field may not be null.
    fields.Str().deserialize(None)  # error: Field may not be null.
    fields.DateTime().deserialize(None)  # error: Field may not be null.

    # allow_none makes None a valid value
    fields.Int(allow_none=True).deserialize(None)  # None

Default Values
**************

Before version 2.0, certain fields (including `String <marshmallow.fields.String>`, `List <marshmallow.fields.List>`, `Nested <marshmallow.fields.Nested>`, and number fields) had implicit default values that would be used if their corresponding input value was `None` or missing.


In 2.0, these implicit defaults are removed.  A `Field's <marshmallow.fields.Field>` ``default`` parameter is only used if you explicitly set it. Otherwise, missing inputs will be excluded from the serialized output.

.. code-block:: python

    from marshmallow import Schema, fields

    class MySchema(Schema):
        str_no_default = fields.Str()
        int_no_default = fields.Int()
        list_no_default = fields.List(fields.Str)

    schema = MySchema()

    # In 1.0, None was treated as a missing input, so implicit default values were used
    schema.dump({'str_no_default': None,
                'int_no_default': None,
                'list_no_default': None}).data
    # {'str_no_default': '', 'int_no_default': 0, 'list_no_default': []}

    # In 2.0, None serializes to None. No more implicit defaults.
    schema.dump({'str_no_default': None,
                'int_no_default': None,
                'list_no_default': None}).data
    # {'str_no_default': None, 'int_no_default': None, 'list_no_default': None}


.. code-block:: python

    # In 1.0, implicit default values were used for missing inputs
    schema.dump({}).data
    # {'int_no_default': 0, 'str_no_default': '', 'list_no_default': []}

    # In 2.0, missing inputs are excluded from the serialized output
    # if no defaults are specified
    schema.dump({}).data
    # {}


As a consequence of this new behavior, the ``skip_missing`` class Meta option has been removed.


Pre-processing and Post-processing Methods
******************************************

The pre- and post-processing API was significantly improved for better consistency and flexibility. The `pre_load <marshmallow.decorators.pre_load>`, `post_load <marshmallow.decorators.post_load>`, `pre_dump <marshmallow.decorators.pre_dump>`, and `post_dump <marshmallow.decorators.post_dump>` should be used to define processing hooks. `Schema.preprocessor` and `Schema.data_handler` are removed.


.. code-block:: python

    # 1.0 API
    from marshmallow import Schema, fields

    class ExampleSchema(Schema):
        field_a = fields.Int()

    @ExampleSchema.preprocessor
    def increment(schema, data):
        data['field_a'] += 1
        return data

    @ExampleSchema.data_handler
    def decrement(schema, data, obj):
        data['field_a'] -= 1
        return data


    # 2.0 API
    from marshmallow import Schema, fields, pre_load, post_dump

    class ExampleSchema(Schema):
        field_a = fields.Int()

        @pre_load
        def increment(self, data):
            data['field_a'] += 1
            return data

        @post_dump
        def decrement(self, data):
            data['field_a'] -= 1
            return data

See the :doc:`Extending Schemas <extending>` page for more information on the ``pre_*`` and ``post_*`` decorators.

Schema Validators
*****************

Similar to pre-processing and post-processing methods, schema validators are now defined as methods. Decorate schema validators with `validates_schema <marshmallow.decorators.validates_schema>`. `Schema.validator` is removed.

.. code-block:: python

    # 1.0 API
    from marshmallow import Schema, fields, ValidationError

    class MySchema(Schema):
        field_a = fields.Int(required=True)
        field_b = fields.Int(required=True)

    @ExampleSchema.validator
    def validate_schema(schema, data):
        if data['field_a'] < data['field_b']:
            raise ValidationError('field_a must be greater than field_b')

    # 2.0 API
    from marshmallow import Schema, fields, validates_schema, ValidationError

    class MySchema(Schema):
        field_a = fields.Int(required=True)
        field_b = fields.Int(required=True)

        @validates_schema
        def validate_schema(self, data):
            if data['field_a'] < data['field_b']:
                raise ValidationError('field_a must be greater than field_b')

Custom Accessors and Error Handlers
***********************************

Custom accessors and error handlers are now defined as methods. `Schema.accessor` and `Schema.error_handler` are deprecated.

.. code-block:: python

    from marshmallow import Schema, fields

    # 1.0 Deprecated API
    class ExampleSchema(Schema):
        field_a = fields.Int()

    @ExampleSchema.accessor
    def get_from_dict(schema, attr, obj, default=None):
        return obj.get(attr, default)

    @ExampleSchema.error_handler
    def handle_errors(schema, errors, obj):
        raise CustomError('Something bad happened', messages=errors)

    # 2.0 API
    class ExampleSchema(Schema):
        field_a = fields.Int()

        def get_attribute(self, attr, obj, default):
            return obj.get(attr, default)

        # handle_error gets passed a ValidationError
        def handle_error(self, exc, data):
            raise CustomError('Something bad happened', messages=exc.messages)

Use `post_load <marshmallow.decorators.post_load>` instead of `make_object`
***************************************************************************

The `make_object` method was deprecated from the `Schema <marshmallow.Schema>` API (see :issue:`277` for the rationale). In order to deserialize to an object, use a `post_load <marshmallow.decorators.post_load>` method.

.. code-block:: python

    # 1.0
    from marshmallow import Schema, fields, post_load

    class UserSchema(Schema):
        name = fields.Str()
        created_at = fields.DateTime()

        def make_object(self, data):
            return User(**data)

    # 2.0
    from marshmallow import Schema, fields, post_load

    class UserSchema(Schema):
        name = fields.Str()
        created_at = fields.DateTime()

        @post_load
        def make_user(self, data):
            return User(**data)

Error Format when ``many=True``
*******************************

When validating a collection (i.e. when calling ``load`` or ``dump`` with ``many=True``), the errors dictionary will be keyed on the indices of invalid items.

.. code-block:: python

    from marshmallow import Schema, fields

    class BandMemberSchema(Schema):
        name = fields.String(required=True)
        email = fields.Email()

    user_data = [
        {'email': 'mick@stones.com', 'name': 'Mick'},
        {'email': 'invalid', 'name': 'Invalid'},  # invalid email
        {'email': 'keith@stones.com', 'name': 'Keith'},
        {'email': 'charlie@stones.com'},  # missing "name"
    ]

    result = BandMemberSchema(many=True).load(user_data)

    # 1.0
    result.errors
    # {'email': ['"invalid" is not a valid email address.'],
    #  'name': ['Missing data for required field.']}

    # 2.0
    result.errors
    # {1: {'email': ['"invalid" is not a valid email address.']},
    #  3: {'name': ['Missing data for required field.']}}

You can still get the pre-2.0 behavior by setting ``index_errors = False`` in a ``Schema's`` *class Meta* options.

Use ``ValidationError`` instead of ``MarshallingError`` and ``UnmarshallingError``
**********************************************************************************

The :exc:`MarshallingError` and :exc:`UnmarshallingError` exceptions are deprecated in favor of a single :exc:`ValidationError <marshmallow.exceptions.ValidationError>`. Users who have written custom fields or are using ``strict`` mode will need to change their code accordingly.

Handle ``ValidationError`` in strict mode
-----------------------------------------

When using `strict` mode, you should handle `ValidationErrors` when calling `Schema.dump` and `Schema.load`.

.. code-block:: python
    :emphasize-lines: 3,14

    from marshmallow import exceptions as exc

    schema = BandMemberSchema(strict=True)

    # 1.0
    try:
        schema.load({'email': 'invalid-email'})
    except exc.UnmarshallingError as err:
        # ...

    # 2.0
    try:
        schema.load({'email': 'invalid-email'})
    except exc.ValidationError as err:
        # ...


Accessing error messages in strict mode
***************************************

In 2.0, `strict` mode was improved so that you can access all error messages for a schema (rather than failing early) by accessing a `ValidationError's` ``messages`` attribute.

.. code-block:: python
    :emphasize-lines: 6

    schema = BandMemberSchema(strict=True)

    try:
        result = schema.load({'email': 'invalid'})
    except ValidationMessage as err:
        print(err.messages)
    # {
    #     'email': ['"invalid" is not a valid email address.'],
    #     'name': ['Missing data for required field.']
    # }


Custom Fields
*************

Two changes must be made to make your custom fields compatible with version 2.0.

- The `_deserialize <marshmallow.fields.Field._deserialize>` method of custom fields now receives ``attr`` (the key corresponding to the value to be deserialized) and the raw input ``data`` as arguments.
- Custom fields should raise :exc:`ValidationError <marshmallow.exceptions.ValidationError>` in their `_deserialize` and `_serialize` methods when a validation error occurs.

.. code-block:: python

    from marshmallow import fields, ValidationError
    from marshmallow.exceptions import UnmarshallingError

    # In 1.0, an UnmarshallingError was raised
    class PasswordField(fields.Field):

        def _deserialize(self, val):
            if not len(val) >= 6:
                raise UnmarshallingError('Password too short.')
            return val

    # In 2.0, _deserialize receives attr and data,
    # and a ValidationError is raised
    class PasswordField(fields.Field):

        def _deserialize(self, val, attr, data):
            if not len(val) >= 6:
                raise ValidationError('Password too short.')
            return val


To make a field compatible with both marshmallow 1.x and 2.x, you can pass `*args` and `**kwargs` to the signature.

.. code-block:: python

    class PasswordField(fields.Field):

        def _deserialize(self, val, *args, **kwargs):
            if not len(val) >= 6:
                raise ValidationError('Password too short.')
            return val

Custom Error Messages
*********************

Error messages can be customized at the `Field` class or instance level.


.. code-block:: python

    # 1.0
    field = fields.Number(error='You passed a bad number')

    # 2.0
    # Instance-level
    field = fields.Number(error_messages={'invalid': 'You passed a bad number.'})


    # Class-level
    class MyNumberField(fields.Number):
        default_error_messages = {
            'invalid': 'You passed a bad number.'
        }

Passing a string to ``required`` is deprecated.

.. code-block:: python

    # 1.0
    field = fields.Str(required='Missing required argument.')

    # 2.0
    field = fields.Str(error_messages={'required': 'Missing required argument.'})


Use ``OneOf`` instead of ``fields.Select``
******************************************

The `fields.Select` field is deprecated in favor of the newly-added `OneOf` validator.

.. code-block:: python

    from marshmallow import fields
    from marshmallow.validate import OneOf

    # 1.0
    fields.Select(['red', 'blue'])

    # 2.0
    fields.Str(validate=OneOf(['red', 'blue']))

Accessing Context from Method fields
************************************

Use ``self.context`` to access a schema's context within a ``Method`` field.

.. code-block:: python

    class UserSchema(Schema):
        name = fields.String()
        likes_bikes = fields.Method('writes_about_bikes')

        def writes_about_bikes(self, user):
            return 'bicycle' in self.context['blog'].title.lower()


Validation Error Messages
*************************

The default error messages for many fields and validators have been changed for better consistency.

.. code-block:: python

    from marshmallow import Schema, fields, validate

    class ValidatingSchema(Schema):
        foo = fields.Str()
        bar = fields.Bool()
        baz = fields.Int()
        qux = fields.Float()
        spam = fields.Decimal(2, 2)
        eggs = fields.DateTime()
        email = fields.Str(validate=validate.Email())
        homepage = fields.Str(validate=validate.URL())
        nums = fields.List(fields.Int())

    schema = ValidatingSchema()
    invalid_data = {
        'foo': 42,
        'bar': 24,
        'baz': 'invalid-integer',
        'qux': 'invalid-float',
        'spam': 'invalid-decimal',
        'eggs': 'invalid-datetime',
        'email': 'invalid-email',
        'homepage': 'invalid-url',
        'nums': 'invalid-list',
    }
    errors = schema.validate(invalid_data)
    # {
    #     'foo': ['Not a valid string.'],
    #     'bar': ['Not a valid boolean.'],
    #     'baz': ['Not a valid integer.'],
    #     'qux': ['Not a valid number.'],
    #     'spam': ['Not a valid number.']
    #     'eggs': ['Not a valid datetime.'],
    #     'email': ['Not a valid email address.'],
    #     'homepage': ['Not a valid URL.'],
    #     'nums': ['Not a valid list.'],
    # }

More
****

For a full list of changes in 2.0, see the :doc:`Changelog <changelog>`.


Upgrading to 1.2
++++++++++++++++

Validators
**********

Validators were rewritten as class-based callables, making them easier to use when declaring fields.

.. code-block:: python

    from marshmallow import fields

    # 1.2
    from marshmallow.validate import Range

    age = fields.Int(validate=[Range(min=0, max=999)])

    # Pre-1.2
    from marshmallow.validate import ranging

    age = fields.Int(validate=[lambda val: ranging(val, min=0, max=999)])


The validator functions from 1.1 are deprecated and will be removed in 2.0.

Deserializing the Empty String
******************************


In version 1.2, deserialization of the empty string (``''``) with `DateTime`, `Date`, `Time`, or `TimeDelta` fields results in consistent error messages, regardless of whether or not `python-dateutil` is installed.

.. code-block:: python

    from marshmallow import fields

    fields.Date().deserialize('')
    # UnmarshallingError: Could not deserialize '' to a date object.


Decimal
*******

The `Decimal` field was added to support serialization/deserialization of `decimal.Decimal` numbers. You should use this field when dealing with numbers where precision is critical. The `Fixed`, `Price`, and `Arbitrary` fields are deprecated in favor the `Decimal` field.


Upgrading to 1.0
++++++++++++++++

Version 1.0 marks the first major release of marshmallow. Many big changes were made from the pre-1.0 releases in order to provide a cleaner API, support object deserialization, and improve field validation.

Perhaps the largest change is in how objects get serialized. Serialization occurs by invoking the :meth:`Schema.dump` method rather than passing the object to the constructor.  Because only configuration options (e.g. the ``many``, ``strict``, and ``only`` parameters) are passed to the constructor, you can more easily reuse serializer instances.  The :meth:`dump <Schema.dump>` method also forms a nice symmetry with the :meth:`Schema.load` method, which is used for deserialization.

.. code-block:: python

    from marshmallow import Schema, fields

    class UserSchema(Schema):
        email = fields.Email()
        name = fields.String()

    user= User(email='monty@python.org', name='Monty Python')

    # 1.0
    serializer = UserSchema()
    data, errors = serializer.dump(user)
    # OR
    result = serializer.dump(user)
    result.data  # => serialized result
    result.errors  # => errors

    # Pre-1.0
    serialized = UserSchema(user)
    data = serialized.data
    errors = serialized.errors

.. note::

    Some crucial parts of the pre-1.0 API have been retained to ease the transition. You can still pass an object to a `Schema` constructor and access the `Schema.data` and `Schema.errors` properties. The `is_valid` method, however, has been completely removed. It is recommended that you migrate to the new API to prevent future releases from breaking your code.

The Fields interface was also reworked in 1.0 to make it easier to define custom fields with their own serialization and deserialization behavior. Custom fields now implement :meth:`Field._serialize` and :meth:`Field._deserialize`.

.. code-block:: python

    from marshmallow import fields, MarshallingError

    class PasswordField(fields.Field):
        def _serialize(self, value, attr, obj):
            if not value or len(value) < 6:
                raise MarshallingError('Password must be greater than 6 characters.')
            return str(value).strip()

        # Similarly, you can override the _deserialize method

Another major change in 1.0 is that multiple validation errors can be stored for a single field. The ``errors`` dictionary returned by :meth:`Schema.dump` and :meth:`Schema.load` is a list of error messages keyed by field name.


.. code-block:: python

    from marshmallow import Schema, fields, ValidationError

    def must_have_number(val):
        if not any(ch.isdigit() for ch in val):
            raise ValidationError('Value must have an number.')

    def validate_length(val):
        if len(val) < 8:
            raise ValidationError('Value must have 8 or more characters.')

    class ValidatingSchema(Schema):
        password = fields.String(validate=[must_have_number, validate_length])

    result, errors = ValidatingSchema().load({'password': 'secure'})
    print(errors)
    # {'password': ['Value must have an number.',
    #               'Value must have 8 or more characters.']}

Other notable changes:

- Serialized output is no longer an `OrderedDict` by default. You must explicitly set the `ordered` class Meta option to `True` .
- :class:`Serializer` has been renamed to :class:`Schema`, but you can still import `marshmallow.Serializer` (which is aliased to :class:`Schema`).
- ``datetime`` objects serialize to ISO8601-formatted strings by default (instead of RFC821 format).
- The ``fields.validated`` decorator was removed, as it is no longer necessary given the new Fields interface.
- `Schema.factory` class method was removed.

.. seealso::

    See the :doc:`Changelog <changelog>` for a  more complete listing of added features, bugfixes and breaking changes.
