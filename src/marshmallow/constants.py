import typing

EXCLUDE: typing.Final = "exclude"
INCLUDE: typing.Final = "include"
RAISE: typing.Final = "raise"


class _Missing:
    _instance: "_Missing | None" = None

    def __new__(cls) -> typing.Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __bool__(self):
        return False

    def __copy__(self):
        return self

    def __deepcopy__(self, _):
        return self

    def __repr__(self):
        return "<marshmallow.missing>"

    def __len__(self):
        return 0

    def __reduce__(self):
        return "missing"


missing: typing.Final = _Missing()
