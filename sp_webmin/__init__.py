from flask import Flask
from flask_bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)


def run(*args, **kwargs):
    Bootstrap(app)
    from .config import load_config
    app.config.update(load_config())
    from . import models
    db.create_all()
    from . import views
    app.run(*args, **kwargs)
