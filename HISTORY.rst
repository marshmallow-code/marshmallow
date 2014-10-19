Changelog
---------

1.0.0-a (2014-10-19)
++++++++++++++++++++

Major reworking and simplification of the public API, centered around support for deserialization, improved validation, and a less stateful ``Schema`` class.

* Rename ``Serializer`` to ``Schema``.
* Support for deserialization.
* Use the ``Schema.dump`` and ``Schema.load`` methods for serializing and deserializing, respectively.
* *Backwards-incompatible*: Remove ``Serializer.json`` and ``Serializer.to_json``. Use ``Schema.dumps`` instead.
* Reworked fields interface.
* *Backwards-incompatible*: ``Field`` classes implement ``_serialize`` and ``_deserialize`` methods. ``serialize`` and ``deserialize`` comprise the public API for a ``Field``. ``Field.format`` and ``Field.output`` have been removed.
* Add ``exceptions.ForcedError`` which allows errors to be raised during serialization (instead of storing errors in the ``errors`` dict).
* *Backwards-incompatible*: ``DateTime`` field serializes to ISO8601 format by default (instead of RFC822).
* *Backwards-incompatible*: Remove `Serializer.factory` method. It is no longer necessary with the ``dump`` method.
* *Backwards-incompatible*: Allow nesting a serializer within itself recursively. Use ``exclude`` or ``only`` to prevent infinite recursion.
* *Backwards-incompatible*: Multiple errors can be stored for a single field. The errors dictionary returned by ``load`` and ``dump`` have lists of error messages keyed by field name.
* Remove ``validated`` decorator. Validation occurs within ``Field`` methods.
* ``Function`` field raises a ``ValueError`` if an uncallable object is passed to its constructor.
* ``Nested`` fields inherit context from their parent.
* Add ``Schema.preprocessor`` and ``Schema.validator`` decorators for registering preprocessing and schema-level validation functions respectively.
* Custom error messages can be specified by raising a ``ValidationError`` within a validation function.
* Extra keyword arguments passed to a Field are stored as metadata.
* Fix ordering of field output.
* Fix behavior of the ``required`` parameter on ``Nested`` fields.
* Fix serializing keyed tuple types (e.g. ``namedtuple``) with ``class Meta`` options.
* Fix default value for ``Fixed`` and ``Price`` fields.
* Fix serialization of binary strings.
* ``Schemas`` can inherit fields from non-``Schema`` base classes (e.g. mixins). Also, fields are inherited according to the MRO (rather than recursing over base classes). Thanks Josh Carp.

0.7.0 (2014-06-22)
++++++++++++++++++

* Add ``Serializer.error_handler`` decorator that registers a custom error handler.
* Add ``Serializer.data_handler`` decorator that registers data post-processing callbacks.
* *Backwards-incompatible*: ``process_data`` method is deprecated. Use the ``data_handler`` decorator instead.
* Fix bug that raised error when passing ``extra`` data together with ``many=True``. Thanks Joe Alcorn for reporting.
* If ``required=True`` validation is violated for a given ``Field``, it will raise an error message that is different from the message specified by the ``error`` argument. Thanks Anders Steinlein.
* More generic error message raised when required field is missing.
* ``validated`` decorator should only wrap a ``Field`` class's ``output`` method.

0.6.0 (2014-06-03)
++++++++++++++++++

* Fix bug in serializing keyed tuple types, e.g. ``namedtuple`` and ``KeyedTuple``.
* Nested field can load a serializer by its class name as a string. This makes it easier to implement 2-way nesting.
* Make Serializer.data override-able.

0.5.5 (2014-05-02)
++++++++++++++++++

* Add ``Serializer.factory`` for creating a factory function that returns a Serializer instance.
* ``MarshallingError`` stores its underlying exception as an instance variable. This is useful for inspecting errors.
* ``fields.Select`` is aliased to ``fields.Enum``.
* Add ``fields.__all__`` and ``marshmallow.__all__`` so that the modules can be more easily extended.
* Expose ``Serializer.OPTIONS_CLASS`` as a class variable so that options defaults can be overridden.
* Add ``Serializer.process_data`` hook that allows subclasses to manipulate the final output data.

0.5.4 (2014-04-17)
++++++++++++++++++

