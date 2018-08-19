import os
import io
import shutil

from .bundle import NotebookBundle

import nbformat
from nbformat import sign
current = nbformat.v4


def is_notebook(path):
    # checks if path follows bundle format
    if not path.endswith('.ipynb'):
        return False
    # if that we have same named ipynb file in directory
    name = path.rsplit('/', 1)[-1]
    file_path = os.path.join(path, name)
    has_file = os.path.isfile(file_path)
    return has_file


def _list_bundles(path):
    root, dirs, files = next(os.walk(path))
    bundles = (os.path.join(root, d) for d in dirs)
    bundles = filter(lambda path: is_notebook(path), bundles)
    bundles = list(bundles)
    return bundles


class BundleManager(object):
    bundle_class = NotebookBundle

    def __init__(self, bundle_class=None):
        if bundle_class:
            self.bundle_class = bundle_class

    def _new_notebook(self):
        model = {}
        model['type'] = 'notebook'
        model['content'] = current.new_notebook(metadata={'name': u''})
        return model

    def _get_bundle_path(self, path):
        return path

    def _get_nb_path(self, path):
        bundle_path = self._get_bundle_path(path)
        name = path.rsplit('/', 1)[-1]
        nb_path = os.path.join(bundle_path, name)
        return nb_path

    def save_notebook(self, model, path=''):
        """
        Save notebook model to file system.

        Note: This differs from the NotebookManager.save_notebook in that
        it doesn't have a rename check.
        """
        if not self.is_writable(path):
            raise Exception("Notebook target is not writable")

        bundle_path = self._get_bundle_path(path)
        if not os.path.exists(bundle_path):
            os.mkdir(bundle_path)

        nb = nbformat.from_dict(model['content'])

        notary = sign.NotebookNotary()
        if notary.check_cells(nb):
            notary.sign(nb)

        self.write_notebook(bundle_path, nb)

        if '__files' in model:
            self.write_files(bundle_path, model)

    def write_notebook(self, bundle_path, nb):
        nb_path = self._get_nb_path(bundle_path)
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
        path
        if not os.path.exists(path):
            return True
        # if path exists, only writable if it is a directory notebook
        if is_notebook(path):
            return True

        return False

    def rename_notebook(self, path, new_path):
        name = path.rsplit('/', 1)[-1]
        new_name = new_path.rsplit('/', 1)[-1]
        # Should we proceed with the move?
        if os.path.exists(new_path):
            raise Exception("Notebook bundle already exists")

        old_notebook_file = os.path.join(path, name)
        new_notebook_file = os.path.join(path, new_name)
        # first move the notebook file
        try:
            os.rename(old_notebook_file, new_notebook_file)
        except Exception as e:
            raise Exception(
                u'Unknown error renaming notebook: %s %s' % (path, e)
            )

        # finally move the bundle folder
        try:
            os.rename(path, new_path)
        except Exception as e:
            raise Exception(
                u'Unknown error renaming notebook: %s %s' % (path, e)
            )

    def get_notebook(self, path):
        bundle = self.bundle_class(path)
        return bundle

    def list_bundles(self, path):
        """
        Get list of bundles in a certain path
        """
        cls = self.bundle_class
        bundles = _list_bundles(path)
        bundles = dict([(path, cls(path)) for path in bundles])
        return bundles

    def list_bundles_by_name(self, path):
        """
        Get list of bundles in a certain path
        """
        bundles = self.list_bundles(path)
        return {bundle.name: bundle for bundle in bundles.values()}

    def list_dirs(self, path):
        """
        Return list of dir names
        """
        if not os.path.isdir(path):
            raise Exception("{path} is not a directory".format(path=path))
        root, dirs, files = next(os.walk(path))
        # remove dirs that are notebooks
        bundles = filter(
            lambda d: not is_notebook(os.path.join(root, d)),
            dirs
        )
        return bundles

    def copy_notebook_file(self, path, cp_path=None):
        nb_path = self._get_nb_path(path)
        shutil.copy2(nb_path, cp_path)
