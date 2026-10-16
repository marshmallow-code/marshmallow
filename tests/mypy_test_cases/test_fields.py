import datetime as dt
from zoneinfo import ZoneInfo

from marshmallow import fields


def naive_datetime(timezone: dt.tzinfo) -> fields.NaiveDateTime:
    return fields.NaiveDateTime(timezone=timezone)


fields.NaiveDateTime(timezone=None)
fields.NaiveDateTime(timezone=dt.timezone.utc)
fields.NaiveDateTime(timezone=ZoneInfo("UTC"))