* Add ``json_module`` class Meta option.
* Add ``required`` option to fields . Thanks `@DeaconDesperado <http://github.com/DeaconDesperado>`_.
* Tested on Python 3.4 and PyPy.

0.5.3 (2014-03-02)
++++++++++++++++++

* Fix ``Integer`` field default. It is now ``0`` instead of ``0.0``. Thanks `@kalasjocke <http://github.com/kalasjocke>`_.
* Add ``context`` param to ``Serializer``. Allows accessing arbitrary objects in ``Function`` and ``Method`` fields.
* ``Function`` and ``Method`` fields raise ``MarshallingError`` if their argument is uncallable.


0.5.2 (2014-02-10)
++++++++++++++++++

* Enable custom field validation via the ``validate`` parameter.
* Add ``utils.from_rfc`` for parsing RFC datestring to Python datetime object.

0.5.1 (2014-02-02)
++++++++++++++++++

* Avoid unnecessary attribute access in ``utils.to_marshallable_type`` for improved performance.
* Fix RFC822 formatting for localized datetimes.

0.5.0 (2013-12-29)
++++++++++++++++++

* Can customize validation error messages by passing the ``error`` parameter to a field.
* *Backwards-incompatible*: Rename ``fields.NumberField`` -> ``fields.Number``.
* Add ``fields.Select``. Thanks @ecarreras.
* Support nesting a Serializer within itself by passing ``"self"`` into ``fields.Nested`` (only up to depth=1).
* *Backwards-incompatible*: No implicit serializing of collections. Must set ``many=True`` if serializing to a list. This ensures that marshmallow handles singular objects correctly, even if they are iterable.
* If Nested field ``only`` parameter is a field name, only return a single value for the nested object (instead of a dict) or a flat list of values.
* Improved performance and stability.

0.4.1 (2013-12-01)
++++++++++++++++++

* An object's ``__marshallable__`` method, if defined, takes precedence over ``__getitem__``.
* Generator expressions can be passed to a serializer.
* Better support for serializing list-like collections (e.g. ORM querysets).
* Other minor bugfixes.

0.4.0 (2013-11-24)
++++++++++++++++++

* Add ``additional`` `class Meta` option.
* Add ``dateformat`` `class Meta` option.
* Support for serializing UUID, date, time, and timedelta objects.
* Remove ``Serializer.to_data`` method. Just use ``Serialize.data`` property.
* String field defaults to empty string instead of ``None``.
* *Backwards-incompatible*: ``isoformat`` and ``rfcformat`` functions moved to utils.py.
* *Backwards-incompatible*: Validation functions moved to validate.py.
* *Backwards-incompatible*: Remove types.py.
* Reorder parameters to ``DateTime`` field (first parameter is dateformat).
* Ensure that ``to_json`` returns bytestrings.
* Fix bug with including an object property in ``fields`` Meta option.
* Fix bug with passing ``None`` to a serializer.

0.3.1 (2013-11-16)
++++++++++++++++++

* Fix bug with serializing dictionaries.
* Fix error raised when serializing empty list.
* Add ``only`` and ``exclude`` parameters to Serializer constructor.
* Add ``strict`` parameter and option: causes Serializer to raise an error if invalid data are passed in, rather than storing errors.
* Updated Flask + SQLA example in docs.

0.3.0 (2013-11-14)
++++++++++++++++++

* Declaring Serializers just got easier. The *class Meta* paradigm allows you to specify fields more concisely. Can specify ``fields`` and ``exclude`` options.
* Allow date formats to be changed by passing ``format`` parameter to ``DateTime`` field constructor. Can either be ``"rfc"`` (default), ``"iso"``, or a date format string.
* More useful error message when declaring fields as classes (instead of an instance, which is the correct usage).
* Rename MarshallingException -> MarshallingError.
* Rename marshmallow.core -> marshmallow.serializer.

0.2.1 (2013-11-12)
++++++++++++++++++

* Allow prefixing field names.
* Fix storing errors on Nested Serializers.
* Python 2.6 support.

0.2.0 (2013-11-11)
++++++++++++++++++

* Field-level validation.
* Add ``fields.Method``.
* Add ``fields.Function``.
* Allow binding of extra data to a serialized object by passing the ``extra`` param when initializing a ``Serializer``.
* Add ``relative`` paramater to ``fields.Url`` that allows for relative URLs.

0.1.0 (2013-11-10)
++++++++++++++++++

* First release.
