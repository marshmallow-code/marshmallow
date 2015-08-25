
.. _upgrading:


Upgrading to Newer Releases
===========================

This section documents migration paths to new releases.

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

The pre- and post-processing API was significantly improved for better consistency and flexibility. The `pre_load <marshmallow.decorators.pre_load>`, `post_load <marshmallow.decorators.post_load>`, `pre_dump <marshmallow.decorators.pre_dump>`, and `post_dump <marshmallow.decorators.post_dump>` should be used to define processing hooks. `Schema.preprocessor` and `Schema.data_handler` are deprecated.


.. code-block:: python

    # 1.0 Deprecated API
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

See the :ref:`Extending Schemas <extending>` page for more information on the ``pre_*`` and ``post_*`` decorators.

Schema Validators
*****************

Similar to pre-processing and post-processing methods, schema validators are now defined as methods. Decorate schema validators with `validator <marshmallow.decorators.validator>`. `Schema.validator <marshmallow.Schema.validator>` is deprecated.

.. code-block:: python

    # 1.0 Deprecated API
    from marshmallow import Schema, fields, ValidationError

    class MySchema(Schema):
        field_a = fields.Int(required=True)
        field_b = fields.Int(required=True)

    @ExampleSchema.validator
    def validate_schema(schema, data):
        if data['field_a'] < data['field_b']:
            raise ValidationError('field_a must be greater than field_b')

    # 2.0 API
    from marshmallow import Schema, fields, validator, ValidationError

    class MySchema(Schema):
        field_a = fields.Int(required=True)
        field_b = fields.Int(required=True)

        @validator
        def validate_schema(self, data):
            if data['field_a'] < data['field_b']:
                raise ValidationError('field_a must be greater than field_b')

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


Error Messages for URL and Email Address Validation
***************************************************

The default error messages for URL and email validation were changed in 2.0.

.. code-block:: python

    from marshmallow import Schema, fields, validate

    class UserSchema(Schema):
        email = fields.Str(validate=validate.Email())
        homepage = fields.Str(validate=validate.URL())

    schema = UserSchema()
    invalid_data = {'email': 'foo', 'homepage': 'bar'}

    # 1.0
    schema.validate(invalid_data)
    # {'email': ['"foo" is not a valid email address.'], 'homepage': ['"bar" is not a valid URL.']}

    # 2.0
    schema.validate(invalid_data)
    # {'email': ['Invalid email address.'], 'homepage': ['Invalid URL.']}


You can get the old messages by passing the ``error`` argument to the validators.

.. code-block:: python

    class UserSchema(Schema):
        email = fields.Str(validate=validate.Email(
            error='"{input}" is not a valid email address.'
        ))
        homepage = fields.Str(validate=validate.URL(
            error='"{input}" is not a valid URL.'
        ))

More
****

For a full list of changes in 2.0, see the :ref:`Changelog <changelog>`.


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

    See the :ref:`Changelog <changelog>` for a  more complete listing of added features, bugfixes and breaking changes.
