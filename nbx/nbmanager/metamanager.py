import os
import datetime

from IPython.utils.traitlets import (
    Dict, Unicode, Integer, List, Bool, Bytes,
    DottedObjectName, TraitError, Tuple,
)
from IPython.utils.importstring import import_item
from IPython.utils.py3compat import getcwd
from IPython.config.configurable import LoggingConfigurable
from IPython.html.services.contents.manager import ContentsManager
from IPython.html.services.contents.filemanager import FileContentsManager
from IPython.html.base.zmqhandlers import ZMQStreamHandler
from IPython.html.utils import is_hidden, to_os_path, url_path_join

from nbx.nbmanager.tagged_gist.gistnbmanager import GistNotebookManager
from nbx.nbmanager.tagged_gist.notebook_gisthub import notebook_gisthub
from nbx.nbmanager.bundle.bundlenbmanager import BundleNotebookManager

from .middleware import manager_hook
from .root_manager import RootManager
from ..handlers import enable_custom_handlers
from .nbxmanager import NBXContentsManager

from .static_handler import patch_file_handler

patch_file_handler()

ZMQStreamHandler.same_origin = lambda self: True

class ManagerMeta(object):
    """
    Example of regular notebook:
        GET /server-home/dir1/dir2/notebook.ipynb
        IPython Vars:
            Name: notebook.ipynb
            Path: /server-home/dir1/dir2
        ManagerMeta Vars:
            request_path: /server-home/dir1/dir2/notebook.ipynb
            name: notebook.ipynb
            path: /dir1/dir2
            nbm_path: server-home

    Example of 1-depth sub manager selection:
        GET /server-home
        IPython Vars:
            Name: server-home
            Path:
        ManagerMeta Vars:
            request_path: /server-home
            name:
            path:
            nbm_path: server-home
    """
    # the original request path
    request_path = None

    #nbm alias
    nbm_path = None

    # local name and path
    path = None

    def __repr__(self):
        attrs = ["{0}={1}".format(k,v) for k, v in self.__dict__.items()]
        return "ManagerMeta({0})".format(",".join(attrs))

