import json

from flask import render_template, request
from flask_login import current_user

from sqlalchemy import desc

from . import plugin

from .models import BanRecord

from sp_webmin import db, app
from sp_webmin.models import Server


@plugin.route("/")
def index():
    return render_template("bans/list.html", bans=BanRecord.query.order_by(desc(BanRecord.date)).all(),
                           servers=Server.list_servers())


@plugin.route("/add", methods=["POST"])
def add_ban():
    ban = BanRecord(name=request.form["name"], duration=request.form["duration"], server_id=request.form["server_id"],
                    target_id=request.form["target_id"], admin_id=current_user.steamid)
    db.session.add(ban)
    db.session.commit()
    return json.dumps({
        "row": render_template("bans/list_row.html", ban=ban)
    })


@plugin.route("/my")
def my_bans():
    return render_template("bans/list.html", bans=BanRecord.query.filter_by(target_id=current_user.steamid).
                           order_by(desc(BanRecord.date)).all(),
                           servers=Server.list_servers())
