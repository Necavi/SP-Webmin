from flask import render_template

from . import plugin

from .models import BanRecord


@plugin.route("/")
def index():
    return render_template("bans/list.html", bans=BanRecord.query.all())

