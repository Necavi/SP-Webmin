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
        config["Default"]["SteamID Format"] = "Steam64"
        config["Default"]["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        config.filename = path
        config.write()
        return {}


def write_config(config):
    new_config = ConfigObj()
    new_config["Default"] = config
    new_config.filename = path
    new_config.write()
