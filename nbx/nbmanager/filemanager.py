from IPython.html.services.contents.manager import ContentsManager
from IPython.html.services.contents.filemanager import FileContentsManager
from IPython.html.utils import url_path_join

from .nbxmanager import NBXContentsManager, BackwardsCompatMixin

def _fullpath(name, path):
    fullpath = url_path_join(path, name)
    return fullpath

class BackwardsFileContentsManager(ContentsManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filemanager = FileContentsManager(*args, **kwargs)

    def get_notebook(self, name, path='', content=True, **kwargs):
        model = self.get(name, path, content=content, **kwargs)
        # note, since this is calling IPython's .get, the model
        # path will be the newer full path. reset it since we're
        # translating back in MetaManager.
        model['path'] = path
        return model

    def get_model(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    # this is dumb, quite literally just translating back

    def is_hidden(self, path):
        return self.filemanager.is_hidden(path)

    def get(self, name, path, **kwargs):
        path = _fullpath(name, path)
        model =  self.filemanager.get(path, **kwargs)
        return model

    def save(self, model, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.save(model, path)

    def update(self, model, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.update(model, path)

    def delete(self, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.delete(path)

    def rename(self, old_name, old_path, new_name, new_path):
        path = _fullpath(name, path)
        return self.filemanager.rename(old_path, new_path)

    def file_exists(self, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.file_exists(path)

    def path_exists(self, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.exists(path)

    def exists(self, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.exists(path)

    # checkpoint stuff
    def get_checkpoint_path(self, checkpoint_id, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.get_checkpoint_path(checkpoint_id, path)

    def get_checkpoint_model(self, checkpoint_id, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.get_checkpoint_model(checkpoint_id, path)

    def create_checkpoint(self, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.create_checkpoint(path)

    def list_checkpoints(self, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.list_checkpoints(path)

    def restore_checkpoint(self, checkpoint_id, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.restore_checkpoint(checkpoint_id, path)

    def delete_checkpoint(self, checkpoint_id, name, path=''):
        path = _fullpath(name, path)
        return self.filemanager.delete_checkpoint(checkpoint_id, path)

    def get_kernel_path(self, name, path='', model=None):
        path = _fullpath(name, path)
        return self.filemanager.get_kernel_path(path, model=model)

