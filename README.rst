********************************************
marshmallow: simplified object serialization
********************************************

.. image:: https://badge.fury.io/py/marshmallow.svg
    :target: http://badge.fury.io/py/marshmallow
    :alt: Latest version

.. image:: https://travis-ci.org/marshmallow-code/marshmallow.svg?branch=pypi
    :target: https://travis-ci.org/marshmallow-code/marshmallow
    :alt: Travis-CI

.. image:: https://readthedocs.org/projects/flask-marshmallow/badge/
   :target: http://marshmallow.readthedocs.io/
   :alt: Documentation

**marshmallow** is an ORM/ODM/framework-agnostic library for converting complex datatypes, such as objects, to and from native Python datatypes.

.. code-block:: python

    from datetime import date
    from marshmallow import Schema, fields, pprint

    class ArtistSchema(Schema):
        name = fields.Str()

    class AlbumSchema(Schema):
        title = fields.Str()
        release_date = fields.Date()
        artist = fields.Nested(ArtistSchema())

    bowie = dict(name='David Bowie')
    album = dict(artist=bowie, title='Hunky Dory', release_date=date(1971, 12, 17))

    schema = AlbumSchema()
    result = schema.dump(album)
    pprint(result.data, indent=2)
    # { 'artist': {'name': 'David Bowie'},
    #   'release_date': '1971-12-17',
    #   'title': 'Hunky Dory'}


In short, marshmallow schemas can be used to:

- **Validate** input data.
- **Deserialize** input data to app-level objects.
- **Serialize** app-level objects to primitive Python types. The serialized objects can then be rendered to standard formats such as JSON for use in an HTTP API.

Get It Now
==========

::

    $ pip install -U marshmallow


Documentation
=============

Full documentation is available at http://marshmallow.readthedocs.io/ .

Requirements
============

- Python >= 2.6 or >= 3.3

marshmallow has no external dependencies outside of the Python standard library, although `python-dateutil <https://pypi.python.org/pypi/python-dateutil>`_ is recommended for robust datetime deserialization.


Ecosystem
=========

A list of marshmallow-related libraries can be found at the GitHub wiki here:

https://github.com/marshmallow-code/marshmallow/wiki/Ecosystem

Project Links
=============

- Docs: http://marshmallow.readthedocs.io/
- Changelog: http://marshmallow.readthedocs.io/en/latest/changelog.html
- PyPI: https://pypi.python.org/pypi/marshmallow
- Issues: https://github.com/marshmallow-code/marshmallow/issues

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/marshmallow-code/marshmallow/blob/pypi/LICENSE>`_ file for more details.
