import datetime
import os.path

from notebook.services.contents.manager import ContentsManager
from IPython.html.utils import url_path_join

from .dispatch import DispatcherMixin

def _fullpath(name, path):
    fullpath = url_path_join(path, name)
    return fullpath

def _path_split(path):
    bits = path.rsplit('/', 1)
    path = ''
    name = bits.pop()
    if bits:
        path = bits[0]
    return name, path

class BackwardsCompatMixin(object):
    # shims to bridge Content service and older notebook apis
    def get_model_dir(self, name, path='', content=True, **kwargs):
        """
        retrofit to use old list_dirs. No notebooks
        note that this requires the dispatcher mixin
        """
        model = self._base_model(name, path)
        fullpath = self.fullpath(name, path)

        model['type'] = 'directory'
        model['format'] = 'json'
        dirs = self.list_dirs(fullpath)
        notebooks = self.list_notebooks(fullpath)

        files = []
        if hasattr(self, 'list_files'):
            files = self.list_files(fullpath)

        entries = list(dirs) + list(notebooks) + list(files)
        model['content'] = entries
        return model

    def get_model_notebook(self, name, path='', content=True, **kwargs):
        """
        note that this requires the dispatcher mixin
        """
        return self.get_notebook(name, path, content=content, **kwargs)

    def file_exists(self, name, path=''):
        # in old version, only file is notebook
        ret =  self.notebook_exists(name, path)
        return ret

    def is_notebook(self, path):
        """
        Note that is_notebook is a nbx method, it's in BackwardsCompatMixin
        because it uses old api

        split path into name, path and use notebook_exists
        """
        path, name = os.path.split(path)
        ret =  self.notebook_exists(name, path)
        return ret

    def is_dir(self, path):
        """
        nbx api method.
        """
        return self.path_exists(path) and not self.is_notebook(path)

    def dir_exists(self, path):
        return self.path_exists(path)

class NBXContentsManager(DispatcherMixin, ContentsManager):
    def __init__(self, *args, **kwargs):
        super(NBXContentsManager, self).__init__(*args, **kwargs)

    def is_dir(self, path):
        raise NotImplementedError('must be implemented in a subclass')

    def is_notebook(self, path):
        return path.endswith('.ipynb')

    def _base_model(self, name, path=''):
        """Build the common base of a contents model"""
        # Create the base model.
        model = {}
        model['name'] = name
        model['path'] = self.fullpath(name, path)
        model['created'] = datetime.datetime.now()
        model['last_modified'] = datetime.datetime.now()
        model['content'] = None
        model['format'] = None
        model['writable'] = None
        model['mimetype'] = None
        return model

    def fullpath(self, name, path):
        return _fullpath(name, path)

    def get(self, name, path='', content=True, **kwargs):
        """
        backwards compat with get_model rename. fml.
        Putting here instead of creating another mixin
        """
        if hasattr(self, 'get_model'):
            return self.get_model(name, path=path, content=content, **kwargs)
        return super().get(name, path=path, content=content, **kwargs)
