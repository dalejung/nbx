import datetime
import itertools
import os
import inspect
import shutil
from functools import wraps

from tornado import web

from traitlets import Unicode
from IPython.utils import tz
from notebook.utils import is_hidden, to_os_path, url_path_join
from notebook.services.contents.filemanager import FileContentsManager

from .manager import BundleManager
from ..nbxmanager import NBXContentsManager
from ..dispatch import DispatcherMixin
from ..filemanager import BackwardsFileContentsManager
from .. import shim

def notebook_type_proxy(alt):
    """
    if notebook is a bundle, use regular method
    if notebook is file, defer to file manager
    """
    def decorator(meth):
        nonlocal alt
        meth_name = meth.__name__
        if alt is None:
            alt = meth_name
        argspec = inspect.getargspec(meth)

        @wraps(meth)
        def wrapper(self, *args, **kwargs):
            scope = kwargs.copy()
            # skip self in args
            scope.update(zip(argspec.args[1:], args))
            path = scope.get('path', '')

            method = meth.__get__(self)
            if self.notebook_type(path=path) == 'file':
                method = getattr(self.filemanager, alt)
            return method(*args, **kwargs)
        return wrapper
    return decorator

class BundleNotebookManager(NBXContentsManager):
    """
    """
    root_dir = Unicode()
    trash_dir = Unicode(config=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bundler = BundleManager()
        self.filemanager = FileContentsManager(*args, **kwargs)
        self.filemanager.root_dir = self.root_dir

    def _get_os_path(self, path=''):
        return to_os_path(path, self.root_dir)

    def is_dir(self, path):
        return self.dir_exists(path) and not self.is_notebook(path)

    @notebook_type_proxy(alt=None)
    def get_kernel_path(self, path='', model=None):
        # get into bundle dir
        bundle_path = self.bundler._get_bundle_path(path)
        return os.path.join(self.root_dir, bundle_path)

    def dir_exists(self, path):
        path = path.strip('/')
        os_path = self._get_os_path(path=path)
        return os.path.isdir(os_path)

    def file_exists(self, path):
        os_path = self._get_os_path(path=path)
        return os.path.isfile(os_path)

    def get_file(self, path='', content=True, **kwargs):
        os_path = self._get_os_path(path=path)
        return self.filemanager.get(path, content=content, **kwargs)

    def save_file(self, model, path=''):
        """Save the notebook model and return the model with no content."""

        model = self.filemanager.save(model, path)
        return model

    @notebook_type_proxy(alt='exists')
    def notebook_exists(self, path=''):
        return self._notebook_exists(path)

    def _notebook_exists(self, path):
        path = path.strip('/')
        os_path = self._get_os_path(path=path)
        return self.bundler.notebook_exists(os_path)

    def notebook_type(self, path=''):
        if self._notebook_exists(path):
            return 'bundle'
        if self.filemanager.exists(path) and path.endswith('ipynb'):
            return 'file'
        return None

    def is_hidden(self, path):
        return False

    def get_dir_model(self, path):
        model = {}
        model['name'] = path.rsplit('/', 1)[-1]
        model['path'] = path
        model['type'] = 'directory'
        return model

    def list_dirs(self, path):
        os_path = self._get_os_path(path=path)
        dirs = self.bundler.list_dirs(os_path)
        dirs = [self.get_dir_model(path) for path in dirs]
        return dirs

    def list_notebooks(self, path):
        os_path = self._get_os_path(path=path)
        bundles = self.bundler.list_bundles(os_path)
        notebooks = []
        for bundle_path, bundle in bundles.items():
            model = bundle.get_model(content=False)
            # the model returned from BundleManager is absolute
            # set back to relative
            model['path'] = os.path.join(path, bundle.name)
            notebooks.append(model)

        # also grab regular notebooks
        dir_model = self.filemanager.get(path=path, content=True)
        for model in dir_model['content']:
            if model['type'] == 'notebook':
                notebooks.append(model)

        return notebooks

    def list_files(self, path):
        os_path = self._get_os_path(path=path)
        notebooks = []

        # also grab regular notebooks
        dir_model = self.filemanager.get(path=path, content=True)
        for model in dir_model['content']:
            if model['type'] == 'file':
                notebooks.append(model)

        return notebooks


    @notebook_type_proxy(alt='get')
    def get_notebook(self, path='', content=True, file_content=False, **kwargs):
        path = path.strip('/')
        if not self.notebook_exists(path=path):
            raise Exception(
                'Notebook does not exist {path}'.format(
                    path=path
                )
            )
        os_path = self._get_os_path(path=path)
        bundle = self.bundler.get_notebook(os_path)
        model = bundle.get_model(content=content, file_content=file_content)
        model['path'] = path
        model['format'] = None
        if content:
            model['format'] = 'json'
        model['writable'] = True
        model['mimetype'] = None
        return model

    @notebook_type_proxy(alt='save')
    def save_notebook(self, model, path=''):
        """Save the notebook model and return the model with no content."""
        path = path.strip('/')

        if 'content' not in model:
            raise Exception(u'No notebook JSON data provided')

        if self.notebook_exists(path) and not self.list_checkpoints(path):
            self.create_checkpoint(path)

        abspath = self._get_os_path(path=path)
        self.bundler.save_notebook(model, path=abspath)

        model = self.get_notebook(path, content=False)
        return model

    @notebook_type_proxy(alt='update')
    def update_notebook(self, model, path=''):
        """Update the notebook's path and/or name"""
        path = path.strip('/')
        new_path = model.get('path', path).strip('/')
        if path != new_path:
            self.rename_notebook(path, new_path)

        model = self.get_notebook(new_path, content=False)
        return model

    @notebook_type_proxy(alt='rename')
    def rename_notebook(self, path, new_path):
        """Update the notebook's path and/or name"""
        os_path = self._get_os_path(path=path)
        new_os_path = self._get_os_path(path=new_path)

        if path != new_path:
            self.bundler.rename_notebook(os_path, new_os_path)
        print(new_path)
        model = self.get_notebook(new_path, content=False)
        return model

    @notebook_type_proxy(alt='delete')
    def delete_notebook(self, path):
        if not self.trash_dir:
            raise Exception("Removing bundle not implemented. Add trash_dir")
            return

        # get into bundle dir
        bundle_path = self.bundler._get_bundle_path(path)
        bundle_path = os.path.join(self.root_dir, bundle_path)

        trash_name = path.replace(os.path.sep, '__')

        trash_path = os.path.join(self.trash_dir, trash_name)

        i = 0
        while os.path.exists(trash_path):
            bits = trash_name.rsplit('.')
            bits[0] = bits[0] + '-' + str(i)
            trash_name = '.'.join(bits)
            trash_path = os.path.join(self.trash_dir, trash_name)

        shutil.move(bundle_path, trash_path)

    # Checkpoint-related utilities
    def _get_checkpoint_dir(self, path=''):
        checkpoint_dir = os.path.join(path, '.ipynb_checkpoints')
        return checkpoint_dir

    @notebook_type_proxy(alt=None)
    def get_checkpoint_path(self, checkpoint_id, path=''):
        """find the path to a checkpoint"""
        path = path.strip('/')
        checkpoint_dir = self._get_checkpoint_dir(path)
        name = path.rsplit('/', 1)[-1]
        basename, ext = os.path.splitext(name)
        filename = u"{name}---{checkpoint_id}{ext}".format(
            name=basename,
            checkpoint_id=checkpoint_id,
            ext=ext,
        )
        cp_path = os.path.join(checkpoint_dir, filename)
        return cp_path

    @notebook_type_proxy(alt=None)
    def get_checkpoint_model(self, checkpoint_id, path=''):
        """construct the info dict for a given checkpoint"""
        path = path.strip('/')
        cp_path = self.get_checkpoint_path(checkpoint_id, path)
        os_cp_path = self._get_os_path(path=cp_path)
        stats = os.stat(os_cp_path)
        last_modified = tz.utcfromtimestamp(stats.st_mtime)
        info = dict(
            id = checkpoint_id,
            last_modified = last_modified,
        )
        return info

    # checkpoint stuff
    @notebook_type_proxy(alt=None)
    def create_checkpoint(self, path=''):
        now = datetime.datetime.now()
        checkpoint_id = now.strftime("%Y-%m-%d %H:%M:%S")
        checkpoint_dir = self._get_checkpoint_dir(path)
        os_checkpoint_dir = self._get_os_path(path=checkpoint_dir)
        if not os.path.exists(os_checkpoint_dir):
            os.mkdir(os_checkpoint_dir)

        os_path = self._get_os_path(path=path)
        cp_path = self.get_checkpoint_path(checkpoint_id, path)
        os_cp_path = self._get_os_path(cp_path)
        self.bundler.copy_notebook_file(os_path, os_cp_path)

        # return the checkpoint info
        return self.get_checkpoint_model(checkpoint_id, path)

    @notebook_type_proxy(alt=None)
    def list_checkpoints(self, path=''):
        """Return a list of checkpoints for a given notebook"""
        path = path.strip('/')

        checkpoint_dir = self._get_checkpoint_dir(path)
        os_checkpoint_dir = self._get_os_path(path=checkpoint_dir)
        if not os.path.exists(os_checkpoint_dir):
            return []

        name = path.rsplit('/', 1)[-1]
        basename, ext = os.path.splitext(name)
        prefix = "{name}---".format(name=basename)

        _, _, files = next(os.walk(os_checkpoint_dir))
        cp_names = [fn for fn in files if fn.startswith(prefix)]
        cp_basenames = map(lambda fn: os.path.splitext(fn)[0], cp_names)
        checkpoint_ids = map(lambda fn: fn.replace(prefix, ''), cp_basenames)
        return [self.get_checkpoint_model(checkpoint_id, path)
                for checkpoint_id in checkpoint_ids]

    def extract_checkpoint_id(self, path):
        """
        Not currently used...

        extra checkpoint_id from strings of form
        "{basename}---{checkpoint_id}.ipynb"
        """
        name = path.rsplit('/', 1)[-1]
        basename, ext = os.path.splitext(name)
        checkpoint_basename, _ = os.path.splitext(name)
        prefix = "{name}---".format(name=basename)
        return checkpoint_basename.replace(prefix, '')

    @notebook_type_proxy(alt=None)
    def restore_checkpoint(self, checkpoint_id, path=''):
        """Restore a notebook from one of its checkpoints"""
        raise NotImplementedError("must be implemented in a subclass")

    @notebook_type_proxy(alt=None)
    def delete_checkpoint(self, checkpoint_id, path=''):
        """delete a checkpoint for a notebook"""
        raise NotImplementedError("must be implemented in a subclass")

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],
                  exit=False)
