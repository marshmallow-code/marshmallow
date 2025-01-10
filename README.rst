********************************************
marshmallow: simplified object serialization
********************************************

|pypi| |build-status| |pre-commit| |docs|

.. |pypi| image:: https://badgen.net/pypi/v/marshmallow
    :target: https://pypi.org/project/marshmallow/
    :alt: Latest version

.. |build-status| image:: https://github.com/marshmallow-code/marshmallow/actions/workflows/build-release.yml/badge.svg
    :target: https://github.com/marshmallow-code/marshmallow/actions/workflows/build-release.yml
    :alt: Build status

.. |pre-commit| image:: https://results.pre-commit.ci/badge/github/marshmallow-code/marshmallow/dev.svg
   :target: https://results.pre-commit.ci/latest/github/marshmallow-code/marshmallow/dev
   :alt: pre-commit.ci status

.. |docs| image:: https://readthedocs.org/projects/marshmallow/badge/
   :target: https://marshmallow.readthedocs.io/
   :alt: Documentation

.. start elevator-pitch

**marshmallow** is an ORM/ODM/framework-agnostic library for converting complex datatypes, such as objects, to and from native Python datatypes.

.. code-block:: python

    from datetime import date
    from pprint import pprint

    from marshmallow import Schema, fields


    class ArtistSchema(Schema):
        name = fields.Str()


    class AlbumSchema(Schema):
        title = fields.Str()
        release_date = fields.Date()
        artist = fields.Nested(ArtistSchema())


    bowie = dict(name="David Bowie")
    album = dict(artist=bowie, title="Hunky Dory", release_date=date(1971, 12, 17))

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

Get it now
==========

.. code-block:: shell-session

    $ pip install -U marshmallow

.. end elevator-pitch

Documentation
=============

Full documentation is available at https://marshmallow.readthedocs.io/ .

Ecosystem
=========

A list of marshmallow-related libraries can be found at the GitHub wiki here:

https://github.com/marshmallow-code/marshmallow/wiki/Ecosystem

Credits
=======

Contributors
------------

This project exists thanks to all the people who contribute.

**You're highly encouraged to participate in marshmallow's development.**
Check out the `Contributing Guidelines <https://marshmallow.readthedocs.io/en/latest/contributing.html>`_ to see how you can help.

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

.. start sponsors

marshmallow is sponsored by `Route4Me <https://route4me.com>`_.

.. image:: https://github.com/user-attachments/assets/018c2e23-032e-4a11-98da-8b6dc25b9054
    :target: https://route4me.com
    :alt: Routing Planner

Support this project by becoming a sponsor (or ask your company to support this project by becoming a sponsor).
Your logo will be displayed here with a link to your website. [`Become a sponsor`_]

.. _`Become a sponsor`: https://opencollective.com/marshmallow#sponsor

.. end sponsors

Professional Support
====================

Professionally-supported marshmallow is now available through the
`Tidelift Subscription <https://tidelift.com/subscription/pkg/pypi-marshmallow?utm_source=pypi-marshmallow&utm_medium=readme>`_.

Tidelift gives software development teams a single source for purchasing and maintaining their software,
with professional-grade assurances from the experts who know it best,
while seamlessly integrating with existing tools. [`Get professional support`_]

.. _`Get professional support`: https://tidelift.com/subscription/pkg/pypi-marshmallow?utm_source=marshmallow&utm_medium=referral&utm_campaign=github

.. image:: https://user-images.githubusercontent.com/2379650/45126032-50b69880-b13f-11e8-9c2c-abd16c433495.png
    :target: https://tidelift.com/subscription/pkg/pypi-marshmallow?utm_source=pypi-marshmallow&utm_medium=readme
    :alt: Get supported marshmallow with Tidelift


Project Links
=============

- Docs: https://marshmallow.readthedocs.io/
- Changelog: https://marshmallow.readthedocs.io/en/latest/changelog.html
- Contributing Guidelines: https://marshmallow.readthedocs.io/en/latest/contributing.html
- PyPI: https://pypi.org/project/marshmallow/
- Issues: https://github.com/marshmallow-code/marshmallow/issues
- Donate: https://opencollective.com/marshmallow

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/marshmallow-code/marshmallow/blob/dev/LICENSE>`_ file for more details.
