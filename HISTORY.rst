Changelog
---------

0.3.0 (unreleased)
++++++++++++++++++

* *class Meta* paradigm allows you to specify fields more concisely.
* More useful error message when declaring fields as classes (instead of instance, which is correct).

0.2.1 (2013-11-12)
++++++++++++++++++

* Allow prefixing field names.
* Fix storing of errors on Nested Serializers.
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
