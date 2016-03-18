from datetime import timedelta

from . import app

pages = [("Home", "index"), ("List Players", "player_list"), ("Settings", "settings")]


def format_date(date):
    local_date = date + timedelta(hours=int(app.config.get("TIME_OFFSET", 0)))
    return local_date.strftime(app.config.get("DATE_FORMAT", "%Y/%m/%d %H:%M:%S"))


@app.context_processor
def context():
    return {
        "pages": pages,
        "format_date": format_date
    }
