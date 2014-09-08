import itertools
import os

from tornado import web

from IPython.utils.traitlets import Unicode
from IPython.utils import tz
from IPython.nbformat import current
from IPython.html.utils import is_hidden, to_os_path

from .manager import BundleManager
from ..nbxmanager import NBXContentsManager

class BundleNotebookManager(NBXContentsManager):
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

    def get_kernel_path(self, name, path='', model=None):
        # get into bundle dir
        bundle_path = self.bundler._get_bundle_path(name, path)
        return os.path.join(self.notebook_dir, bundle_path)

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
            model = bundle.get_model(content=False)
            # the model returned from BundleManager is absolute
            # set back to relative
            model['path'] = path
            notebooks.append(model)
        return notebooks

    def is_dir(self, path):
        os_path = os.path.join(self.root_dir, path)
        return os.path.isdir(os_path)

    def get_model_dir(self, name, path='', content=True):
        """ retrofit to use old list_dirs. No notebooks """
        model = self._base_model(name, path)
        model['type'] = 'directory'
        dirs = self.list_dirs(path)
        notebooks = self.list_notebooks(path)
        entries = dirs + notebooks
        model['content'] = entries
        return model

    def get_notebook(self, name, path='', content=True, file_content=False):
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
        os_path = self._get_os_path(name=None, path=path)
        bundle = self.bundler.get_notebook(name, os_path)
        model = bundle.get_model(content=content, file_content=file_content)
        model['path'] = path
        return model

    def save_notebook(self, model, name='', path=''):
        """Save the notebook model and return the model with no content."""
        path = path.strip('/')

        if 'content' not in model:
            raise Exception(u'No notebook JSON data provided')

        if self.notebook_exists(name, path) and not self.list_checkpoints(name, path):
            self.create_checkpoint(name, path)

        abspath = self._get_os_path(name=None, path=path)
        self.bundler.save_notebook(model, name=name, path=abspath)

        model = self.get_notebook(name, path, content=False)
        return model

    def update_notebook(self, model, name, path=''):
        """Update the notebook's path and/or name"""
        path = path.strip('/')
        new_name = model.get('name', name)
        new_path = model.get('path', path).strip('/')
        if path != new_path or name != new_name:
            self.rename_notebook(name, path, new_name, new_path)

        model = self.get_notebook(new_name, new_path, content=False)
        return model

    def rename_notebook(self, name, path, new_name, new_path):
        """Update the notebook's path and/or name"""
        os_path = self._get_os_path(path=path)
        new_os_path = self._get_os_path(path=new_path)

        if path != new_path or name != new_name:
            self.bundler.rename_notebook(name, os_path, new_name, new_os_path)
        model = self.get_notebook(new_name, new_path, content=False)
        return model

    # Checkpoint-related utilities
    def _get_checkpoint_dir(self, name, path=''):
        checkpoint_dir = os.path.join(path, name, '.ipynb_checkpoints')
        return checkpoint_dir

    def get_checkpoint_path(self, checkpoint_id, name, path=''):
        """find the path to a checkpoint"""
        path = path.strip('/')
        checkpoint_dir = self._get_checkpoint_dir(name, path)
        basename, _ = os.path.splitext(name)
        filename = u"{name}-{checkpoint_id}{ext}".format(
            name=basename,
            checkpoint_id=checkpoint_id,
            ext=self.filename_ext,
        )
        cp_path = os.path.join(checkpoint_dir, filename)
        return cp_path

    def get_checkpoint_model(self, checkpoint_id, name, path=''):
        """construct the info dict for a given checkpoint"""
        path = path.strip('/')
        cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
        os_cp_path = self._get_os_path(path=cp_path)
        stats = os.stat(os_cp_path)
        last_modified = tz.utcfromtimestamp(stats.st_mtime)
        info = dict(
            id = checkpoint_id,
            last_modified = last_modified,
        )
        return info

    # checkpoint stuff
    def create_checkpoint(self, name, path=''):
        checkpoint_id = u"checkpoint"
        checkpoint_dir = self._get_checkpoint_dir(name, path)
        os_checkpoint_dir = self._get_os_path(path=checkpoint_dir)
        if not os.path.exists(os_checkpoint_dir):
            os.mkdir(os_checkpoint_dir)

        os_path = self._get_os_path(path=path)
        cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
        os_cp_path = self._get_os_path(cp_path)
        self.bundler.copy_notebook_file(name, os_path, os_cp_path)

        # return the checkpoint info
        return self.get_checkpoint_model(checkpoint_id, name, path)

    def list_checkpoints(self, name, path=''):
        """Return a list of checkpoints for a given notebook"""
        path = path.strip('/')
        checkpoint_id = "checkpoint"
        cp_path = self.get_checkpoint_path(checkpoint_id, name, path)
        os_path = self._get_os_path(cp_path)
        if not os.path.exists(os_path):
            return []
        else:
            return [self.get_checkpoint_model(checkpoint_id, name, path)]

    def restore_checkpoint(self, checkpoint_id, name, path=''):
        """Restore a notebook from one of its checkpoints"""
        raise NotImplementedError("must be implemented in a subclass")

    def delete_checkpoint(self, checkpoint_id, name, path=''):
        """delete a checkpoint for a notebook"""
        raise NotImplementedError("must be implemented in a subclass")

