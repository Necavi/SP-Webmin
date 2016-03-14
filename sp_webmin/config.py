import os

from configobj import ConfigObj


path = "./sp_webmin/config.ini"


def load_config():
    if os.path.exists(path):
        return ConfigObj(path)["Default"]
    else:
        config = ConfigObj()
        config["Default"] = {}
        config.filename = path
        config.write()
        return {}
