import datetime

from notebook.services.contents.manager import ContentsManager

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
        model['format'] = 'json'
        return model

    def list_dirs(self, path):
        return self._list_nbm_dirs()

    def list_notebooks(self, path=''):
        return []

    def info_string(self):
        return ''

    def file_exists(self, name, path):
        return False

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
        model['writable'] = None
        model['mimetype'] = None
        return model

    def get_model(self, name, path='', content=True, **kwargs):
        """ retrofit to use old list_dirs. No notebooks """
        model = self._base_model(name, path)
        model['type'] = 'directory'
        dirs = self.list_dirs(path)
        model['content'] = dirs
        model['format'] = 'json'
        return model

