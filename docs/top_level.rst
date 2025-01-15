Top-level API
=============

.. automodule:: marshmallow
   :members:
   :autosummary:
   :exclude-members: OPTIONS_CLASS

.. Can't use :autodata: here due to Sphinx bug: https://github.com/sphinx-doc/sphinx/issues/6495
.. data:: missing

   Singleton value that indicates that a field's value is missing from input
   dict passed to `Schema.load <marshmallow.Schema.load>`. If the field's value is not required,
   its ``default`` value is used.

Constants for ``unknown``
-------------------------

.. seealso:: :ref:`unknown`

.. data:: EXCLUDE

   Indicates that fields that are not explicitly declared on a schema should be
   excluded from the deserialized result.


.. data:: INCLUDE

   Indicates that fields that are not explicitly declared on a schema should be
   included from the deserialized result.

.. data:: RAISE

   Indicates that fields that are not explicitly declared on a schema should
   result in an error.
