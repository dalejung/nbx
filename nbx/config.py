from dotenv import load_dotenv, dotenv_values, find_dotenv
from traitlets.config.loader import (
    PyFileConfigLoader
)
from jupyter_core.paths import jupyter_config_dir


def get_config(filename='nbx_config.py'):
    config_dir = jupyter_config_dir()
    pyloader = PyFileConfigLoader(filename, path=config_dir)
    config = pyloader.load_config()
    return config


config = dotenv_values()
GITHUB_TOKEN = config.get('GITHUB_TOKEN', None)