class MetaManager(NBXContentsManager):
    """
        Holds NotebookManager classes and routes calls to the appropiate
        manager.
    """
    debug = Bool(True)

    file_dirs = Dict(config=True,
                           help="Dict of alias, path")
    bundle_dirs = Dict(config=True,
                           help="BundleNBManager. Dict of alias, path")
    github_accounts = List(Tuple, config=True,
                           help="List of Tuple(github_account, github_password)")

    manager_middleware = Dict(config=True,
                           help="Dict of Middleware")

    # Not sure if this should be optional. For now, make it configurable
    enable_custom_handlers = Bool(True, config=True, help="Enable Custom Handlers")

    root_dir = Unicode(getcwd())

    def __init__(self, *args, **kwargs):
        super(MetaManager, self).__init__(*args, **kwargs)
        self.app = kwargs['parent']

        self.managers = {}
        server_home = FileContentsManager()
        server_home.root_dir = self.root_dir
        self.managers['server-home'] = server_home

        if self.enable_custom_handlers:
            enable_custom_handlers()

        for alias, path in self.file_dirs.items():
            fb = FileContentsManager()
            fb.root_dir = path
            self.managers[alias] = fb

        for alias, path in self.bundle_dirs.items():
            fb = BundleNotebookManager()
            fb.root_dir = path
            self.managers[alias] = fb

        for user, pw in self.github_accounts:
            gh = notebook_gisthub(user, pw)
            gbm = GistNotebookManager(gisthub=gh)
            self.managers['gist:'+user] = gbm

        self.middleware = {}
        for name, middleware in self.manager_middleware.items():
            cls = import_item(middleware)
            self.middleware[name] = cls(parent=self, log=self.log)

        self.root = RootManager(meta_manager=self)

    def dispatch_middleware(self, hook_name, *args, **kwargs):
        """
        dispatch hook calls to middleware
        """
        for name, middleware in self.middleware.items():
            method = getattr(middleware, hook_name, None)
            if method is not None:
                method(*args, **kwargs)

    def _nbm_from_path(self, path):
        """
        So this helper function takes in a request path and returns
        the manager for that path.

        Note: I would like to only take in a single full request path, but
        IPython is odd in its handling of this. So I have to accept a name
        param. Sometimes the name is really a path. blah
        """
        if self.debug:
            print('nbm_from_path(path={0})'.format(path))
            import inspect
            print(inspect.stack()[1][3])
        # TODO clean up this logic.
        request_path = path
        # remove beginning slash (/)
        if request_path and request_path[0] == os.sep:
            request_path = request_path[1:]

        meta = ManagerMeta()
        # we are on root
        if not request_path:
            meta.request_path = ''
            meta.path = ''
            return self.root, meta

        bits = request_path.split(os.sep)
        manager_path = bits.pop(0)

        local_path = os.sep.join(bits)

        meta.request_path = request_path
        meta.path = local_path
        meta.nbm_path = manager_path

        nbm = self.managers.get(manager_path)

        if self.debug:
            print(nbm, meta)
        return nbm, meta

    def list_dirs(self, path):
        nbm, meta = self._nbm_from_path(path)
        val = nbm.list_dirs(meta.path)
        return val

    # ContentsManager API part 1
    def path_exists(self, path):
        nbm, meta = self._nbm_from_path(path)
        if nbm is None:
            return False
        exists = nbm.path_exists(meta.path)
        return exists

    def is_hidden(self, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.is_hidden(meta.path)

    def file_exists(self, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.file_exists(meta.path)

    def exists(self, path=''):
        nbm, meta = self._nbm_from_path(path)
        if nbm is None:
            return False
        exists = nbm.exists(meta.path)
        return exists

    def get_model(self, path, content=True):
        nbm, meta = self._nbm_from_path(path)
        model = nbm.get_model(path=meta.path, content=content)

        # while the local manager doesn't know its nbm_path,
        # we have to add it back in for the metamanager.
        if model['type'] == 'directory':
            content = model.get("content", [])
            for m in content:
                m['path'] = meta.request_path
        return model

    @manager_hook
    def save(self, model, path):
        nbm, meta = self._nbm_from_path(path)
        # make sure path is local and doesn't include sub manager prefix
        model['path'] = meta.path
        model = nbm.save(model=model,path=meta.path)
        return model

    def update(self, model, path):
        """Update the notebook and return the model with no content."""
        nbm, meta = self._nbm_from_path(path)
        model['path'] = meta.path
        return nbm.update(model, meta.path)

    def delete(self, path):
        """Delete notebook by name and path."""
        nbm, meta = self._nbm_from_path(path)
        return nbm.delete(meta.path)

    def create_checkpoint(self, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.create_checkpoint(meta.path)

    def list_checkpoints(self, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.list_checkpoints(meta.path)

    def restore_checkpoint(self, checkpoint_id, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.restore_checkpoint(checkpoint_id, meta.path)

    def delete_checkpoint(self, checkpoint_id, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.delete_checkpoint(checkpoint_id, meta.path)

    # ContentsManager API part 2: methods that have useable default
    # implementations, but can be overridden in subclasses.

    # Note, some of these just call the default ContentsManager
    # implementation. In reality, they won't need to ever be overridden.
    def info_string(self):
        infos = [nbm.info_string() for nbm in self.managers.values()]
        return "\n".join(infos)

    def get_kernel_path(self,  path):
        """ defined where kernel for notebooks is started """
        nbm, meta = self._nbm_from_path(path)
        return nbm.get_kernel_path(meta.path)

    def increment_filename(self, filename, path=''):
        nbm, meta = self._nbm_from_path(path)
        return nbm.get_kernel_path(filename, meta.path)

    def create_file(self, model=None, path='', ext='.ipynb'):
        nbm, meta = self._nbm_from_path(path)
        model = nbm.create_file(model, meta.path, ext)
        model['path'] = path
        return model

    def copy(self, from_name, to_name=None, path=''):
        nbm, meta = self._nbm_from_path(path)
        model = nbm.copy(from_name, to_name, meta.path)
        model['path'] = path
        return model

    def trust_notebook(self, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.trust_notebook(meta.path)

    def check_and_sign(self, nb, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.check_and_sign(nb, meta.path)

    def mark_trusted_cells(self, nb, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.mark_trusted_cells(nb, meta.path)

    ## END ContentsManager API

    # StaticFileHandler
    def get_absolute_path(self, path):
        """ return absolute path for static file handler """
        nbm, meta = self._nbm_from_path(path)
        return nbm.get_absolute_path(meta.path)
