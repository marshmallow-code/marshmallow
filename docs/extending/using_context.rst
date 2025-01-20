Using context
=============

.. warning::

    The ``context`` attribute is deprecated and will be removed in marshmallow 4.
    Use `contextvars.ContextVar` for passing context to fields, pre-/post-processing methods, and validators instead.
    marshmallow 4 will also provide an `experimental helper API <https://marshmallow.readthedocs.io/en/latest/marshmallow.experimental.context.html>`_
    for using context.

The ``context`` attribute of a `Schema <marshmallow.Schema>` is a general-purpose store for extra information that may be needed for (de)serialization. 
It may be used in both ``Schema`` and ``Field`` methods.

.. code-block:: python

    schema = UserSchema()
    # Make current HTTP request available to
    # custom fields, schema methods, schema validators, etc.
    schema.context["request"] = request
    schema.dump(user)
