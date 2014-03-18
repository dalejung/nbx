import os
import unittest
from contextlib import contextmanager

import nose.tools as nt

from nbx.nbmanager.bundle.bundlenbmanager import BundleNotebookManager
from common import *

@contextmanager
def fake_manager():
    with fake_file_system() as td:
        manager = BundleNotebookManager()
        manager.notebook_dir = td
        yield manager

class TestBundleNotebookManager(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_list_dirs(self):
        """
        List the non notebook dirs.
        """
        with fake_manager() as mgr:
            dirs = mgr.list_dirs('')
            test_names = [model['name'] for model in dirs]
            nt.assert_items_equal(test_names, ['empty.ipynb', 'not_notebook', 'testing'])

    def test_list_notebooks(self):
        with fake_manager() as mgr:
            notebooks = mgr.list_notebooks('')
            test_names = [model['name'] for model in notebooks]
            nt.assert_items_equal(test_names, ['second.ipynb', 'test.ipynb'])

    def test_save_notebook(self):
        with fake_manager() as mgr:
            notebooks = mgr.list_notebooks('')
            dirs = mgr.list_dirs('')
            model = mgr.bundler.new_notebook()
            model['name'] = 'new-name.ipynb'
            model['path'] = 'testing'
            model['__files'] = {}
            model['__files']['file1.txt'] = 'file1.txt content'
            mgr.save_notebook(model, 'new-name.ipynb', 'testing')

            # check that files were saved
            nb_dir = os.path.join(mgr.notebook_dir, 'testing', 'new-name.ipynb')
            nt.assert_true(os.path.isdir(nb_dir))
            nt.assert_true(os.path.isfile(os.path.join(nb_dir, 'new-name.ipynb')))
            nt.assert_true(os.path.isfile(os.path.join(nb_dir, 'file1.txt')))

fm = fake_manager()
mgr = fm.__enter__()
print mgr.notebook_dir
notebooks = mgr.list_notebooks('')
dirs = mgr.list_dirs('')
model = mgr.bundler.new_notebook()
model['name'] = 'new-name.ipynb'
model['path'] = 'testing'
model['__files'] = {}
model['__files']['file1.txt'] = 'file1.txt content'
mgr.save_notebook(model, 'new-name.ipynb', 'testing')
nb_dir = os.path.join(mgr.notebook_dir, 'testing', 'new-name.ipynb')


if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x', '--pdb'],
                  exit=False)
