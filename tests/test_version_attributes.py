# ruff: noqa: B018
import pytest

import marshmallow


def test_version_attributes_deprecated():
    with pytest.warns(DeprecationWarning):
        marshmallow.__version__

    with pytest.warns(DeprecationWarning):
        marshmallow.__parsed_version__

    with pytest.warns(DeprecationWarning):
        marshmallow.__version_info__
