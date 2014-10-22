**marshmallow** is an ORM/ODM/framework-agnostic library for converting complex datatypes, such as objects, to and from native Python datatypes.

.. code-block:: python

    from datetime import datetime
    from marshmallow import Schema, fields, pprint

    # A "model"
    class Person(object):
        def __init__(self, name):
            self.name = name
            self.date_born = datetime.now()

    # A serializer schema
    class PersonSchema(Schema):
        name = fields.String()
        date_born = fields.DateTime()

    person = Person("Guido van Rossum")
    schema = PersonSchema()
    result = schema.dump(person)
    pprint(result.data)
    # {"name": "Guido van Rossum", "date_born": "2014-08-17T14:42:12.479650+00:00"}


In short, marshmallow schemas are used to:

- **Validate** input data.
- **Deserialize** input data to app-level objects.
- **Serialize** app-level objects to primitive Python types. The serialized objects can then be rendered to standard formats such as JSON for use in an HTTP API.


Get It Now
==========

.. code-block:: bash

    $ pip install -U marshmallow==1.0.0-a


Ready to get started? Go on to the :ref:`Quickstart tutorial <quickstart>` or check out some :ref:`Examples <examples>`.
