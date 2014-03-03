import os

from tornado import web
import tornado.template as template
from IPython.html.base.handlers import IPythonHandler
from jinja2 import Environment, FileSystemLoader

template_path = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(template_path))

class NBXHandler(IPythonHandler):
    def get_template(self, name):
        """Return the jinja template object for a given name"""
        return env.get_template(name)

class TestHandler(NBXHandler):
    """Render the tree view, listing notebooks, clusters, etc."""
    @web.authenticated
    def get(self, path='', name=None):
        self.write(self.render_template('test.html'))

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/test", TestHandler),
    ]
