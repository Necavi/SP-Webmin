import re

from flask import session, redirect, url_for, render_template, request
from flask.ext.openid import OpenID, COMMON_PROVIDERS
from flask.ext.login import LoginManager, AnonymousUserMixin, \
    current_user, login_user, logout_user

from . import app, db
from .models import User, Permission, PermissionObject, Server

oid = OpenID(app)
_steam_id_re = re.compile("steamcommunity.com/openid/id/(.*?)$")
login_manager = LoginManager(app)


class AnonymousUser(AnonymousUserMixin):
    permissions = set()
    permission_cache = set()
    username = "Anonymous"

    def __init__(self):
        guest_group = PermissionObject.query.filter_by(identifier=app.config.get("GUEST_GROUP", "guest")).first()
        if guest_group is None:
            return
        self.permissions.update([perm.node for perm in guest_group.permissions])
        self.permissions.add("web.pages.index")
        self.permission_cache.add(User._compile_permission("web.pages.index"))

    def has_permission(self, permission):
        for perm in self.permission_cache:
            if perm.match(permission):
                return True
        return False

login_manager.anonymous_user = AnonymousUser


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
    return render_template("header.html")


@app.route("/list_players", methods=["GET", "POST"])
def list_players():
    if request.method == "POST":
        obj = PermissionObject(type=request.form["type"], identifier=request.form["identifier"])
        db.session.add(obj)
        db.session.commit()
        return redirect(url_for("list_players"))
    return render_template("object_list.html", objects=PermissionObject.query.all())


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
