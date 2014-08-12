********************************************
marshmallow: simplified object serialization
********************************************

.. image:: https://badge.fury.io/py/marshmallow.png
    :target: http://badge.fury.io/py/marshmallow
    :alt: Latest version

.. image:: https://travis-ci.org/sloria/marshmallow.png?branch=master
    :target: https://travis-ci.org/sloria/marshmallow
    :alt: Travis-CI

Homepage: http://marshmallow.rtfd.org/


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
    # {"name": "Guido van Rossum", "date_born": "Sun, 10 Nov 2013 14:24:50 -0000"}



Get It Now
==========

::

    $ pip install -U marshmallow


Documentation
=============

Full documentation is available at http://marshmallow.rtfd.org/ .


Requirements
============

- Python >= 2.6 or >= 3.3

marshmallow has no external dependencies outside of the Python standard library.


License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/marshmallow/blob/master/LICENSE>`_ file for more details.
