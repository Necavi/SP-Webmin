import json

from datetime import datetime

from flask import render_template, render_template_string, request
from flask_login import current_user

from sqlalchemy import desc

from . import plugin

from .models import BanRecord

from sp_webmin import db, app
from sp_webmin.models import Server


@plugin.route("/")
def index():
    return render_template("bans/list.html", bans=BanRecord.query.order_by(desc(BanRecord.start_date)).all(),
                           servers=Server.list_servers())


@plugin.route("/add", methods=["POST"])
def add_ban():
    ban = BanRecord(name=request.form["name"], duration=request.form["duration"], server_id=request.form["server_id"],
                    target_id=request.form["target_id"], admin_id=current_user.steamid, reason=request.form["reason"])
    db.session.add(ban)
    db.session.commit()
    return json.dumps({
        "row": render_template("bans/list_row.html", ban=ban)
    })


@plugin.route("/remove", methods=["POST"])
def remove_ban():
    ban_id = request.form.get("ban_id")
    ban = BanRecord.query.filter_by(id=ban_id).first()
    if ban is not None:
        ban.stop_date = datetime.utcnow()
        db.session.commit()
        return json.dumps({"date": render_template_string("Stop Date: {{ format_date(ban.stop_date) }}", ban=ban)})
    return json.dumps({"date": ""})


@plugin.route("/my")
def my_bans():
    return render_template("bans/list.html", bans=BanRecord.query.filter_by(target_id=current_user.steamid).
                           order_by(desc(BanRecord.date)).all(),
                           servers=Server.list_servers())
