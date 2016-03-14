import os

from configobj import ConfigObj


path = "./sp_webmin/config.ini"


def load_config():
    if os.path.exists(path):
        return ConfigObj(path)["Default"]
    else:
        config = ConfigObj()
        config["Default"] = {}
        config["Default"]["SECRET_KEY"] = ""
        config["Default"]["STEAM_API_KEY"] = ""
        config["Default"]["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        config.filename = path
        config.write()
        return {}
