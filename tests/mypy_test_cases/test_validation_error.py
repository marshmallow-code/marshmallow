from __future__ import annotations

import marshmallow as ma

# OK types for 'message'
ma.ValidationError("foo")
ma.ValidationError(["foo"])
ma.ValidationError({"foo": "bar"})

# non-OK types for 'message'
ma.ValidationError(0)  # type: ignore[arg-type]

# 'messages' is a dict|list
err = ma.ValidationError("foo")
a: dict | list = err.messages
# union type can't assign to non-union type
b: str = err.messages  # type: ignore[assignment]
c: dict = err.messages  # type: ignore[assignment]
# 'messages_dict' is a dict, so that it can assign to a dict
d: dict = err.messages_dict
