Why marshmallow?
================

The Python ecosystem has many great libraries for data formatting and schema validation.

In fact, marshmallow was influenced by a number of these libraries. marshmallow is inspired by `Django REST Framework`_, `Flask-RESTful`_, and `colander <https://docs.pylonsproject.org/projects/colander/en/latest/>`_. It borrows a number of implementation and design ideas from these libraries to create a flexible and productive solution for marshalling, unmarshalling, and validating data.

Here are just a few reasons why you might use marshmallow.

Agnostic
--------

marshmallow makes no assumption about web frameworks or database layers. It will work with just about any ORM, ODM, or no ORM at all. This gives you the freedom to choose the components that fit your application's needs without having to change your data formatting code. If you wish, you can build integration layers to make marshmallow work more closely with your frameworks and libraries of choice (for examples, see `Flask-Marshmallow <https://github.com/marshmallow-code/flask-marshmallow>`_ and `Django REST Marshmallow <https://github.com/marshmallow-code/django-rest-marshmallow>`_).

Concise, familiar syntax
------------------------

If you have used `Django REST Framework`_ or  `WTForms <https://wtforms.readthedocs.io/en/stable/>`_, marshmallow's :class:`Schema <marshmallow.Schema>` syntax will feel familiar to you. Class-level field attributes define the schema for formatting your data. Configuration is added using the `class Meta <marshmallow.Schema.Meta>` paradigm. Configuration options can be overridden at application runtime by passing arguments to the `Schema <marshmallow.Schema>` constructor. The :meth:`dump <marshmallow.Schema.dump>` and :meth:`load <marshmallow.Schema.load>` methods are used for serialization and deserialization (of course!).

Class-based schemas allow for code reuse and configuration
----------------------------------------------------------

Unlike `Flask-RESTful`_, which uses dictionaries to define output schemas, marshmallow uses classes. This allows for easy code reuse and configuration. It also enables patterns for configuring and extending schemas, such as adding :doc:`post-processing and error handling behavior <extending/index>`.

Consistency meets flexibility
-----------------------------

marshmallow makes it easy to modify a schema's output at application runtime. A single :class:`Schema <marshmallow.Schema>` can produce multiple output formats while keeping the individual field outputs consistent.

As an example, you might have a JSON endpoint for retrieving all information about a video game's state. You then add a low-latency endpoint that only returns a minimal subset of information about game state. Both endpoints can be handled by the same `Schema <marshmallow.Schema>`.

.. code-block:: python

    class GameStateSchema(Schema):
        _id = fields.UUID(required=True)
        score = fields.Nested(ScoreSchema)
        players = fields.List(fields.Nested(PlayerSchema))
        last_changed = fields.DateTime(format="rfc")


    # Serializes full game state
    full_serializer = GameStateSchema()
    # Serializes a subset of information, for a low-latency endpoint
    summary_serializer = GameStateSchema(only=("_id", "last_changed"))
    # Also filter the fields when serializing multiple games
    gamelist_serializer = GameStateSchema(
        many=True, only=("_id", "players", "last_changed")
    )

In this example, a single schema produced three different outputs! The dynamic nature of a :class:`Schema` leads to **less code** and **more consistent formatting**.

.. _Django REST Framework: https://www.django-rest-framework.org/
.. _Flask-RESTful: https://flask-restful.readthedocs.io/

Advanced schema nesting
-----------------------

Most serialization libraries provide some means for nesting schemas within each other, but they often fail to meet common use cases in clean way. marshmallow aims to fill these gaps by adding a few nice features for :doc:`nesting schemas <nesting>`:

- You can specify which :ref:`subset of fields <specifying-nested-fields>` to include on nested schemas.
- :ref:`Two-way nesting <two-way-nesting>`. Two different schemas can nest each other.
- :ref:`Self-nesting <self-nesting>`. A schema can be nested within itself.
