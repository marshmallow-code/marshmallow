.. _install:

Installation
============

**marshmallow** requires Python >= 2.7 or >= 3.4. It has no external dependencies other than the Python standard library.

.. note::

    The `python-dateutil <https://pypi.python.org/pypi/python-dateutil>`_ package is not a hard dependency, but it is recommended for robust datetime deserialization.

    ::

        $ pip install 'python-dateutil>=2.7.0'

Installing/Upgrading from the PyPI
----------------------------------

To install the latest stable version from the PyPI:

::

    $ pip install -U marshmallow

To install the latest pre-release version from the PyPI:

::

    $ pip install -U marshmallow --pre


To install marshmallow with the recommended soft dependencies:

::

    $ pip install -U marshmallow[reco]

Get the Bleeding Edge Version
-----------------------------

To get the latest development version of marshmallow, run

::

    $ pip install -U git+https://github.com/marshmallow-code/marshmallow.git@dev


.. seealso::

    Need help upgrading to newer releases? See the :doc:`Upgrading to Newer Releases <upgrading>` page.
