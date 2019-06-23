Upgrading to Newer Releases
===========================

This section documents migration paths to new releases.

.. _upgrading_3_0:

Upgrading to 3.0
++++++++++++++++

Python compatibility
********************

The marshmallow 3.x series supports Python >= 3.5.

Python 2.6, 2.7, 3.3, and 3.4 are no longer supported.


Schemas are always strict
*************************

Two major changes were made to (de)serialization behavior:

- The ``strict`` parameter was removed. Schemas are always strict.
- `Schema().load <marshmallow.Schema.load>` and `Schema().dump <marshmallow.Schema.dump>` don't return a ``(data, errors)`` tuple any more. Only ``data`` is returned.

If invalid data are passed, a :exc:`ValidationError <marshmallow.exceptions.ValidationError>` is raised.
The dictionary of validation errors is accessible from the
`ValidationError.messages <marshmallow.exceptions.ValidationError.messages>` attribute,
along with the valid data from the `ValidationError.valid_data
<marshmallow.exceptions.ValidationError.valid_data>` attribute.

.. code-block:: python

    from marshmallow import ValidationError

    # 2.x
    schema = UserSchema()
    data, errors = schema.load({"name": "Monty", "email": "monty@python.org"})
    # OR
    schema = UserSchema(strict=True)
    try:
        data, _ = schema.load({"name": "Monty", "email": "monty@python.org"})
    except ValidationError as err:
        errors = err.messages
        valid_data = err.valid_data

    # 3.x
    schema = UserSchema()
    # There is only one right way
    try:
        data = schema.load({"name": "Monty", "email": "monty@python.org"})
    except ValidationError as err:
        errors = err.messages
        valid_data = err.valid_data

:meth:`Schema().validate <marshmallow.Schema.validate>` always returns a dictionary of validation errors (same as 2.x with ``strict=False``).

.. code-block:: python

    schema.validate({"email": "invalid"})
    # {'email': ['Not a valid email address.']}

Setting the ``strict`` option on ``class Meta`` has no effect on `Schema` behavior.
Passing ``strict=True`` or ``strict=False`` to the `Schema` constructor
will raise a :exc:`TypeError`.


.. code-block:: python

    # 3.x
    UserSchema(strict=True)
    # TypeError: __init__() got an unexpected keyword argument 'strict'


.. seealso::

    See GitHub issues :issue:`377` and :issue:`598` for the discussions on
    this change.


Decorated methods receive ``many`` and ``partial``
**************************************************

Methods decorated with
`pre_load <marshmallow.decorators.pre_load>`, `post_load <marshmallow.decorators.post_load>`,
`pre_dump <marshmallow.decorators.pre_dump>`, `post_dump <marshmallow.decorators.post_dump>`,
and `validates_schema <marshmallow.decorators.validates_schema>` receive
``many`` as a keyword argument. In addition, `pre_load <marshmallow.decorators.pre_load>`, `post_load <marshmallow.decorators.post_load>`,
and `validates_schema <marshmallow.decorators.validates_schema>` receive
``partial``. To account for these additional arguments, add ``**kwargs`` to your methods.

.. code-block:: python

    # 2.x
    class UserSchema(Schema):
        name = fields.Str()
        slug = fields.Str()

        @pre_load
        def slugify_name(self, in_data):
            in_data["slug"] = in_data["slug"].lower().strip().replace(" ", "-")
            return in_data


    # 3.x
    class UserSchema(Schema):
        name = fields.Str()
        slug = fields.Str()

        @pre_load
        def slugify_name(self, in_data, **kwargs):
            in_data["slug"] = in_data["slug"].lower().strip().replace(" ", "-")
            return in_data

Deserializing invalid types raises a ``ValidationError``
********************************************************

Numbers, booleans, strings, and ``None`` are
considered invalid input to `Schema.load
<marshmallow.Schema.load>`.

.. code-block:: python

    # 2.x
    # Passes silently
    schema.load(None)
    schema.load(False)
    schema.load("pass")

    # 3.x
    # marshmallow.exceptions.ValidationError: {'_schema': ['Invalid input type.']}
    schema.load(None)
    schema.load(False)
    schema.load("nope")


