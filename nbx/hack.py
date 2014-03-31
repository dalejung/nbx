import os.path
from tornado import web

from IPython.html.base.handlers import IPythonHandler, json_errors
from IPython.html.services.kernels.kernelmanager import MappingKernelManager
from IPython.html.services.sessions.handlers import SessionRootHandler, \
                                url_path_join, url_escape, json, date_default
from IPython.html.services.notebooks.nbmanager import NotebookManager
from IPython.html.services.notebooks.filenbmanager import FileNotebookManager

# monkey patch alternative to  https://github.com/ipython/ipython/pull/5469

def cwd_for_path(self, path):
    """Turn API path into absolute OS path."""
    # short circuit for NotebookManagers that pass in absolute paths
    if os.path.exists(path):
        return path

    os_path = to_os_path(path, self.root_dir)
    # in the case of notebooks and kernels not being on the same filesystem,
    # walk up to root_dir if the paths don't exist
    while not os.path.exists(os_path) and os_path != self.root_dir:
        os_path = os.path.dirname(os_path)
    return os_path

MappingKernelManager.cwd_for_path = cwd_for_path

@web.authenticated
@json_errors
def post(self):
    # Creates a new session
    #(unless a session already exists for the named nb)
    sm = self.session_manager
    nbm = self.notebook_manager
    km = self.kernel_manager
    model = self.get_json_body()
    if model is None:
        raise web.HTTPError(400, "No JSON data provided")
    try:
        name = model['notebook']['name']
    except KeyError:
        raise web.HTTPError(400, "Missing field in JSON data: name")
    try:
        path = model['notebook']['path']
    except KeyError:
        raise web.HTTPError(400, "Missing field in JSON data: path")
    # Check to see if session exists
    if sm.session_exists(name=name, path=path):
        model = sm.get_session(name=name, path=path)
    else:
        # allow nbm to specify kernels cwd
        kernel_path = nbm.get_kernel_path(name=name, path=path)
        kernel_id = km.start_kernel(path=kernel_path)
        model = sm.create_session(name=name, path=path, kernel_id=kernel_id)
    location = url_path_join(self.base_url, 'api', 'sessions', model['id'])
    self.set_header('Location', url_escape(location))
    self.set_status(201)
    self.finish(json.dumps(model, default=date_default))

SessionRootHandler.post = post

def get_kernel_path(self, name, path='', model=None):
    """ Return the path to start kernel in """
    return path

NotebookManager.get_kernel_path = get_kernel_path

def get_kernel_path(self, name, path='', model=None):
    """ Return the path to start kernel in """
    return os.path.join(self.notebook_dir, path)

FileNotebookManager.get_kernel_path = get_kernel_path
