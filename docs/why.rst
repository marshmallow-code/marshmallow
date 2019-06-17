Why marshmallow?
================

The Python ecosystem has many great libraries for data formatting and schema validation.

In fact, marshmallow was influenced by a number of these libraries. Marshmallow is inspired by `Django REST Framework`_, `Flask-RESTful`_, and `colander <https://docs.pylonsproject.org/projects/colander/en/latest/>`_. It borrows a number of implementation and design ideas from these libraries to create a flexible and productive solution for marshalling, unmarshalling, and validating data.

Here are just a few reasons why you might use marshmallow.

Agnostic.
---------

Marshmallow makes no assumption about web frameworks or database layers. It will work with just about any ORM, ODM, or no ORM at all. This gives you the freedom to choose the components that fit your application's needs without having to change your data formatting code. If you wish, you can build integration layers to make marshmallow work more closely with your frameworks and libraries of choice (for examples, see `Flask-Marshmallow <https://github.com/marshmallow-code/flask-marshmallow>`_ and `Django REST Marshmallow <https://github.com/marshmallow-code/django-rest-marshmallow>`_).

Concise, familiar syntax.
-------------------------

If you have used `Django REST Framework`_ or  `WTForms <https://wtforms.readthedocs.io/en/stable/>`_, marshmallow's :class:`Schema <marshmallow.Schema>` syntax will feel familiar to you. Class-level field attributes define the schema for formatting your data. Configuration is added using the ``class Meta`` paradigm. Configuration options can be overriden at application runtime by passing arguments to the `Schema <marshmallow.Schema>` constructor. The :meth:`dump <marshmallow.Schema.dump>` and :meth:`load <marshmallow.Schema.load>` methods are used for serialization and deserialization (of course!).

Class-based schemas allow for code reuse and configuration.
-----------------------------------------------------------

Unlike `Flask-RESTful`_, which uses dictionaries to define output schemas, marshmallow uses classes. This allows for easy code reuse and configuration. It also allows for powerful means for configuring and extending schemas, such as adding :doc:`post-processing and error handling behavior <extending>`.

Consistency meets flexibility.
------------------------------

Marshmallow makes it easy to modify a schema's output at application runtime. A single :class:`Schema <marshmallow.Schema>` can produce multiple outputs formats while keeping the individual field outputs consistent.

As an example, you might have a JSON endpoint for retrieving all information about a video game's state. You then add a low-latency endpoint that only returns a minimal subset of information about game state. Both endpoints can be handled by the same `Schema <marshmallow.Schema>`.

.. code-block:: python

    class GameStateSchema(Schema):
        _id = fields.UUID(required=True)
        players = fields.Nested(PlayerSchema, many=True)
        score = fields.Nested(ScoreSchema)
        last_changed = fields.DateTime(format="rfc")

        class Meta:
            additional = ("title", "date_created", "type", "is_active")


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


Context-aware serialization.
----------------------------

Marshmallow schemas can modify their output based on the context in which they are used. Field objects have access to a ``context`` dictionary that can be changed at runtime.

Here's a simple example that shows how a `Schema <marshmallow.Schema>` can anonymize a person's name when a boolean is set on the context.

.. code-block:: python

    class PersonSchema(Schema):
        id = fields.Integer()
        name = fields.Method("get_name")

        def get_name(self, person, context):
            if context.get("anonymize"):
                return "<anonymized>"
            return person.name


    person = Person(name="Monty")
    schema = PersonSchema()
    schema.dump(person)  # {'id': 143, 'name': 'Monty'}

    # In a different context, anonymize the name
    schema.context["anonymize"] = True
    schema.dump(person)  # {'id': 143, 'name': '<anonymized>'}


.. seealso::

    See the relevant section of the :ref:`usage guide <adding-context>` to learn more about context-aware serialization.

Advanced schema nesting.
------------------------

Most serialization libraries provide some means for nesting schemas within each other, but they often fail to meet common use cases in clean way. Marshmallow aims to fill these gaps by adding a few nice features for :doc:`nesting schemas <nesting>`:

- You can specify which :ref:`subset of fields <specifying-nested-fields>` to include on nested schemas.
- :ref:`Two-way nesting <two-way-nesting>`. Two different schemas can nest each other.
- :ref:`Self-nesting <self-nesting>`. A schema can be nested within itself.
