import pytz
from datetime import timedelta
from collections import namedtuple


BOT_TZ = pytz.timezone("Asia/Dubai")

Timedelta = namedtuple("Timedelta", "delta unit")

def get_timedelta(arg: str) -> timedelta:
    """Converts a string of time for eg: 5h -> into an equivalent timedelta object. Returns a namedtuple with the timedelta and the unit as a string."""
    time_, unit = "", ""
    for i in arg:
        if i.isdigit():
            time_ += i
        else:
            unit += i
    else:
        time_ = int(time_)

    if unit.lower().startswith("h"):
        return Timedelta(delta=timedelta(hours=time_), unit="hours")
    elif unit.lower().startswith("d"):
        return Timedelta(delta=timedelta(days=time_), unit="days")
    else:
        raise TypeError(f"Unsupported unit of time. Expecting `hours` or `days`, got {unit}")
    