#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
The main test runner script.

Usage: ::

    python run_tests.py

Skip slow tests: ::

    python run_tests.py fast
'''
from __future__ import unicode_literals
import nose
import sys
from marshmallow.compat import PY2, PY26


def main():
    args = get_argv()
    success = nose.run(argv=args)
    sys.exit(0) if success else sys.exit(1)


def get_argv():
    args = [sys.argv[0], ]
    attr_conditions = []  # Use nose's attribselect plugin to filter tests
    if "force-all" in sys.argv:
        # Don't exclude any tests
        return args
    if PY26:
        # Exclude tests that don't work on python2.6
        attr_conditions.append("not py27_only")
    if not PY2:
        # Exclude tests that only work on python2
        attr_conditions.append("not py2_only")
    if "fast" in sys.argv:
        attr_conditions.append("not slow")

    attr_expression = " and ".join(attr_conditions)
    if attr_expression:
        args.extend(["-A", attr_expression])
    return args

if __name__ == '__main__':
    main()