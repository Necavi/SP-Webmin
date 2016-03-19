from datetime import timedelta, datetime

from . import app

pages = [("Home", "index"), ("List Players", "player_list"), ("Settings", "settings")]


def format_date(date):
    local_date = date + timedelta(hours=int(app.config.get("TIME_OFFSET", 0)))
    return local_date.strftime(app.config.get("DATE_FORMAT", "%Y/%m/%d %H:%M:%S"))


def td_format(td_object):
        seconds = int(td_object.total_seconds())
        periods = [
                ('year',        60*60*24*365),
                ('month',       60*60*24*30),
                ('day',         60*60*24),
                ('hour',        60*60),
                ('minute',      60),
                ('second',      1)
                ]

        strings = []
        for period_name, period_seconds in periods:
                if seconds > period_seconds:
                        period_value, seconds = divmod(seconds, period_seconds)
                        if period_value == 1:
                                strings.append("%s %s" % (period_value, period_name))
                        else:
                                strings.append("%s %ss" % (period_value, period_name))

        return ", ".join(strings)


@app.context_processor
def context():
    return {
        "pages": pages,
        "format_date": format_date,
        "format_duration": td_format,
        "timedelta": timedelta,
        "datetime": datetime
    }