When ``many=True``, non-collection types are also considered invalid.


.. code-block:: python

    # 2.x
    # Passes silently
    schema.load(None, many=True)
    schema.load({}, many=True)
    schema.load("pass", many=True)

    # 3.x
    # marshmallow.exceptions.ValidationError: {'_schema': ['Invalid input type.']}
    schema.load(None, many=True)
    schema.load({}, many=True)
    schema.load("invalid", many=True)


``ValidationError.fields`` is removed
*************************************

:exc:`ValidationError <marshmallow.exceptions.ValidationError>` no
longer stores a list of `Field <marshmallow.fields.Field>` instances
associated with the validation errors.

If you need field instances associated with an error, you can access
them from ``schema.fields``.

.. code-block:: python


    from marshmallow import Schema, fields, ValidationError


    class MySchema(Schema):
        foo = fields.Int()


    schema = MySchema()

    try:
        schema.load({"foo": "invalid"})
    except ValidationError as error:
        field = schema.fields["foo"]
        # ...


``ValidationError`` expects a single field name
***********************************************

:exc:`ValidationError <marshmallow.exceptions.ValidationError>` no
longer accepts a list of field names. It expects a single field name. If none
is passed, the error refers to the schema.

To return an error for several fields at once, a `dict` must be used.

.. code-block:: python

    from marshmallow import Schema, fields, validates_schema, ValidationError


    class NumberSchema(Schema):
        field_a = fields.Integer()
        field_b = fields.Integer()

        # 2.x
        @validates_schema
        def validate_numbers(self, data):
            if data["field_b"] >= data["field_a"]:
                raise ValidationError(
                    "field_a must be greater than field_b", ["field_a", "field_b"]
                )

        # 3.x
        @validates_schema
        def validate_numbers(self, data):
            if data["field_b"] >= data["field_a"]:
                raise ValidationError(
                    {
                        "field_a": ["field_a must be greater than field_b"],
                        "field_b": ["field_a must be greater than field_b"],
                    }
                )

``ValidationError`` error messages are deep-merged
**************************************************

When multiple :exc:`ValidationError <marshmallow.exceptions.ValidationError>`
are raised, the error structures are merged in the final :exc:`ValidationError`
raised at the end of the process.

When reporting error messages as `dict`, the keys should refer to subitems
of the item the message refers to, and the values should be error messages.

See the "Schema-level Validation" section of :doc:`Extending Schemas <extending>`
page for an example.

Schemas raise ``ValidationError`` when deserializing data with unknown keys
***************************************************************************

Marshmallow 3.x schemas can deal with unknown keys in three different ways,
configurable with the ``unknown`` option:

- ``EXCLUDE``: drop those keys (same as marshmallow 2)
- ``INCLUDE``: pass those keys/values as is, with no validation performed
- ``RAISE`` (default): raise a ``ValidationError``

The ``unknown`` option can be passed as a Meta option, on Schema instantiation,
or at load time.

.. code-block:: python

    from marshmallow import Schema, fields, EXCLUDE, INCLUDE, RAISE


    class MySchema(Schema):
        foo = fields.Int()

        class Meta:
            # Pass EXCLUDE as Meta option to keep marshmallow 2 behavior
            unknown = EXCLUDE


    MySchema().load({"foo": 42, "bar": "whatever"})  # => ['foo': 42]

    #  Value passed on instantiation overrides Meta option
    schema = MySchema(unknown=INCLUDE)
    schema.load({"foo": 42, "bar": "whatever"})  # => ['foo': 42, 'bar': 'whatever']

    #  Value passed on load overrides instance attribute
    schema.load({"foo": 42, "bar": "whatever"}, unknown=RAISE)  # => ValidationError

Overriding ``get_attribute``
****************************

If your `Schema <marshmallow.Schema>` overrides `get_attribute <marshmallow.Schema.get_attribute>`, you will need to update the method's signature. The positions of the ``attr`` and ``obj`` arguments were switched for consistency with Python builtins, e.g. `getattr`.

