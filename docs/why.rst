.. module:: marshmallow

Why marshmallow?
================

The Python ecosystem has many great libraries for data formatting and schema validation.

In fact, marshmallow was influenced by a number of these libraries. Marshmallow is inspired by `Django REST Framework`_, `Flask-RESTful`_, and `colander <http://docs.pylonsproject.org/projects/colander/en/latest/>`_. It borrows a number of implementation and design ideas from these libraries to create a flexible and productive solution for marshalling and unmarshalling Python objects.

Here are just a few reasons why you might use marshmallow.

Agnostic.
---------

Marshmallow makes no assumption about web frameworks or database layers. It will work with just about any ORM, ODM, or no ORM at all. This gives you the freedom to choose the components that fit your application's needs without having to change your data formatting code. If you wish, you can build integration layers to make marshmallow work more closely with your frameworks and libraries of choice.

Terse, familiar syntax.
-----------------------

If you have used `Django REST Framework`_ or  `WTForms <http://wtforms.simplecodes.com/docs/1.0.3/>`_, marshmallow's :class:`Serializer` syntax will feel familiar to you. Class-level field attributes define the schema for formatting your data. Configuration is added using the :ref:`class Meta <meta_options>` paradigm. Configuration options can be overriden at application runtime by passing arguments to the :class:`Serializer` constructor. The :meth:`dump <Serializer.dump>` and :meth:`load <Serialier.load>` methods are used for serialization and deserialization (of course!).

Class-based schemas allow for inheritance and configuration.
------------------------------------------------------------

Unlike `Flask-RESTful`_, which uses dictionaries to define output schemas, marshmallow uses classes. This allows for easy code reuse and configuration. It also allows for powerful means for configuring and extending serializers, such as adding :ref:`post-processing and error handling behavior <extending>`.

Flexibility.
------------

Marshmallow's makes it easy to modify a serializer's output at runtime. A single :class:`Serializer` class can produce multiple outputs formats. Why might that be useful?

As an example, you might have a JSON endpoint for retrieving all information about a video game's state. You then add a low-latency endpoint that only returns a minimal subset of information about game state. Both endpoints could be handled by the same :class:`Serializer`.

.. code-block:: python

    class GameStateSerializer(Serializer):
        _id = fields.UUID(required=True)
        players = fields.Nested(PlayerSerializer, many=True)
        score = fields.Nested(ScoreSerializer)
        last_changed = fields.DateTime(format='rfc')

        class Meta:
            additional = ('title', 'date_created', 'type', 'is_active')

    # Serializes full game state
    full_serializer = GameStateSerializer()
    # Serializes a subset of information, for a low-latency endpoint
    summary_serializer = GameStateSerializer(only=('_id', 'last_changed'))
    # Also filter the fields when serializing multiple games
    gamelist_serializer = GameStateSerializer(many=True,
                                               only=('_id', 'players', 'last_changed'))

In this example, a single serializer class produced three different outputs! The dynamic nature of a :class:`Serializer` schema keeps your code `DRY <https://en.wikipedia.org/wiki/DRY>`_ and flexible.

.. _Django REST Framework: http://www.django-rest-framework.org/
.. _Flask-RESTful: http://flask-restful.readthedocs.org/
