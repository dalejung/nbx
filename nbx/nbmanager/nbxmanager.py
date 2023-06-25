import datetime

from jupyter_server.services.contents.manager import ContentsManager

from .dispatch import DispatcherMixin


class NBXContentsManager(DispatcherMixin, ContentsManager):
    def __init__(self, *args, **kwargs):
        super(NBXContentsManager, self).__init__(*args, **kwargs)

    def is_dir(self, path):
        raise NotImplementedError('must be implemented in a subclass')

    def is_notebook(self, path):
        return path.endswith('.ipynb')

    def _base_model(self, path=''):
        """Build the common base of a contents model"""
        # Create the base model.
        model = {}
        model['name'] = path.rsplit('/', 1)[-1]
        model['path'] = path
        model['created'] = datetime.datetime.now()
        model['last_modified'] = datetime.datetime.now()
        model['content'] = None
        model['format'] = None
        model['writable'] = None
        model['mimetype'] = None
        return model

    def get(self, path='', content=True, **kwargs):
        """
        backwards compat with get_model rename. fml.
        Putting here instead of creating another mixin
        """
        return super().get(path=path, content=content, **kwargs)

    # shims to bridge Content service and older notebook apis
    def get_dir(self, path='', content=True, **kwargs):
        """
        retrofit to use old list_dirs. No notebooks
        note that this requires the dispatcher mixin
        """
        model = self._base_model(path)
        fullpath = path

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
