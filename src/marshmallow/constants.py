import typing

EXCLUDE: typing.Final = "exclude"
INCLUDE: typing.Final = "include"
RAISE: typing.Final = "raise"


class _Missing:
    def __bool__(self):
        return False

    def __copy__(self):
        return self

    def __deepcopy__(self, _):
        return self

    def __repr__(self):
        return "<marshmallow.missing>"


missing: typing.Final = _Missing()
