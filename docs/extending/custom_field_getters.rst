Custom field getters
====================

By default, the value that is serialized or deserialized is accessed on the
input object or `dict` using a name as key or attribute.

Custom (de)serialization getters can be passed to the field to specify custom
ways of getting the values. This allows, for instance, aggregating several
values into one.


.. code-block:: python

    def make_full_name(obj, attr, default):
        return f"{obj.first_name} {obj.last_name}"


    def profile_complete(obj, attr, default):
        return all(obj[p] is not None for p in ("property_1", "property_2"))


    class UserSchema(Schema):
        first_name = fields.String(required=True)
        last_name = fields.String(required=True)
        full_name = fields.String(dump_only=True, dump_getter=make_full_name)
        property_1 = fields.String()
        property_2 = fields.String()
        profile_complete = fields.Boolean(load_getter=is_profile_complete)