.. code-block:: python

    from marshmallow import Schema

    # 2.x
    class MySchema(Schema):
        def get_attribute(self, attr, obj, default):
            return getattr(obj, attr, default)


    # 3.x
    class MySchema(Schema):
        def get_attribute(self, obj, attr, default):
            return getattr(obj, attr, default)

``pass_original=True`` passes individual items when ``many=True``
*****************************************************************

When ``pass_original=True`` is passed to
`validates_schema <marshmallow.decorators.validates_schema>`,
`post_load <marshmallow.decorators.post_load>`, or
`post_dump <marshmallow.decorators.post_dump>`, the `original_data`
argument will be a single item corresponding to the (de)serialized
datum.

.. code-block:: python

    from marshmallow import Schema, fields, post_load, EXCLUDE


    class ShoeSchema(Schema):
        size = fields.Int()

        class Meta:
            unknown = EXCLUDE

        @post_load(pass_original=True)
        def post_load(self, data, original_data, **kwargs):
            # original_data has 'width' but
            # data does not because it's not
            # in the schema
            assert "width" in original_data
            assert "width" not in data
            return data


    input_data = [{"size": 10, "width": "M"}, {"size": 6, "width": "W"}]

    print(ShoeSchema(many=True).load(input_data))
    # [{'size': 10}, {'size': 6}]


``utils.get_func_args`` no longer returns bound arguments
*********************************************************

The `utils.get_func_args <marshmallow.utils.get_func_args>` function will no longer return bound arguments, e.g. `'self'`.

.. code-block:: python

    from marshmallow.utils import get_func_args


    class MyCallable:
        def __call__(self, foo, bar):
            return 42


    callable_obj = MyCallable()

    # 2.x
    get_func_args(callable_obj)  # => ['self', 'foo', 'bar']

    # 3.x
    get_func_args(callable_obj)  # => ['foo', 'bar']


Handling ``AttributeError`` in ``Method`` and ``Function`` fields
*****************************************************************

The `Method <marshmallow.fields.Method>` and `Function <marshmallow.fields.Function>` fields no longer swallow ``AttributeErrors``. Therefore, your methods and functions are responsible for handling inputs such as `None`.

.. code-block:: python

    from marshmallow import Schema, fields, missing

    # 2.x
    class ShapeSchema(Schema):
        area = fields.Method("get_area")

        def get_area(self, obj):
            return obj.height * obj.length


    schema = ShapeSchema()
    # In 2.x, the following would pass without errors
    # In 3.x, and AttributeError would be raised
    result = schema.dump(None)
    result  # => {}


    # 3.x
    class ShapeSchema(Schema):
        area = fields.Method("get_area")

        def get_area(self, obj):
            if obj is None:
                # 'area' will not appear in serialized output
                return missing
            return obj.height * obj.length


    schema = ShapeSchema()
    result = schema.dump(None)
    result  # => {}

Adding additional data to serialized output
*******************************************

Use a `post_dump <marshmallow.decorators.post_dump>` to add additional data on serialization. The ``extra`` argument on `Schema <marshmallow.Schema>` was removed.


.. code-block:: python

    from marshmallow import Schema, fields, post_dump

    # 2.x
    class MySchema(Schema):
        x = fields.Int()
        y = fields.Int()


    schema = MySchema(extra={"z": 123})
    schema.dump({"x": 1, "y": 2})
    # => {'z': 123, 'y': 2, 'x': 1}

    # 3.x
    class MySchema(Schema):
        x = fields.Int()
        y = fields.Int()

        @post_dump
        def add_z(self, output):
            output["z"] = 123
            return output


    schema = MySchema()
    schema.dump({"x": 1, "y": 2})
    # => {'z': 123, 'y': 2, 'x': 1}


Schema-level validators are skipped when field validation fails
***************************************************************

By default, schema validator methods decorated by `validates_schema <marshmallow.decorators.validates_schema>` won't execute if any of the field validators fails (including ``required=True`` validation).

