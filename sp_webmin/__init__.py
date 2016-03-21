from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)


def run(*args, **kwargs):
    from .config import load_config
    app.config.update(load_config())
    from . import models
    from . import views
    from .plugins import bans
    from .jinja_context import pages, my_pages
    app.register_blueprint(bans.plugin)
    pages.extend(bans.pages)
    my_pages.extend(bans.my_pages)
    db.create_all()
    app.run(*args, **kwargs)
