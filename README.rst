********************************************
marshmallow: Simplified Object Serialization
********************************************

.. image:: https://badge.fury.io/py/marshmallow.png
    :target: http://badge.fury.io/py/marshmallow
    :alt: Latest version

.. image:: https://travis-ci.org/sloria/marshmallow.png?branch=master
    :target: https://travis-ci.org/sloria/marshmallow
    :alt: Travis-CI

Homepage: http://marshmallow.readthedocs.org/


**marshmallow** is an ORM/ODM/framework-agnostic library for converting complex datatypes, such as objects, into native Python datatypes. The serialized objects can then be rendered to standard formats such as JSON for use in a REST API.

.. code-block:: python

    from datetime import datetime
    from marshmallow import Serializer, fields

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
    serialized = PersonSerializer(person)
    serialized.data
    # {"name": "Guido van Rossum", "date_born": "Sun, 10 Nov 2013 14:24:50 -0000"}


Get It Now
----------

.. code-block:: bash

    $ pip install -U marshmallow


Documentation
=============

Full documentation is available at http://marshmallow.readthedocs.org/ .


Requirements
============

- Python >= 2.7 or >= 3.3


License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/marshmallow/blob/master/LICENSE>`_ file for more details.
