import datetime

from IPython.html.services.contents.manager import ContentsManager
from IPython.html.utils import url_path_join

class NBXContentsManager(ContentsManager):

    def is_dir(self, path):
        raise NotImplementedError('must be implemented in a subclass')

    def fullpath(self, name, path):
        fullpath = url_path_join(name, path)
        return fullpath

    def get_model(self, name, path='', content=True):
        path = path.strip('/')

        fullpath = self.fullpath(name, path)
        if self.is_dir(fullpath):
            model_type = 'dir'
        elif name.endswith('.ipynb'):
            model_type = 'notebook'
        else:
            model_type = 'file'
        return self._dispatch_method('get_model', model_type, name=name,
                              path=path, content=content)

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

    def save(self, model, name='', path=''):
        if 'type' not in model:
            raise Exception(u"Model has no file type")
        model_type = model['type']
        self._dispatch_method('save', model_type, model, name=name, path=path)

    def _dispatch_method(self, hook, model_type, *args, **kwargs):
        print('dispatch_method', hook, model_type)
        # call type specific hook
        method_name = "{hook}_{type}".format(hook=hook, type=model_type)
        method = getattr(self, method_name, None)
        if method:
            return method(*args, **kwargs)

        # try default
        default_name = '{hook}_default'.format(hook=hook)
        default_method = getattr(self, default_name)
        return default_method(model, name, path)

    def get_model_dir(self, name, path='', content=True):
        """ retrofit to use old list_dirs. No notebooks """
        model = self._base_model(name, path)
        fullpath = url_path_join(name, path)

        model['type'] = 'directory'
        dirs = self.list_dirs(fullpath)
        notebooks = self.list_notebooks(fullpath)
        entries = dirs + notebooks
        model['content'] = entries
        return model