.. code-block:: python

    from marshmallow import Schema, fields, validates_schema, ValidationError


    class MySchema(Schema):
        x = fields.Int(required=True)
        y = fields.Int(required=True)

        @validates_schema
        def validate_schema(self, data):
            if data["x"] <= data["y"]:
                raise ValidationError("x must be greater than y")


    schema = MySchema()

    # 2.x
    # A KeyError is raised in validate_schema
    schema.load({"x": 2})

    # 3.x
    # marshmallow.exceptions.ValidationError: {'y': ['Missing data for required field.']}
    # validate_schema is not run
    schema.load({"x": 2})

If you want a schema validator to run even if a field validator fails, pass ``skip_on_field_errors=False``. Make sure your code handles cases where fields are missing from the deserialized data (due to validation errors).


.. code-block:: python

    from marshmallow import Schema, fields, validates_schema, ValidationError


    class MySchema(Schema):
        x = fields.Int(required=True)
        y = fields.Int(required=True)

        @validates_schema(skip_on_field_errors=False)
        def validate_schema(self, data):
            if "x" in data and "y" in data:
                if data["x"] <= data["y"]:
                    raise ValidationError("x must be greater than y")


    schema = MySchema()
    schema.load({"x": 2})
    # marshmallow.exceptions.ValidationError: {'y': ['Missing data for required field.']}

`SchemaOpts` constructor receives ``ordered`` argument
******************************************************

Subclasses of `SchemaOpts <marshmallow.SchemaOpts>` receive an additional argument, ``ordered``, which is `True` if the `ordered` option is set to `True` on a Schema or one of its parent classes.

.. code-block:: python

    from marshmallow import SchemaOpts

    # 2.x
    class CustomOpts(SchemaOpts):
        def __init__(self, meta):
            super().__init__(meta)
            self.custom_option = getattr(meta, "meta", False)


    # 3.x
    class CustomOpts(SchemaOpts):
        def __init__(self, meta, ordered=False):
            super().__init__(meta, ordered)
            self.custom_option = getattr(meta, "meta", False)

`ContainsOnly` accepts empty and duplicate values
*************************************************

`validate.ContainsOnly <marshmallow.validate.ContainsOnly>` now accepts duplicate values in the input value.


.. code-block:: python

    from marshmallow import validate

    validator = validate.ContainsOnly(["red", "blue"])

    # in 2.x the following raises a ValidationError
    # in 3.x, no error is raised
    validator(["red", "red", "blue"])


If you don't want to accept duplicates, use a custom validator, like the following.

.. code-block:: python

    from marshmallow import ValidationError
    from marshmallow.validate import ContainsOnly


    class ContainsOnlyNoDuplicates(ContainsOnly):
        def __call__(self, value):
            ret = super(ContainsOnlyNoDuplicates, self).__call__(value)
            if len(set(value)) != len(value):
                raise ValidationError("Duplicate values not allowed")
            return ret

.. note::

    If you need to handle unhashable types, you can use the  `implementation of
    ContainsOnly from marshmallow 2.x <https://github.com/marshmallow-code/marshmallow/blob/2888e6978bc8c409a5fed35da6ece8bdb23384f2/marshmallow/validate.py#L436-L467>`_.

`validate.ContainsOnly <marshmallow.validate.ContainsOnly>` also accepts empty values as valid input.

.. code-block:: python

    from marshmallow import validate

    validator = validate.ContainsOnly(["red", "blue"])

    # in 2.x the following raises a ValidationError
    # in 3.x, no error is raised
    validator([])

To validate against empty inputs, use `validate.Length(min=1) <marshmallow.validate.Length>`.


``json_module`` option is renamed to ``render_module``
******************************************************

The ``json_module`` class Meta option is deprecated in favor of ``render_module``.

.. code-block:: python

    import ujson

    # 2.x
    class MySchema(Schema):
        class Meta:
            json_module = ujson


    # 3.x
    class MySchema(Schema):
        class Meta:
            render_module = ujson


