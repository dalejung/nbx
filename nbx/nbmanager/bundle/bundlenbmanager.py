import itertools
import os.path

from tornado import web

from IPython.utils.traitlets import Unicode
from IPython.utils import tz
from IPython.html.services.notebooks.nbmanager import NotebookManager
from IPython.html.services.notebooks.filenbmanager import FileNotebookManager
from IPython.nbformat import current
from IPython.html.utils import is_hidden, to_os_path

from nbx.nbmanager.bundle.manager import BundleManager

class BundleNotebookManager(NotebookManager):
    """
    """
    notebook_dir = Unicode()

    def __init__(self, *args, **kwargs):
        super(BundleNotebookManager, self).__init__(*args, **kwargs)
        self.bundler = BundleManager()

    def _get_os_path(self, name=None, path=''):
        """Given a notebook name and a URL path, return its file system
        path.

        Parameters
        ----------
        name : string
            The name of a notebook file with the .ipynb extension
        path : string
            The relative URL path (with '/' as separator) to the named
            notebook.

        Returns
        -------
        path : string
            A file system path that combines notebook_dir (location where
            server started), the relative path, and the filename with the
            current operating system's url.
        """
        if name is not None:
            path = path + '/' + name
        return to_os_path(path, self.notebook_dir)

    def path_exists(self, path):
        path = path.strip('/')
        os_path = self._get_os_path(path=path)
        return os.path.isdir(os_path)

    def notebook_exists(self, name, path=''):
        path = path.strip('/')
        os_path = self._get_os_path(path=path)
        return self.bundler.notebook_exists(name, os_path)

    def is_hidden(self, path):
        return False

    def get_dir_model(self, name, path):
        model = {}
        model['name'] = name
        model['path'] = path
        model['type'] = 'directory'
        return model

    def list_dirs(self, path):
        os_path = self._get_os_path(path=path)
        dirs = self.bundler.list_dirs(os_path)
        dirs = [self.get_dir_model(name, os_path) for name in dirs]
        return dirs

    def list_notebooks(self, path):
        os_path = self._get_os_path(path=path)
        bundles = self.bundler.list_bundles(os_path)
        notebooks = []
        for name, bundle in bundles.items():
            model = self.get_notebook(name, path, content=False)
            notebooks.append(model)
        return notebooks

    def get_notebook(self, name, path='', content=True):
        """ Takes a path and name for a notebook and returns its model

        Parameters
        ----------
        name : str
            the name of the notebook
        path : str
            the URL path that describes the relative path for
            the notebook

        Returns
        -------
        model : dict
            the notebook model. If contents=True, returns the 'contents' 
            dict in the model as well.
        """
        path = path.strip('/')
        if not self.notebook_exists(name=name, path=path):
            raise Exception('Notebook does not exist {name} {path}'.format(name=name,
                                                                           path=path))
        os_path = self._get_os_path(name, path)
        info = os.stat(os_path)
        last_modified = tz.utcfromtimestamp(info.st_mtime)
        created = tz.utcfromtimestamp(info.st_ctime)
        # Create the notebook model.
        model ={}
        model['name'] = name
        model['path'] = path
        model['last_modified'] = last_modified
        model['created'] = created
        model['type'] = 'notebook'
        if content:
            with io.open(os_path, 'r', encoding='utf-8') as f:
                try:
                    nb = current.read(f, u'json')
                except Exception as e:
                    raise web.HTTPError(400, u"Unreadable Notebook: %s %s" % (os_path, e))
            self.mark_trusted_cells(nb, name, path)
            model['content'] = nb
        return model

    def save_notebook(self, model, name='', path=''):
        """Save the notebook model and return the model with no content."""
        path = path.strip('/')

        if 'content' not in model:
            raise Exception(u'No notebook JSON data provided')

        # One checkpoint should always exist
        # if self.notebook_exists(name, path) and not self.list_checkpoints(name, path):
        #     self.create_checkpoint(name, path)
        abspath = self._get_os_path(name=None, path=path)
        self.bundler.save_notebook(model, name=name, path=abspath)

        #model = self.get_notebook(new_name, new_path, content=False)
        return model