from flask import Blueprint

plugin = Blueprint("bans", __name__, url_prefix="/bans", template_folder="templates")

pages = [("Bans", "bans.index")]

from . import views