``missing`` and ``default`` ``Field`` parameters are passed in deserialized form
********************************************************************************

.. code-block:: python

    # 2.x
    class UserSchema(Schema):
        id = fields.UUID(missing=lambda: str(uuid.uuid1()))
        birthdate = fields.DateTime(default=lambda: dt.datetime(2017, 9, 19).isoformat())


    # 3.x
    class UserSchema(Schema):
        id = fields.UUID(missing=uuid.uuid1)
        birthdate = fields.DateTime(default=dt.datetime(2017, 9, 19))


Pass ``default`` as a keyword argument
**************************************

`fields.Boolean <marshmallow.fields.Boolean>` now receives additional ``truthy`` and ``falsy`` parameters. Consequently, the ``default`` parameter should always be passed as a keyword argument.


.. code-block:: python

    # 2.x
    fields.Boolean(True)

    # 3.x
    fields.Boolean(default=True)


``Email`` and ``URL`` fields do not validate on serialization
*************************************************************

`fields.Email <marshmallow.fields.Email>` and `fields.URL <marshmallow.fields.URL>` only validate input upon
deserialization. They do not validate on serialization. This makes them
more consistent with the other fields and improves serialization
performance.


``load_from`` and ``dump_to`` are merged into ``data_key``
**********************************************************

The same key is used for serialization and deserialization.

.. code-block:: python

    # 2.x
    class UserSchema(Schema):
        email = fields.Email(load_from="CamelCasedEmail", dump_to="CamelCasedEmail")


    # 3.x
    class UserSchema(Schema):
        email = fields.Email(data_key="CamelCasedEmail")

It is not possible to specify a different key for serialization and deserialization on the same field.
This use case is covered by using two different `Schema`.

.. code-block:: python

    from marshmallow import Schema, fields

    # 2.x
    class UserSchema(Schema):
        id = fields.Str()
        email = fields.Email(load_from="CamelCasedEmail", dump_to="snake_case_email")


    # 3.x
    class BaseUserSchema(Schema):
        id = fields.Str()


    class LoadUserSchema(BaseUserSchema):
        email = fields.Email(data_key="CamelCasedEmail")


    class DumpUserSchema(BaseUserSchema):
        email = fields.Email(data_key="snake_case_email")


Also, when ``data_key`` is specified on a field, only ``data_key`` is checked in the input data. In marshmallow 2.x the field name is checked if ``load_from`` is missing from the input data.

Pre/Post-processors must return modified data
*********************************************

In marshmallow 2.x, ``None`` returned by a pre or post-processor is interpreted as "the data was mutated". In marshmallow 3.x, the return value is considered as processed data even if it is ``None``.

Processors that mutate the data should be updated to also return it.


.. code-block:: python

    # 2.x
    class UserSchema(Schema):
        name = fields.Str()
        slug = fields.Str()

        @pre_load
        def slugify_name(self, in_data):
            # In 2.x, implicitly returning None implied that data were mutated
            in_data["slug"] = in_data["slug"].lower().strip().replace(" ", "-")


    # 3.x
    class UserSchema(Schema):
        name = fields.Str()
        slug = fields.Str()

        @pre_load
        def slugify_name(self, in_data, **kwargs):
            # In 3.x, always return the processed data
            in_data["slug"] = in_data["slug"].lower().strip().replace(" ", "-")
            return in_data

``Nested`` field no longer supports plucking
********************************************

In marshmallow 2.x, when a string was passed to a ``Nested`` field's ```only`` parameter, the field would be plucked. In marshmallow 3.x, the ``Pluck`` field must be used instead.


.. code-block:: python

    # 2.x
    class UserSchema(Schema):
        name = fields.Str()
        friends = fields.Nested("self", many=True, only="name")


    # 3.x
    class UserSchema(Schema):
        name = fields.Str()
        friends = fields.Pluck("self", "name", many=True)


Accessing attributes on objects within a list
*********************************************

In order to serialize attributes on inner objects within a list, use the
``Pluck`` field.

