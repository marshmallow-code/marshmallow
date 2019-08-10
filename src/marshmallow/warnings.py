# -*- coding: utf-8 -*-
from __future__ import absolute_import
import functools
import warnings


class RemovedInMarshmallow3Warning(DeprecationWarning):
    pass


class ChangedInMarshmallow3Warning(FutureWarning):
    pass


def unused_and_removed_in_ma3(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        warnings.warn(
            '{} is unused and is removed in marshmallow 3.'.format(f.__name__),
            RemovedInMarshmallow3Warning,
            stacklevel=2,
        )
        return f(*args, **kwargs)

    return wrapped
