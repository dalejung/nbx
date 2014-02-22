import os

from IPython.config.configurable import LoggingConfigurable
from IPython.html.services.notebooks.nbmanager import NotebookManager
from IPython.html.services.notebooks.filenbmanager import FileNotebookManager

class MetaManager(LoggingConfigurable):
    """
        Holds NotebookManager classes and routes calls to the appropiate
        manager.
    """
    def __init__(self, *args, **kwargs):
        self.managers = {}
        self.managers['file'] = FileNotebookManager()
        self.root = HomeManager(meta_manager=self)
        super(MetaManager, self).__init__(*args, **kwargs)

    def __getattr__(self, name):
        print name
        val = getattr(self.managers['file'], name)
        return val

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

    def list_dirs(self, path):
        nbm, local_path = self._nbm_from_path(path)
        val = nbm.list_dirs(local_path)
        return val

    def path_exists(self, path):
        nbm, local_path = self._nbm_from_path(path)
        return nbm.path_exists(local_path)

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
        return nbm.get_notebook(name, path=local_path, content=content)

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
