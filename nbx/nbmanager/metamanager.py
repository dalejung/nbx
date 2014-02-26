import os

from IPython.utils.traitlets import (
    Dict, Unicode, Integer, List, Bool, Bytes,
    DottedObjectName, TraitError, Tuple,
)
from IPython.config.configurable import LoggingConfigurable
from IPython.html.services.notebooks.nbmanager import NotebookManager
from IPython.html.services.notebooks.filenbmanager import FileNotebookManager

from nbx.nbmanager.gistnbmanager import GistNotebookManager
from nbx.nbmanager.notebook_gisthub import notebook_gisthub


class MetaManager(LoggingConfigurable):
    """
        Holds NotebookManager classes and routes calls to the appropiate
        manager.
    """
    github_accounts = List(Tuple, config=True,
                           help="List of Tuple(github_account, github_password)")

    def __init__(self, *args, **kwargs):
        super(MetaManager, self).__init__(*args, **kwargs)
        self.managers = {}
        self.managers['file'] = FileNotebookManager()

        for user, pw in self.github_accounts:
            gh = notebook_gisthub(user, pw)
            gbm = GistNotebookManager(gisthub=gh)
            self.managers['gist:'+user] = gbm

        self.root = HomeManager(meta_manager=self)

    def _nbm_from_path(self, path):
        # we are on root
        if not path:
            return self.root, ''

        # remove beginning slash (/)
        if path[0] == os.sep:
            path = path[1:]
        bits = path.split(os.sep)
        manager_path = bits[0]
        local_path = os.sep.join(bits[1:])

        nbm = self.managers.get(manager_path)
        return nbm, local_path

    @property
    def notebook_dir(self):
        return self.managers['file'].notebook_dir

    def info_string(self):
        infos = [nbm.info_string() for nbm in self.managers.values()]
        return "\n".join(infos)

    def list_dirs(self, path):
        nbm, local_path = self._nbm_from_path(path)
        val = nbm.list_dirs(local_path)
        return val

    def path_exists(self, path):
        nbm, local_path = self._nbm_from_path(path)
        if nbm is None:
            return False
        return nbm.path_exists(local_path)

    def create_notebook(self, model=None, path=''):
        """Create a new notebook and return its model with no content."""
        nbm, local_path = self._nbm_from_path(path)
        return nbm.create_notebook(model=model, path=local_path)

    def list_notebooks(self, path=''):
        nbm, local_path = self._nbm_from_path(path)
        val = nbm.list_notebooks(local_path)
        return val

    def is_hidden(self, path):
        nbm, local_path = self._nbm_from_path(path)
        return nbm.is_hidden(local_path)

    def notebook_exists(self, name, path):
        nbm, local_path = self._nbm_from_path(path)
        return nbm.notebook_exists(name, local_path)

    def get_notebook(self, name, path='', content=True):
        nbm, local_path = self._nbm_from_path(path)
        model = nbm.get_notebook(name, path=local_path, content=content)
        return model

    def save_notebook(self, model, name='', path=''):
        nbm, local_path = self._nbm_from_path(path)
        # make sure path is local and doesn't include sub manager prefix
        model['path'] = local_path
        model = nbm.save_notebook(model=model, name=name, path=local_path)
        return model

    def update_notebook(self, model, name, path=''):
        """Update the notebook and return the model with no content."""
        nbm, local_path = self._nbm_from_path(path)
        return nbm.update_notebook(model, name, local_path)

    def delete_notebook(self, name, path=''):
        """Delete notebook by name and path."""
        nbm, local_path = self._nbm_from_path(path)
        return nbm.delete_notebook(name, local_path)

    def create_checkpoint(self, name, path=''):
        nbm, local_path = self._nbm_from_path(path)
        return nbm.create_checkpoint(name, local_path)

    def list_checkpoints(self, name, path=''):
        nbm, local_path = self._nbm_from_path(path)
        return nbm.list_checkpoints(name, local_path)

    def restore_checkpoint(self, checkpoint_id, name, path=''):
        nbm, local_path = self._nbm_from_path(path)
        return nbm.restore_checkpoint(checkpoint_id, name, local_path)

    def delete_checkpoint(self, checkpoint_id, name, path=''):
        nbm, local_path = self._nbm_from_path(path)
        return nbm.delete_checkpoint(checkpoint_id, name, local_path)

class HomeManager(NotebookManager):
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
        model['path'] = name
        model['type'] = 'directory'
        return model

    def list_dirs(self, path):
        return self._list_nbm_dirs()

    def list_notebooks(self, path=''):
        return []

    def info_string(self):
        return ''
