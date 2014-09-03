"""
This is just a monkey patch module to allow the static file handler to
delegate the absolute path to the contentsmanager.

We also apply the method to the FileContentsManager since this isn't official
IPython api.
"""
import os.path

from tornado import web

def get_absolute_path(self, root, path):
    """
    So this is a bit kludgey. The tornado version of this is a classmethod.

    We are overridding it with an instancemthod so we have access to the
    contents_manager. In practice, this shouldn't affect anything, but it's
    something to note in prevent confusion.
    """
    cm = self.contents_manager
    if hasattr(cm, 'get_absolute_path'):
        abspath = cm.get_absolute_path(path)
    else:
        abspath = super(self.__class__, self).get_absolute_path(root, path)
    return abspath

def file_get_absolute_path(self, path):
    """
    monkey patch method for the FileContentsManager
    """
    return os.path.join(self.root_dir, path)

def patch_file_handler():
    from IPython.html.base.handlers import AuthenticatedFileHandler
    AuthenticatedFileHandler.get_absolute_path = get_absolute_path

    from IPython.html.services.contents.filemanager import FileContentsManager
    FileContentsManager.get_absolute_path = file_get_absolute_path
