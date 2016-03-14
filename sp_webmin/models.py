import re
import requests

from sqlalchemy import Column, Integer, String, BigInteger, UniqueConstraint, Table, Enum, ForeignKey
from sqlalchemy.orm import relationship
from flask.ext.login import UserMixin

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


class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True)
    username = ""
    email = Column(String(256), unique=True, nullable=True)
    steamid = Column(BigInteger, unique=True)
    permissions = set()
    permission_cache = set()

    def __init__(self, steamid):
        self.steamid = steamid

    @staticmethod
    def _compile_permission(permission):
        return re.compile(permission.replace('.', '\\.').replace('*', '(.*)'))

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
        user.permission_cache.clear()
        for permission in user.permissions:
            user.permission_cache.add(User._compile_permission(permission))
        steam_user = requests.get(steam_url.format(app.config["STEAM_API_KEY"], steamid)).json()
        user.username = steam_user['response']['players'][0]['personaname']
        user.permissions.add("web.pages.index")
        user.permission_cache.add(User._compile_permission("web.pages.index"))
        return user

    def has_permission(self, permission):
        for perm in self.permission_cache:
            if perm.match(permission):
                return True
        return False

    def get_id(self):
        return self.steamid

    def __repr__(self):
        return "User: {}:{}:{}".format(self.name, self.email, self.steamid)


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

    id = Column(Integer, primary_key=True)
    identifier = Column(String(64), nullable=False, unique=True)
    type = Column(Enum('Group', 'Player'), name='object_type')

    permissions = relationship('Permission', backref='object')
    children = relationship('PermissionObject',
                            secondary=parents_table,
                            primaryjoin=id == parents_table.c.parent_id,
                            secondaryjoin=id == parents_table.c.child_id,
                            backref='parents'
                            )

    @staticmethod
    def get(identifier):
        return PermissionObject.query.filter_by(identifier=identifier).first()

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
