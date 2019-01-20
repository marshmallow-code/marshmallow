import sys
import json
from packaging import version
from marshmallow import Schema, fields, INCLUDE, pprint, ValidationError


class Version(fields.Field):
    """Version field that deserializes to a Version object.
    Raises a ValidationError if version is invalid.
    """

    def _deserialize(self, value, *args, **kwargs):
        try:
            return version.Version(value)
        except version.InvalidVersion:
            raise ValidationError("Not a valid version.")

    def _serialize(self, value, *args, **kwargs):
        return str(value)


class PackageSchema(Schema):
    name = fields.Str(required=True)
    version = Version(required=True)
    description = fields.Str(required=True)
    main = fields.Str(required=False)
    homepage = fields.URL(required=False)
    scripts = fields.Dict(keys=fields.Str(), values=fields.Str())
    license = fields.Str(required=True)
    dependencies = fields.Dict(keys=fields.Str(), values=fields.Str(), required=False)
    dev_dependencies = fields.Dict(
        keys=fields.Str(),
        values=fields.Str(),
        required=False,
        data_key="devDependencies",
    )

    class Meta:
        # Include unknown fields in the
        # deserialized output
        unknown = INCLUDE


if __name__ == "__main__":
    pkg = json.load(sys.stdin)
    try:
        pprint(PackageSchema().load(pkg))
    except ValidationError as error:
        print("ERROR: package.json is invalid")
        pprint(error.messages)
        sys.exit(1)
