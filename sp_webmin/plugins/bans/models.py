from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import reconstructor
from sqlalchemy.sql import func

from sp_webmin import db
from sp_webmin.models import PermissionObject

base = db.Model


class BanRecord(base):
    __tablename__ = "bans"

    id = Column(Integer, primary_key=True)
    target_id = Column(BigInteger, nullable=False)
    admin_id = Column(BigInteger, nullable=False)
    name = Column(String(128))
    start_date = Column(DateTime, default=func.now())
    stop_date = Column(DateTime)
    duration = Column(Integer, default=0)
    reason = Column(String(256))
    ip_address = Column(String(32))
    server_id = Column(Integer, default=-1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load()

    # noinspection PyAttributeOutsideInit
    @reconstructor
    def load(self):
        self.target = PermissionObject.get(self.target_id)
        self.admin = PermissionObject.get(self.admin_id)
        self.server = PermissionObject.get(self.server_id)
