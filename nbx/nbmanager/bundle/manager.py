import os
import io

from nbx.nbmanager.bundle.bundle import NotebookBundle

from IPython.nbformat import current, sign

def is_notebook(name, path):
    # checks if path follows bundle format
    if not name.endswith('.ipynb'):
        return False
    # if that we have same named ipynb file in directory
    file_path = os.path.join(path, name, name)
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

    def new_notebook(self):
        model = {}
        metadata = current.new_metadata(name=u'')
        model['content'] = current.new_notebook(metadata=metadata)
        return model

    def save_notebook(self, model, name='', path=''):
        new_path = model.get('path', path)
        new_name = model.get('name', name)

        if not self.is_writable(new_name, new_path):
            raise Exception("Notebook target is not writable")

        if path != new_path or name != new_name:
            self.rename_notebook(name, path, new_name, new_path)

        bundle_path = os.path.join(new_path, new_name)
        if not os.path.exists(bundle_path):
            os.mkdir(bundle_path)

        # Save the notebook file
        nb = current.to_notebook_json(model['content'])

        #self.check_and_sign(nb, new_name, new_path)
        notary = sign.NotebookNotary()
        if notary.check_cells(nb):
            notary.sign(nb)

        self.write_notebook(bundle_path, new_name, nb)

        if '__files' in model:
            self.write_files(bundle_path, model)

    def write_notebook(self, bundle_path, name, nb):
        nb_path = os.path.join(bundle_path, name)
        if 'name' in nb['metadata']:
            nb['metadata']['name'] = u''
        try:
            with io.open(nb_path, 'w', encoding='utf-8') as f:
                current.write(nb, f, u'json')
        except Exception as e:
            raise Exception(u'Unexpected error while autosaving notebook: %s %s' % (nb_path, e))

    def write_files(self, bundle_path, model):
        # write files
        files = model.get('__files')
        for fn, fcontent in files.items():
            filepath = os.path.join(bundle_path, fn)
            with open(filepath, 'w') as f:
                f.write(fcontent)

    def notebook_exists(self, name, path):
        return is_notebook(name, path)

    def is_writable(self, name, path):
        bundle_path = os.path.join(path, name)
        if not os.path.exists(bundle_path):
            return True
        # if path exists, only writable if it is a directory notebook
        if is_notebook(name, path):
            return True

        return False

    def rename_notebook(self, name, path, new_name, new_path):
        print name, path, new_name, new_path

    def get_notebook(self, name, path):
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

