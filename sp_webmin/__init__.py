from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)


def run(*args, **kwargs):
    from .config import load_config
    app.config.update(load_config())
    from . import models
    from . import views
    db.create_all()
    app.run(*args, **kwargs)
