from traitlets.config.loader import (
    PyFileConfigLoader
)

from jupyter_core.paths import jupyter_config_dir, jupyter_data_dir

def get_config(filename='nbx_config.py'):
    config_dir = jupyter_config_dir()
    pyloader = PyFileConfigLoader(filename, path=config_dir)
    config = pyloader.load_config()
    return config
