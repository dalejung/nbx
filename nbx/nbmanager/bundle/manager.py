import os
import io
import shutil

from .bundle import NotebookBundle

from IPython import nbformat
from IPython.nbformat import sign
current = nbformat.v4

def is_notebook(path):
    name = path.rsplit('/', 1)[-1]
    # checks if path follows bundle format
    if not name.endswith('.ipynb'):
        return False
    # if that we have same named ipynb file in directory
    file_path = os.path.join(path, name)
    has_file = os.path.isfile(file_path)
    return has_file

def _list_bundles(path):
    root, dirs, files = next(os.walk(path))
    dirs = filter(lambda d: is_notebook(d, root), dirs)
    return dirs

class BundleManager(object):
    bundle_class = NotebookBundle

    def __init__(self, bundle_class=None):
        if bundle_class:
            self.bundle_class = bundle_class

    def _get_bundle_path(self, path):
        return path

    def _get_nb_path(self, path):
        name = path.rsplit('/', 1)[-1]
        bundle_path = self._get_bundle_path(path)
        nb_path = os.path.join(bundle_path, name)
        return nb_path

    def save_notebook(self, model, path):
        """
        Save notebook model to file system.

        Note: This differs from the NotebookManager.save_notebook in that
        it doesn't have a rename check.
        """
        name = path.rsplit('/', 1)[-1]
        if not self.is_writable(path):
            raise Exception("Notebook target is not writable")

        if not os.path.exists(path):
            os.mkdir(path)

        nb = nbformat.from_dict(model['content'])

        #self.check_and_sign(nb, name, path)
        notary = sign.NotebookNotary()
        if notary.check_cells(nb):
            notary.sign(nb)

        self.write_notebook(path, nb)

        if '__files' in model:
            self.write_files(path, model)

    def write_notebook(self, path, nb):
        name = path.rsplit('/', 1)[-1]
        nb_path = os.path.join(path, name)
        if 'name' in nb['metadata']:
            nb['metadata']['name'] = u''
        try:
            with io.open(nb_path, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f, version=nbformat.NO_CONVERT)
        except Exception as e:
            raise Exception(u'Unexpected error while autosaving notebook: %s %s' % (nb_path, e))

    def write_files(self, bundle_path, model):
        # write files
        files = model.get('__files')
        for fn, fcontent in files.items():
            filepath = os.path.join(bundle_path, fn)
            with open(filepath, 'w') as f:
                f.write(fcontent)

    def notebook_exists(self, path):
        return is_notebook(path)

    def is_writable(self, path):
        bundle_path = path
        if not os.path.exists(bundle_path):
            return True
        # if path exists, only writable if it is a directory notebook
        if is_notebook(path):
            return True

        return False

    def rename_notebook(self, path, new_path):
        if path != new_path :
            raise NotImplementedError('Moving directories not supported')

        name = path.rsplit('/', 1)[-1]
        new_name = new_path.rsplit('/', 1)[-1]
        bundle_path = os.path.join(path, name)
        new_bundle_path = os.path.join(new_path, new_name)
        # Should we proceed with the move?
        if os.path.exists(new_bundle_path):
            raise Exception("Notebook bundle already exists")

        old_notebook_file = os.path.join(bundle_path, name)
        new_notebook_file = os.path.join(bundle_path, new_name)
        # first move the notebook file
        try:
            os.rename(old_notebook_file, new_notebook_file)
        except Exception as e:
            raise Exception(u'Unknown error renaming notebook: %s %s' % (bundle_path, e))

        # finally move the bundle folder
        try:
            os.rename(bundle_path, new_bundle_path)
        except Exception as e:
            raise Exception(u'Unknown error renaming notebook: %s %s' % (bundle_path, e))

    def get_notebook(self, path):
        name = path.rsplit('/', 1)[-1]
        bundle = self.bundle_class(name, path)
        return bundle

    def list_bundles(self, path):
        """
        Get list of bundles in a certain path
        """
        cls = self.bundle_class
        bundles = _list_bundles(path)
        bundles = dict([(name, cls(name, path)) for name in bundles])
        return bundles

    def list_dirs(self, path):
        """
        Return list of dir names
        """
        if not os.path.isdir(path):
            raise Exception("{path} is not a directory".format(path=path))
        root, dirs, files = next(os.walk(path))
        # remove dirs that are notebooks
        dirs = filter(lambda path: not is_notebook(path), dirs)
        return dirs

    def copy_notebook_file(self, path, cp_path=None):
        nb_path = self._get_nb_path(path)
        shutil.copy2(nb_path, cp_path)