.. code-block:: python

    # 2.x
    class FactorySchema(Schema):
        widget_ids = fields.List(fields.Int(attribute="id"))


    # 3.x
    class FactorySchema(Schema):
        widget_ids = fields.List(fields.Pluck(WidgetSchema, "id"))


``Float`` field takes a new ``allow_nan`` parameter
***************************************************

In marshmallow 2.x, ``Float`` field would serialize and deserialize special values such as ``nan``, ``inf`` or ``-inf``. In marshmallow 3, those values trigger a ``ValidationError`` unless ``allow_nan`` is ``True``. ``allow_nan`` defaults to ``False``.


.. code-block:: python

    # 2.x
    class MySchema(Schema):
        x = fields.Float()


    MySchema().load({"x": "nan"})
    # => {{'x': nan}}

    # 3.x
    class MySchema(Schema):
        x = fields.Float()
        y = fields.Float(allow_nan=True)


    MySchema().load({"x": 12, "y": "nan"})
    # => {{'x': 12.0, 'y': nan}}

    MySchema().load({"x": "nan"})
    # marshmallow.exceptions.ValidationError: {'x': ['Special numeric values (nan or infinity) are not permitted.']}

``DateTime`` field ``dateformat`` ``Meta`` option is renamed ``datetimeformat``
*******************************************************************************

The ``Meta`` option ``dateformat`` used to pass format to `DateTime <marshmallow.fields.DateTime>` field is renamed as ``datetimeformat``.

`Date <marshmallow.fields.Date>` field gets a new ``format`` parameter to specify the format to use for serialization. ``dateformat`` ``Meta`` option now applies to `Date <marshmallow.fields.Date>` field.

.. code-block:: python

    # 2.x
    class MySchema(Schema):
        x = fields.DateTime()

        class Meta:
            dateformat = "%Y-%m"


    MySchema().dump({"x": dt.datetime(2017, 9, 19)})
    # => {{'x': '2017-09'}}

    # 3.x
    class MySchema(Schema):
        x = fields.DateTime()
        y = fields.Date()

        class Meta:
            datetimeformat = "%Y-%m"
            dateformat = "%m-%d"


    MySchema().dump({"x": dt.datetime(2017, 9, 19), "y": dt.date(2017, 9, 19)})
    # => {{'x': '2017-09', 'y': '09-19'}}

The ``prefix`` ``Schema`` parameter is removed
**********************************************

