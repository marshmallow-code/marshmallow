Contributing Guidelines
=======================

In General
----------

- `PEP 8`_, when sensible.
- Test ruthlessly. Write docs for new features.
- Even more important than Test-Driven Development--*Human-Driven Development*.

.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/

In Particular
-------------

Questions, Feature Requests, Bug Reports, and Feedback. . .
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

. . .should all be reported on the `Github Issue Tracker`_ .

.. _`Github Issue Tracker`: https://github.com/sloria/marshmallow/issues?state=open

Setting Up for Local Development
++++++++++++++++++++++++++++++++

1. Fork marshmallow_ on Github. ::

    $ git clone https://github.com/sloria/marshmallow.git
    $ cd marshmallow

2. Install development requirements. It is highly recommended that you use a virtualenv. ::

    # After activating your virtualenv
    $ pip install -r dev-requirements.txt

3. Install marshmallow in develop mode. ::

   $ python setup.py develop

Git Branch Structure
++++++++++++++++++++

Marshmallow loosely follows Vincent Driessen's `Successful Git Branching Model <http://http://nvie.com/posts/a-successful-git-branching-model/>`_ . In practice, the following branch conventions are used:

``dev``
    The next release branch.

``master``
    Current production release on PyPI.

Pull Requests
++++++++++++++

1. Create a new local branch.
::

    $ git checkout -b name-of-feature

2. Commit your changes. Write `good commit messages <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_.
::

    $ git commit -m "Detailed commit message"
    $ git push origin name-of-feature

3. Before submitting a pull request, check the following:

- If the pull request adds functionality, it is tested and the docs are updated.
- You've added yourself to ``AUTHORS.rst``.

4. Submit a pull request to the ``sloria:dev`` branch. The `Travis CI <https://travis-ci.org/sloria/marshmallow>`_ build must be passing before your pull request is merged.

Running tests
+++++++++++++

To run all tests: ::

    $ invoke test

To run tests on Python 2.6, 2.7, 3.3, 3.4, and PyPy virtual environments (must have each interpreter installed): ::

    $ tox

Documentation
+++++++++++++

Contributions to the documentation are welcome. Documentation is written in `reStructured Text`_ (rST). A quick rST reference can be found `here <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_. Builds are powered by Sphinx_.

To build the docs: ::

    $ invoke docs -b

The ``-b`` (for "browse") automatically opens up the docs in your browser after building.


.. _Sphinx: http://sphinx.pocoo.org/
.. _`reStructured Text`: http://docutils.sourceforge.net/rst.html
.. _marshmallow: https://github.com/sloria/marshmallow
