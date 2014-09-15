import json
from tornado import web
from nbx.handlers import NBXHandler

class ServerInfoHandler(NBXHandler):
    @web.authenticated
    def get(self, path='', name=None):
        nbm = self.contents_manager
        app = nbm.parent
        data = {}
        data['profile'] = app.profile
        self.finish(json.dumps(data))

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/server-info", ServerInfoHandler),
    ]
