**marshmallow** is an ORM/ODM/framework-agnostic library for converting complex datatypes, such as objects, to and from native Python datatypes. The serialized objects can then be rendered to standard formats such as JSON for use in an HTTP API.

.. code-block:: python

    from datetime import datetime
    from marshmallow import Serializer, fields, pprint

    # A "model"
    class Person(object):
        def __init__(self, name):
            self.name = name
            self.date_born = datetime.now()

    # A serializer
    class PersonSerializer(Serializer):
        name = fields.String()
        date_born = fields.DateTime()

    person = Person("Guido van Rossum")
    serializer = PersonSerializer()
    result, errors = serializer.dump(person)
    pprint(result)
    # {"name": "Guido van Rossum", "date_born": "2014-08-17T14:42:12.479650+00:00"}


Get It Now
==========

.. code-block:: bash

    $ pip install -U marshmallow


Ready to get started? Go on to the :ref:`Quickstart tutorial <quickstart>` or check out some :ref:`Examples <examples>`.
