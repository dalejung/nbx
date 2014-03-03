
from tornado import web
from nbx.handlers import NBXHandler

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