The ``prefix`` parameter of ``Schema`` is removed. The same feature can be achieved using a post_dump <marshmallow.decorators.post_dump>` method.


.. code-block:: python

    # 2.x
    class MySchema(Schema):
        f1 = fields.Field()
        f2 = fields.Field()


    MySchema(prefix="pre_").dump({"f1": "one", "f2": "two"})
    # {'pre_f1': 'one', '_pre_f2': 'two'}

    # 3.x
    class MySchema(Schema):
        f1 = fields.Field()
        f2 = fields.Field()

        @post_dump
        def prefix_usr(self, data):
            return {"usr_{}".format(k): v for k, v in iteritems(data)}


    MySchema().dump({"f1": "one", "f2": "two"})
    # {'pre_f1': 'one', '_pre_f2': 'two'}


``fields.FormattedString`` is removed
*************************************

``fields.FormattedString`` field is removed. Use `fields.Function
<marshmallow.fields.Function>` or
`fields.Method <marshmallow.fields.Method>` instead.

.. code-block:: python

    # 2.x
    class MySchema(Schema):
        full_name = fields.FormattedString("{first_name} {last_name}")


    # 3.x
    class MySchema(Schema):
        full_name = fields.Function(lambda u: f"{u.first_name} {u.last_name}")


``attribute`` or ``data_key`` collision triggers an exception
*************************************************************

When a `Schema <marshmallow.Schema>` is instantiated, a check is performed and a ``ValueError`` is triggered if

- several fields have the same ``attribute`` value (or field name if ``attribute`` is not passed), excluding ``dump_only`` fields, or
- several fields have the same ``data_key`` value (or field name if ``data_key`` is not passed), excluding ``load_only`` fields

In marshmallow 2, it was possible to have multiple fields with the same ``attribute``. It would work provided the ``Schema`` was only used for dumping. When loading, the behaviour was undefined. In marshmallow 3, all but one of those fields must be marked as ``dump_only``. Likewise for ``data_key`` (formerly ``dump_to``) for fields that are not ``load_only``.

.. code-block:: python

    # 2.x
    class MySchema(Schema):
        f1 = fields.Field()
        f2 = fields.Field(attribute="f1")
        f3 = fields.Field(attribute="f5")
        f4 = fields.Field(attribute="f5")


    MySchema()
    #  No error

    # 3.x
    class MySchema(Schema):
        f1 = fields.Field()
        f2 = fields.Field(attribute="f1")
        f3 = fields.Field(attribute="f5")
        f4 = fields.Field(attribute="f5")


    MySchema()
    # ValueError: 'Duplicate attributes: ['f1', 'f5]'


    class MySchema(Schema):
        f1 = fields.Field()
        f2 = fields.Field(attribute="f1", dump_only=True)
        f3 = fields.Field(attribute="f5")
        f4 = fields.Field(attribute="f5", dump_only=True)


    MySchema()
    # No error


``python-dateutil`` recommended dependency is removed
*****************************************************

In marshmallow 2, ``python-dateutil`` was used to deserialize RFC or ISO 8601
datetimes if it was installed. In marshmallow 3, datetime deserialization is
done with no additional dependency.

``python-dateutil`` is no longer used by marshmallow.


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

Similarly, the ``method_name`` of `fields.Method <marshmallow.fields.Method>` was also renamed to ``serialize``.

.. code-block:: python

    # YES
    lowername = fields.Method(serialize="lowercase")
    # or
    lowername = fields.Method("lowercase")

    # NO
    lowername = fields.Method(method_name="lowercase")

The ``func`` parameter is still available for backwards-compatibility. It will be removed in marshmallow 3.0.

Both `fields.Function <marshmallow.fields.Function>` and `fields.Method <marshmallow.fields.Method>` will allow the serialize parameter to not be passed, in this case use the ``deserialize`` parameter by name.

.. code-block:: python

    lowername = fields.Function(deserialize=lambda name: name.lower())
    # or
    lowername = fields.Method(deserialize="lowername")

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
    schema.dump(
        {"str_no_default": None, "int_no_default": None, "list_no_default": None}
    ).data
    # {'str_no_default': '', 'int_no_default': 0, 'list_no_default': []}

    # In 2.0, None serializes to None. No more implicit defaults.
    schema.dump(
        {"str_no_default": None, "int_no_default": None, "list_no_default": None}
    ).data
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
        data["field_a"] += 1
        return data


    @ExampleSchema.data_handler
    def decrement(schema, data, obj):
        data["field_a"] -= 1
        return data


    # 2.0 API
    from marshmallow import Schema, fields, pre_load, post_dump


    class ExampleSchema(Schema):
        field_a = fields.Int()

        @pre_load
        def increment(self, data):
            data["field_a"] += 1
            return data

        @post_dump
        def decrement(self, data):
            data["field_a"] -= 1
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
        if data["field_a"] < data["field_b"]:
            raise ValidationError("field_a must be greater than field_b")


    # 2.0 API
    from marshmallow import Schema, fields, validates_schema, ValidationError


    class MySchema(Schema):
        field_a = fields.Int(required=True)
        field_b = fields.Int(required=True)

        @validates_schema
        def validate_schema(self, data):
            if data["field_a"] < data["field_b"]:
                raise ValidationError("field_a must be greater than field_b")

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
        raise CustomError("Something bad happened", messages=errors)


    # 2.0 API
    class ExampleSchema(Schema):
        field_a = fields.Int()

        def get_attribute(self, attr, obj, default):
            return obj.get(attr, default)

        # handle_error gets passed a ValidationError
        def handle_error(self, exc, data):
            raise CustomError("Something bad happened", messages=exc.messages)

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
        {"email": "mick@stones.com", "name": "Mick"},
        {"email": "invalid", "name": "Invalid"},  # invalid email
        {"email": "keith@stones.com", "name": "Keith"},
        {"email": "charlie@stones.com"},  # missing "name"
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
        schema.load({"email": "invalid-email"})
    except exc.UnmarshallingError as err:
        handle_error(err)

    # 2.0
    try:
        schema.load({"email": "invalid-email"})
    except exc.ValidationError as err:
        handle_error(err)


Accessing error messages in strict mode
***************************************

In 2.0, `strict` mode was improved so that you can access all error messages for a schema (rather than failing early) by accessing a `ValidationError's` ``messages`` attribute.

