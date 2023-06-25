import datetime

from jupyter_server.services.contents.manager import ContentsManager


class RootManager(ContentsManager):
    """
    Handle the root path "/"

    Basically creates the psuedo home directory listing
    """
    def __init__(self, *args, **kwargs):
        self.meta_manager = kwargs.pop('meta_manager')
        super(RootManager, self).__init__(*args, **kwargs)

    @property
    def managers(self):
        return self.meta_manager.managers

    def is_hidden(self, path):
        return False

    def _list_nbm_dirs(self):
        dirs = []
        for name in self.managers:
            model = self._get_dir_model(name)
            dirs.append(model)
        return dirs

    def get(self, path, content=True, type=None, format=None):
        if type == 'directory':
            return self.get_dir(path)

    def _get_dir_model(self, name):
        model = {}
        model['name'] = name
        model['path'] = name
        model['type'] = 'directory'
        model['format'] = 'json'
        return model

    def list_dirs(self, path):
        return self._list_nbm_dirs()

    def list_notebooks(self, path=''):
        return []

    def info_string(self):
        return ''

    def file_exists(self, path):
        return False

    def dir_exists(self, path):
        return True

    def _base_model(self, path=''):
        """Build the common base of a contents model"""
        # Create the base model.
        model = {}
        model['name'] = path.rsplit('/', 1)[-1]
        model['path'] = path
        model['last_modified'] = datetime.datetime.now()
        model['created'] = datetime.datetime.now()
        model['content'] = None
        model['format'] = None
        model['writable'] = None
        model['mimetype'] = None
        return model

    def get_dir(self, path='', content=True, **kwargs):
        """ retrofit to use old list_dirs. No notebooks """
        model = self._base_model(path)
        model['type'] = 'directory'
        dirs = self.list_dirs(path)
        model['content'] = dirs
        model['format'] = 'json'
        return model
