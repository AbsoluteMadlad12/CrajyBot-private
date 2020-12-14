import pytz
from datetime import timedelta

BOT_TZ = pytz.timezone("Asia/Dubai")

def get_timedelta(arg: str) -> timedelta:
    """Converts a string of time for eg: 5h -> into an equivalent timedelta object."""
    time_, unit = "", ""
    for i in arg:
        if i.isdigit():
            time_ += i
        else:
            unit += i
    else:
        time_ = int(time_)

    if unit.lower().startswith("h"):
        return timedelta(hours=time_)
    elif unit.lower().startswith("d"):
        return timedelta(days=time_)
    else:
        raise TypeError(f"Unsupported unit of time. Expecting `hours` or `days`, got {unit}")
    