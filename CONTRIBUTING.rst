Contributing Guidelines
=======================

So you're interested in contributing to marshmallow or `one of our associated
projects <https://github.com/marshmallow-code>`__? That's awesome! We
welcome contributions from anyone willing to work in good faith with
other contributors and the community (see also our
:doc:`code_of_conduct`).

Security Contact Information
----------------------------

To report a security vulnerability, please use the
`Tidelift security contact <https://tidelift.com/security>`_.
Tidelift will coordinate the fix and disclosure.

Questions, Feature Requests, Bug Reports, and Feedback…
-------------------------------------------------------

…should all be reported on the `Github Issue Tracker`_ .

.. _`Github Issue Tracker`: https://github.com/marshmallow-code/marshmallow/issues?state=open

Ways to Contribute
------------------

- Comment on some of marshmallow's `open issues <https://github.com/marshmallow-code/marshmallow/issues>`_ (especially those `labeled "feedback welcome" <https://github.com/marshmallow-code/marshmallow/issues?q=is%3Aopen+is%3Aissue+label%3A%22feedback+welcome%22>`_). Share a solution or workaround. Make a suggestion for how a feature can be made better. Opinions are welcome!
- Improve `the docs <https://marshmallow.readthedocs.io>`_.
  For straightforward edits,
  click the ReadTheDocs menu button in the bottom-right corner of the page and click "Edit".
  See the :ref:`Documentation <contributing_documentation>` section of this page if you want to build the docs locally.
- If you think you've found a bug, `open an issue <https://github.com/marshmallow-code/marshmallow/issues>`_.
- Contribute an :ref:`example usage <contributing_examples>` of marshmallow.
- Send a PR for an open issue (especially one `labeled "help wanted" <https://github.com/marshmallow-code/marshmallow/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22>`_). The next section details how to contribute code.


Contributing Code
-----------------

In General
++++++++++

- `PEP 8`_, when sensible.
- Test ruthlessly. Write docs for new features.
- Even more important than Test-Driven Development--*Human-Driven Development*.

.. _`PEP 8`: https://www.python.org/dev/peps/pep-0008/

In Particular
+++++++++++++


Setting Up for Local Development
********************************

1. Fork marshmallow_ on Github.

::

    $ git clone https://github.com/marshmallow-code/marshmallow.git
    $ cd marshmallow

2. Install development requirements. **It is highly recommended that you use a virtualenv.**
   Use the following command to install an editable version of
   marshmallow along with its development requirements.

::

    # After activating your virtualenv
    $ pip install -e '.[dev]'

3. Install the pre-commit hooks, which will format and lint your git staged files.

::

    # The pre-commit CLI was installed above
    $ pre-commit install --allow-missing-config

Git Branch Structure
********************

Marshmallow abides by the following branching model:

``dev``
    Current development branch. **New features should branch off here**.

``X.Y-line``
    Maintenance branch for release ``X.Y``. **Bug fixes should be sent to the most recent release branch.** The maintainer will forward-port the fix to ``dev``. Note: exceptions may be made for bug fixes that introduce large code changes.

**Always make a new branch for your work**, no matter how small. Also, **do not put unrelated changes in the same branch or pull request**. This makes it more difficult to merge your changes.

Pull Requests
**************

1. Create a new local branch.

::

    # For a new feature
    $ git checkout -b name-of-feature dev

    # For a bugfix
    $ git checkout -b fix-something 2.x-line

2. Commit your changes. Write `good commit messages <https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_.

::

    $ git commit -m "Detailed commit message"
    $ git push origin name-of-feature

3. Before submitting a pull request, check the following:

- If the pull request adds functionality, it is tested and the docs are updated.
- You've added yourself to ``AUTHORS.rst``.

4. Submit a pull request to ``marshmallow-code:dev`` or the appropriate maintenance branch. The `CI <https://dev.azure.com/sloria1/sloria/_build/latest?definitionId=5&branchName=dev>`_ build must be passing before your pull request is merged.

Running tests
*************

To run all tests: ::

    $ pytest

To run syntax checks: ::

    $ tox -e lint

(Optional) To run tests in all supported Python versions in their own virtual environments (must have each interpreter installed): ::

    $ tox

.. _contributing_documentation:

Documentation
*************

Contributions to the documentation are welcome. Documentation is written in `reStructured Text`_ (rST). A quick rST reference can be found `here <https://docutils.sourceforge.net/docs/user/rst/quickref.html>`_. Builds are powered by Sphinx_.

To build the docs in "watch" mode: ::

   $ tox -e watch-docs

Changes in the `docs/` directory will automatically trigger a rebuild.


.. _contributing_examples:

Contributing Examples
*********************

Have a usage example you'd like to share? A custom `Field` that others might find useful? Feel free to add it to the `examples <https://github.com/marshmallow-code/marshmallow/tree/dev/examples>`_ directory and send a pull request.


.. _Sphinx: https://www.sphinx-doc.org/
.. _`reStructured Text`: http://docutils.sourceforge.net/rst.html
.. _marshmallow: https://github.com/marshmallow-code/marshmallow
