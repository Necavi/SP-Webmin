import json

from flask import render_template, request
from flask_login import current_user

from . import plugin

from .models import BanRecord

from sp_webmin import db, app
from sp_webmin.models import Server
from sp_webmin.jinja_context import format_date


@plugin.route("/")
def index():
    return render_template("bans/list.html", bans=BanRecord.query.all(), servers=Server.list_servers())


@plugin.route("/add", methods=["POST"])
def add_ban():
    ban = BanRecord(name=request.form["name"], duration=request.form["duration"], server_id=request.form["server_id"],
                    target_id=request.form["target_id"], admin_id=current_user.steamid)
    db.session.add(ban)
    db.session.commit()
    return json.dumps({
        "target": "{} ({})".format(ban.target.name, ban.target.formattedSteamId),
        "admin": "{} ({})".format(ban.admin.name, ban.admin.formattedSteamId),
        "date": format_date(ban.date)
    })
