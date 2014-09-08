import datetime

from IPython.html.services.contents.manager import ContentsManager
from IPython.html.utils import url_path_join

class NBXContentsManager(ContentsManager):

    def is_dir(self, path):
        raise NotImplementedError('must be implemented in a subclass')

    def get_model(self, name, path='', content=True):
        path = path.strip('/')

        fullpath = url_path_join(name, path)
        if self.is_dir(fullpath):
            model = self.get_model_dir(name, path, content)
        elif name.endswith('.ipynb'):
            model = self.get_model_notebook(name, path, content)
        else:
            model = self.get_model_file(name, path, content)
        return model

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
