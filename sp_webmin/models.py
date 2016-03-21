import re
import requests

from valve.steam import id

from sqlalchemy import Column, Integer, String, BigInteger, UniqueConstraint, Table, Enum, ForeignKey
from sqlalchemy.orm import relationship, reconstructor

from flask.ext.login import UserMixin, AnonymousUserMixin

from . import db
from . import app

Base = db.Model

steam_url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={}&steamids={}"
parents_table = Table(
    'parents',
    Base.metadata,
    Column('parent_id', Integer, ForeignKey('objects.id'), primary_key=True),
    Column('child_id', Integer, ForeignKey('objects.id'), primary_key=True)
)


class PermissionSet(set):

    def __init__(self):
        super().__init__()
        self.permissions_cache = set()

    @staticmethod
    def _compile_permission(permission):
        return re.compile(permission.replace('.', '\\.').replace('*', '(.*)'))

    def update(self, *args, **kwargs):
        for arg in args:
            for value in arg:
                self.add(value)

    def add(self, perm):
        self.permissions_cache.add(self._compile_permission(perm))
        super().add(perm)

    def remove(self, perm):
        self.permissions_cache.remove(self._compile_permission(perm))
        super().remove(perm)

    def has(self, perm):
        for node in self.permissions_cache:
            if node.match(perm):
                return True
        return False


class PermissionBase(object):
    username = "Base"

    def __init__(self):
        self.permissions = PermissionSet()

    def has_permission(self, permission):
        return self.permissions.has(permission)


class AnonymousUser(PermissionBase, AnonymousUserMixin):
    username = "Anonymous"

    def __init__(self):
        super().__init__()
        guest_group = PermissionObject.query.filter_by(identifier=app.config.get("GUEST_GROUP", "guest")).first()
        if guest_group is None:
            return
        self.permissions.update([perm.node for perm in guest_group.permissions])


class User(PermissionBase, Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True)
    email = Column(String(256), unique=True, nullable=True)
    steamid = Column(BigInteger, unique=True)

    avatarUrl = ""

    def __init__(self, steamid):
        super().__init__()
        self.steamid = steamid

    @staticmethod
    def get(steamid):
        user = User.query.filter(User.steamid == steamid).first()
        if user is None:
            user = User(steamid)
        obj = PermissionObject.get(steamid)
        user.permissions.clear()
        if obj is None:
            user.permissions.update(PermissionObject.get(
                app.config.get("DEFAULT_GROUP", "default")).flatten_permissions())
        else:
            user.permissions.update(obj.flatten_permissions())
        steam_user = requests.get(steam_url.format(app.config["STEAM_API_KEY"], steamid)).json()
        user.username = steam_user['response']['players'][0]['personaname']
        user.avatarUrl = steam_user["response"]["players"][0]["avatar"]
        user.permissions.add("web.pages.index")
        return user

    def get_id(self):
        return self.steamid

    def __repr__(self):
        return "User: {}:{}:{}".format(self.username, self.email, self.steamid)


class Permission(Base):
    __tablename__ = 'permissions'
    __table_args__ = (UniqueConstraint('object_id', 'server_id', 'node',
                                       name='object_server_node_uc'),)

    id = Column(Integer, primary_key=True)
    object_id = Column(Integer, ForeignKey('objects.id'), nullable=False)
    server_id = Column(Integer, default=-1, nullable=False)
    node = Column(String(255), nullable=False)


class PermissionObject(Base):
    __tablename__ = 'objects'
    __table_args__ = (UniqueConstraint(
        'identifier', 'object_type', name='identifier_type_uc'),)

    name = ""
    avatarUrl = ""
    steamUrl = ""
    formattedSteamId = ""

    id = Column(Integer, primary_key=True)
    identifier = Column(String(64), nullable=False)
    type = Column(Enum('Group', 'Player'), name='object_type')
    permissions = relationship('Permission', backref='object')
    children = relationship('PermissionObject',
                            secondary=parents_table,
                            primaryjoin=id == parents_table.c.parent_id,
                            secondaryjoin=id == parents_table.c.child_id,
                            backref='parents'
                            )

    def __init__(self, identifier, type):
        self.identifier = identifier
        self.type = type
        self.on_load()

    @reconstructor
    def on_load(self):
        self.name = self.identifier
        self.formattedSteamId = self.identifier
        if self.type == "Player":
            steam_user = requests.get(steam_url.format(app.config["STEAM_API_KEY"], self.identifier)).json()
            if len(steam_user["response"]["players"]) > 0:
                self.name = steam_user['response']['players'][0]['personaname']
                self.avatarUrl = steam_user["response"]["players"][0]["avatarmedium"]
                self.steamUrl = steam_user["response"]["players"][0]["profileurl"]
            steam_id = id.SteamID.from_community_url("http://steamcommunity.com/profiles/" +
                                                     str(self.identifier))
            steamid_format = app.config.get("STEAMID_FORMAT", "")
            if steamid_format.casefold() == "Steam3".casefold():
                self.formattedSteamId = steam_id.as_32()
            elif steamid_format.casefold() == "Steam2".casefold():
                self.formattedSteamId = str(steam_id)

    @staticmethod
    def get(identifier):
        obj = PermissionObject.query.filter_by(identifier=identifier).first()
        return obj

    def get_permissions(self):
        return set([perm.node for perm in self.permissions if perm.server_id == -1])

    def get_permission_heirarchy(self):
        perms = list()
        perms.append(self.identifier)
        perms.append([(perm.node, perm.server_id) for perm in self.permissions])
        if len(self.parents) > 0:
            parents = []
            for parent in self.parents:
                parents.append(parent.get_permission_heirarchy())
            perms.append(parents)
        return perms

    def get_permission_heirarchy_by_server(self, perms, prefix=None, first=True):
        if prefix is None:
            prefix = self.identifier
        else:
            prefix = prefix + "." + self.identifier
        for perm in self.permissions:
            if perm.server_id not in perms:
                perms[perm.server_id] = {}
            if prefix not in perms[perm.server_id]:
                perms[perm.server_id][prefix] = []
            perms[perm.server_id][prefix].append(perm.node)
        for parent in self.parents:
            parent.get_permission_heirarchy_by_server(perms, prefix=None if first else prefix, first=False)

    def flatten_permissions(self):
        perms = []
        perms.extend([perm.node for perm in self.permissions if perm.server_id == -1])
        for parent in self.parents:
            perms.extend(parent.flatten_permissions())
        return perms

    def __repr__(self):
        return "User: {}:{}".format(self.identifier, self.type)


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True)
    name = Column(String(127), nullable=False)

    @staticmethod
    def list_servers():
        servers = {-1: "All Servers"}
        servers.update({server.id: server.name for server in Server.query.all()})
        return servers

    @staticmethod
    def get(self, id):
        if id == -1:
            server = Server(id=-1, name="All Servers")
        else:
            server = Server.query.filter_by(id=id).first()