.. code-block:: python
    :emphasize-lines: 6

    schema = BandMemberSchema(strict=True)

    try:
        result = schema.load({"email": "invalid"})
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
                raise UnmarshallingError("Password too short.")
            return val


    # In 2.0, _deserialize receives attr and data,
    # and a ValidationError is raised
    class PasswordField(fields.Field):
        def _deserialize(self, val, attr, data):
            if not len(val) >= 6:
                raise ValidationError("Password too short.")
            return val


To make a field compatible with both marshmallow 1.x and 2.x, you can pass `*args` and `**kwargs` to the signature.

.. code-block:: python

    class PasswordField(fields.Field):
        def _deserialize(self, val, *args, **kwargs):
            if not len(val) >= 6:
                raise ValidationError("Password too short.")
            return val

Custom Error Messages
*********************

Error messages can be customized at the `Field` class or instance level.


.. code-block:: python

    # 1.0
    field = fields.Number(error="You passed a bad number")

    # 2.0
    # Instance-level
    field = fields.Number(error_messages={"invalid": "You passed a bad number."})


    # Class-level
    class MyNumberField(fields.Number):
        default_error_messages = {"invalid": "You passed a bad number."}

Passing a string to ``required`` is deprecated.

.. code-block:: python

    # 1.0
    field = fields.Str(required="Missing required argument.")

    # 2.0
    field = fields.Str(error_messages={"required": "Missing required argument."})


Use ``OneOf`` instead of ``fields.Select``
******************************************

The `fields.Select` field is deprecated in favor of the newly-added `OneOf` validator.

.. code-block:: python

    from marshmallow import fields
    from marshmallow.validate import OneOf

    # 1.0
    fields.Select(["red", "blue"])

    # 2.0
    fields.Str(validate=OneOf(["red", "blue"]))

Accessing Context from Method fields
************************************

Use ``self.context`` to access a schema's context within a ``Method`` field.

.. code-block:: python

    class UserSchema(Schema):
        name = fields.String()
        likes_bikes = fields.Method("writes_about_bikes")

        def writes_about_bikes(self, user):
            return "bicycle" in self.context["blog"].title.lower()


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
        "foo": 42,
        "bar": 24,
        "baz": "invalid-integer",
        "qux": "invalid-float",
        "spam": "invalid-decimal",
        "eggs": "invalid-datetime",
        "email": "invalid-email",
        "homepage": "invalid-url",
        "nums": "invalid-list",
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

    fields.Date().deserialize("")
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


    user = User(email="monty@python.org", name="Monty Python")

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
                raise MarshallingError("Password must be greater than 6 characters.")
            return str(value).strip()

        # Similarly, you can override the _deserialize method

Another major change in 1.0 is that multiple validation errors can be stored for a single field. The ``errors`` dictionary returned by :meth:`Schema.dump` and :meth:`Schema.load` is a list of error messages keyed by field name.


.. code-block:: python

    from marshmallow import Schema, fields, ValidationError


    def must_have_number(val):
        if not any(ch.isdigit() for ch in val):
            raise ValidationError("Value must have an number.")


    def validate_length(val):
        if len(val) < 8:
            raise ValidationError("Value must have 8 or more characters.")


    class ValidatingSchema(Schema):
        password = fields.String(validate=[must_have_number, validate_length])


    result, errors = ValidatingSchema().load({"password": "secure"})
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
