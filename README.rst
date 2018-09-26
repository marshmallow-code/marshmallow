********************************************
marshmallow: simplified object serialization
********************************************

.. image:: https://badge.fury.io/py/marshmallow.svg
    :target: http://badge.fury.io/py/marshmallow
    :alt: Latest version

.. image:: https://travis-ci.org/marshmallow-code/marshmallow.svg?branch=pypi
    :target: https://travis-ci.org/marshmallow-code/marshmallow
    :alt: Travis-CI

.. image:: https://readthedocs.org/projects/marshmallow/badge/
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
    pprint(result, indent=2)
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

    $ pip install -U marshmallow --pre


Documentation
=============

Full documentation is available at http://marshmallow.readthedocs.io/ .

Requirements
============

- Python >= 2.7 or >= 3.5

marshmallow has no external dependencies outside of the Python standard library, although `python-dateutil <https://pypi.python.org/pypi/python-dateutil>`_ is recommended for robust datetime deserialization.


Ecosystem
=========

A list of marshmallow-related libraries can be found at the GitHub wiki here:

https://github.com/marshmallow-code/marshmallow/wiki/Ecosystem

Credits
=======

Contributors
------------

This project exists thanks to all the people who contribute.

You're highly encouraged to participate in marshmallow's development.
Check out the `Contributing Guidelines <https://marshmallow.readthedocs.io/en/latest/contributing.html>`_ to see
how you can help.

Thank you to all who have already contributed to marshmallow!

.. image:: https://opencollective.com/marshmallow/contributors.svg?width=890&button=false
    :target: https://marshmallow.readthedocs.io/en/latest/authors.html
    :alt: Contributors

Backers
-------

If you find marshmallow useful, please consider supporting the team with
a donation. Your donation helps move marshmallow forward.

Thank you to all our backers! [`Become a backer`_]

.. _`Become a backer`: https://opencollective.com/marshmallow#backer

.. image:: https://opencollective.com/marshmallow/backers.svg?width=890
    :target: https://opencollective.com/marshmallow#backers
    :alt: Backers

Sponsors
--------

Support this project by becoming a sponsor (or ask your company to support this project by becoming a sponsor).
Your logo will show up here with a link to your website. [`Become a sponsor`_]

.. _`Become a sponsor`: https://opencollective.com/marshmallow#sponsor

.. image:: https://opencollective.com/marshmallow/sponsor/0/avatar.svg
    :target: https://opencollective.com/marshmallow/sponsor/0/website
    :alt: Sponsors


Professional support
====================

Professionally-supported marshmallow is now available through the
`Tidelift Subscription <https://tidelift.com/subscription/pkg/pypi-marshmallow?utm_source=pypi-marshmallow&utm_medium=readme>`_.

Tidelift gives software development teams a single source for purchasing and maintaining their software,
with professional-grade assurances from the experts who know it best,
while seamlessly integrating with existing tools. [`Get professional support`_]

.. _`Get professional support`: https://tidelift.com/subscription/pkg/pypi-marshmallow?utm_source=pypi-marshmallow&utm_medium=readme

.. image:: https://user-images.githubusercontent.com/2379650/45126032-50b69880-b13f-11e8-9c2c-abd16c433495.png
    :target: https://tidelift.com/subscription/pkg/pypi-marshmallow?utm_source=pypi-marshmallow&utm_medium=readme
    :alt: Get supported marshmallow with Tidelift

Project Links
=============

- Docs: http://marshmallow.readthedocs.io/
- Changelog: http://marshmallow.readthedocs.io/en/latest/changelog.html
- PyPI: https://pypi.python.org/pypi/marshmallow
- Issues: https://github.com/marshmallow-code/marshmallow/issues
- Donate: https://opencollective.com/marshmallow

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/marshmallow-code/marshmallow/blob/pypi/LICENSE>`_ file for more details.
