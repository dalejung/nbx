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

from nbx.nbmanager.tagged_gist.gistnbmanager import GistNotebookManager
from nbx.nbmanager.tagged_gist.notebook_gisthub import notebook_gisthub
from nbx.nbmanager.bundle.bundlenbmanager import BundleNotebookManager

from IPython.html.base.zmqhandlers import ZMQStreamHandler
from IPython.html.utils import is_hidden, to_os_path, url_path_join

from .middleware import manager_hook

ZMQStreamHandler.same_origin = lambda self: True

class ManagerMeta(object):
    """
    """
    # the original request path, include the nbm alias
    request_path = None
    nbm_path = None

    # local name and path
    path = None
    name = None

class MetaManager(ContentsManager):
    """
        Holds NotebookManager classes and routes calls to the appropiate
        manager.
    """
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
            from nbx.handlers import enable_custom_handlers
            enable_custom_handlers()

        for alias, path in self.file_dirs.items():
            fb = FileContentsManager()
            fb.root_dir = path
            self.managers[alias] = fb

        for alias, path in self.bundle_dirs.items():
            fb = BundleNotebookManager()
            fb.notebook_dir = path
            self.managers[alias] = fb

        for user, pw in self.github_accounts:
            gh = notebook_gisthub(user, pw)
            gbm = GistNotebookManager(gisthub=gh)
            self.managers['gist:'+user] = gbm

        self.middleware = {}
        for name, middleware in self.manager_middleware.items():
            cls = import_item(middleware)
            self.middleware[name] = cls(parent=self, log=self.log)

        self.root = HomeManager(meta_manager=self)

    def dispatch_middleware(self, hook_name, *args, **kwargs):
        """
        dispatch hook calls to middleware
        """
        for name, middleware in self.middleware.items():
            method = getattr(middleware, hook_name, None)
            if method is not None:
                method(*args, **kwargs)

    def _nbm_from_path(self, path, name=None):
        meta = ManagerMeta()
        meta.request_path = self._get_fullpath(name, path)
        # get the nbm root path i.e. manager alias
        bits = os.path.split(meta.request_path)
        meta.nbm_path = bits and bits[0] or ''

        # we are on root
        if not path and not name:
            meta.path = ''
            meta.name = ''
            # assume this call won't need name.
            return self.root, meta

        # not sure where the semantic changed. But /blah now has
        # shows up as name='blah, path=''
        # special case the single root path bit
        if name is not None and not path:
            path = name
            name = ''

        # remove beginning slash (/)
        if path[0] == os.sep:
            path = path[1:]
        bits = path.split(os.sep)
        manager_path = bits[0]
        meta.path = os.sep.join(bits[1:])

        nbm = self.managers.get(manager_path)

        meta.name = name
        meta.path = meta.path
        return nbm, meta

    def _get_fullpath(self, name=None, path=''):
        if name is not None:
            path = url_path_join(path, name)
        return path

    @property
    def notebook_dir(self):
        return self.managers['server-home'].notebook_dir

    def info_string(self):
        infos = [nbm.info_string() for nbm in self.managers.values()]
        return "\n".join(infos)

    def list_dirs(self, path):
        nbm, meta = self._nbm_from_path(path)
        val = nbm.list_dirs(meta.path)
        return val

    # TODO remove?
    def path_exists(self, path):
        nbm, meta = self._nbm_from_path(path)
        if nbm is None:
            return False
        exists = nbm.path_exists(meta.path)
        return exists

    def exists(self, name, path):
        nbm, meta = self._nbm_from_path(path, name)
        if nbm is None:
            return False
        exists = nbm.exists(meta.name, meta.path)
        return exists

    def create_notebook(self, model=None, path=''):
        """Create a new notebook and return its model with no content."""
        nbm, meta = self._nbm_from_path(path)
        return nbm.create_notebook(model=model, path=meta.path)

    def list_notebooks(self, path=''):
        nbm, meta = self._nbm_from_path(path)
        val = nbm.list_notebooks(meta.path)
        return val

    def is_hidden(self, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.is_hidden(meta.path)

    # TODO remove?
    def notebook_exists(self, name, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.notebook_exists(name, meta.path)

    def file_exists(self, name, path):
        nbm, meta = self._nbm_from_path(path)
        return nbm.file_exists(name, meta.path)

    def get_notebook(self, name, path='', content=True):
        nbm, meta = self._nbm_from_path(path)
        model = nbm.get_notebook(name, path=meta.path, content=content)
        return model

    def get_model(self, name, path='', content=True):
        nbm, meta = self._nbm_from_path(path, name)
        model = nbm.get_model(meta.name, path=meta.path, content=content)

        # while the local manager doesn't know its nbm_path,
        # we have to add it back in for the metamanager.
        if model['type'] == 'directory':
            content = model.get("content", [])
            for m in content:
                m['path'] = meta.request_path
        return model

    @manager_hook
    def save_notebook(self, model, name='', path=''):
        nbm, meta = self._nbm_from_path(path)
        # make sure path is local and doesn't include sub manager prefix
        model['path'] = meta.path
        model = nbm.save_notebook(model=model, name=name, path=meta.path)
        return model

    def update_notebook(self, model, name, path=''):
        """Update the notebook and return the model with no content."""
        nbm, meta = self._nbm_from_path(path)
        return nbm.update_notebook(model, name, meta.path)

    def delete_notebook(self, name, path=''):
        """Delete notebook by name and path."""
        nbm, meta = self._nbm_from_path(path)
        return nbm.delete_notebook(name, meta.path)

    def create_checkpoint(self, name, path=''):
        nbm, meta = self._nbm_from_path(path)
        return nbm.create_checkpoint(name, meta.path)

    def list_checkpoints(self, name, path=''):
        nbm, meta = self._nbm_from_path(path)
        return nbm.list_checkpoints(name, meta.path)

    def restore_checkpoint(self, checkpoint_id, name, path=''):
        nbm, meta = self._nbm_from_path(path)
        return nbm.restore_checkpoint(checkpoint_id, name, meta.path)

    def delete_checkpoint(self, checkpoint_id, name, path=''):
        nbm, meta = self._nbm_from_path(path)
        return nbm.delete_checkpoint(checkpoint_id, name, meta.path)

    def get_kernel_path(self, name, path=''):
        nbm, meta = self._nbm_from_path(path)
        return nbm.get_kernel_path(name, meta.path)

class HomeManager(ContentsManager):
    """
    Handle the root path "/"

    Basically creates the psuedo home directory listing
    """
    def __init__(self, *args, **kwargs):
        self.meta_manager = kwargs.pop('meta_manager')
        super(HomeManager, self).__init__(*args, **kwargs)

    @property
    def managers(self):
        return self.meta_manager.managers

    def is_hidden(self, path):
        return False

    def path_exists(self, path):
        return True

    def _list_nbm_dirs(self):
        dirs = []
        for name in self.managers:
            model = self.get_dir_model(name)
            dirs.append(model)
        return dirs

    def get_dir_model(self, name):
        model ={}
        model['name'] = name
        model['path'] = ''
        model['type'] = 'directory'
        return model

    def list_dirs(self, path):
        return self._list_nbm_dirs()

    def list_notebooks(self, path=''):
        return []

    def info_string(self):
        return ''

    def _base_model(self, name, path=''):
        """Build the common base of a contents model"""
        # Create the base model.
        model = {}
        model['name'] = name
        model['path'] = path
        model['created'] = datetime.datetime.now()
        model['last_modified'] = datetime.datetime.now()
        model['content'] = None
        model['format'] = None
        return model

    def get_model(self, name, path='', content=True):
        """ retrofit to use old list_dirs. No notebooks """
        model = self._base_model(name, path)
        model['type'] = 'directory'
        dirs = self.list_dirs(path)
        model['content'] = dirs
        return model

