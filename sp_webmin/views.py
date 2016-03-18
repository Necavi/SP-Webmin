import re
import json
import requests

from datetime import timedelta

from flask import session, redirect, url_for, render_template, request
from flask.ext.openid import OpenID, COMMON_PROVIDERS
from flask.ext.login import LoginManager, current_user, login_user, logout_user

from . import app, db
from .config import load_config, write_config
from .models import User, Permission, PermissionObject, Server, AnonymousUser

from .plugins import bans
from .jinja_context import pages

oid = OpenID(app)
_steam_id_re = re.compile("steamcommunity.com/openid/id/(.*?)$")
login_manager = LoginManager(app)


steam_url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={}&steamids={}"
login_manager.anonymous_user = AnonymousUser

app.register_blueprint(bans.plugin)
pages.extend(bans.pages)


@app.route("/register")
@oid.loginhandler
def register_start():
    return oid.try_login(COMMON_PROVIDERS["steam"])


@app.route("/log_out", methods=["POST"])
def logout():
    logout_user()
    session.pop("steamid")
    return redirect(url_for("index"))


@oid.after_login
def create_or_login(resp):
    match = _steam_id_re.search(resp.identity_url)
    session["steamid"] = match.group(1)
    login_user(User.get(session["steamid"]))
    return redirect(oid.get_next_url())


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/")
def index():
    return render_template("layout.html")


@app.route("/player_list", methods=["GET", "POST"])
def player_list():
    if request.method == "POST":
        obj = PermissionObject(type=request.form["type"], identifier=request.form["identifier"])
        db.session.add(obj)
        db.session.commit()
        return redirect(url_for("player_list"))
    return render_template("player_list.html", objects=PermissionObject.query.all())


@app.route("/player_detail/<identifier>", methods=["GET", "POST"])
def player_detail(identifier):
    obj = PermissionObject.get(identifier)
    if request.method == "POST":
        perm = Permission(object_id=obj.id, node=request.form["node"], server_id=request.form["server"])
        PermissionObject.get(identifier).permissions.append(perm)
        db.session.commit()
        return redirect(url_for("player_detail", identifier=identifier))
    return render_template("object_detail.html", obj=obj, servers=Server.list_servers(), type=type)


@app.route("/remove_object_permission", methods=["POST"])
def remove_object_permission():
    obj = PermissionObject.get(request.form["identifier"])
    rem_perm = None
    for perm in obj.permissions:
        if perm.node == request.form["node"] and perm.server_id == int(request.form["server_id"]):
            rem_perm = perm
            break
    if rem_perm is not None:
        db.session.delete(rem_perm)
        db.session.commit()
    return redirect(url_for("player_detail", identifier=request.form["identifier"]))


@app.route("/add_server", methods=["POST"])
def add_server():
    name = request.form["name"]
    try:
        server = Server(name=name)
        db.session.add(server)
        db.session.commit()
    except:
        server = Server.query.filter_by(name=name).first()
    return json.dumps({
        "id": server.id,
        "name": server.name
    })


@app.route("/add_object", methods=["POST"])
def add_object():
    identifier = request.form["identifier"]
    try:
        obj = PermissionObject(identifier, request.form["type"])
        db.session.add(obj)
        db.session.commit()
    except:
        obj = PermissionObject.query.filter_by(identifier=identifier).first()
    return json.dumps({
        "identifier": obj.identifier,
        "name": obj.name,
        "type": obj.type,
        "url": url_for("player_detail", identifier=obj.identifier),
        "steamUrl": obj.steamUrl
    })


@app.route("/settings")
def settings():
    return render_template("settings.html", config=load_config())


@app.route("/update_settings", methods=["POST"])
def update_settings():
    config = {key.upper().replace(" ", "_"): value for key, value in request.form.items()}
    write_config(config)
    app.config.update(config)
    return redirect(url_for("settings"))


@app.route("/check_steam_id")
def check_steam_id():
    if "steamID" not in request.args:
        return json.dumps({"result": False})
    url = steam_url.format(app.config["STEAM_API_KEY"], request.args["steamID"])
    steam_user = requests.get(url).json()
    if len(steam_user["response"]["players"]) > 0:
        return json.dumps({"result": True, "player": {"name": steam_user["response"]["players"][0]["personaname"]}})
    else:
        return json.dumps({"result": False})
