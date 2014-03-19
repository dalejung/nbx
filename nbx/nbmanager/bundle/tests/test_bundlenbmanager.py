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

            for notebook in notebooks:
                nt.assert_equal(notebook['path'], '')

    def test_save_notebook(self):
        with fake_manager() as mgr:
            notebooks = mgr.list_notebooks('')
            dirs = mgr.list_dirs('')
            model = mgr.bundler.new_notebook()
            model['name'] = 'new-name.ipynb'
            model['path'] = 'testing'
            model['__files'] = {}
            model['__files']['file1.txt'] = 'file1.txt content'
            new_model = mgr.save_notebook(model, 'new-name.ipynb', 'testing')

            # check that files were saved
            nb_dir = os.path.join(mgr.notebook_dir, 'testing', 'new-name.ipynb')
            nt.assert_true(os.path.isdir(nb_dir))
            nt.assert_true(os.path.isfile(os.path.join(nb_dir, 'new-name.ipynb')))
            nt.assert_true(os.path.isfile(os.path.join(nb_dir, 'file1.txt')))

            nt.assert_equal(new_model['path'], model['path'])
            nt.assert_equal(new_model['name'], model['name'])
            nt.assert_items_equal(new_model['__files'], ['file1.txt'])

    def test_get_notebook(self):
        with fake_manager() as mgr:
            # test subdirectory get_notebook
            model = mgr.get_notebook('subtest.ipynb', 'testing')
            nt.assert_equal(model['path'], 'testing')

            # testing files
            model = mgr.get_notebook('second.ipynb')
            nt.assert_equal(model['path'], '')
            nt.assert_items_equal(model['__files'], ['data.py'])
            nt.assert_equal(model['__files']['data.py'], None)

            # testing with file_content
            model = mgr.get_notebook('second.ipynb', file_content=True)
            nt.assert_equal(model['path'], '')
            nt.assert_items_equal(model['__files'], ['data.py'])
            nt.assert_equal(model['__files']['data.py'], '# data.py')

    def test_update_notebook(self):
        with fake_manager() as mgr:
            # simulate a change name request
            model = mgr.get_notebook('second.ipynb')
            model['name'] = 'second_changed.ipynb'
            mgr.update_notebook(model, 'second.ipynb')
            new_model = mgr.get_notebook('second_changed.ipynb')
            nt.assert_equal(new_model['name'], 'second_changed.ipynb')


fm = fake_manager()
mgr = fm.__enter__()
notebooks = mgr.list_notebooks('')
model = mgr.get_notebook('second.ipynb')
model['name'] = 'second_changed.ipynb'
mgr.update_notebook(model, 'second.ipynb')
new_model = mgr.get_notebook('second_changed.ipynb')
nt.assert_equal(new_model['name'], 'second_changed.ipynb')

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x', '--pdb'],
                  exit=False)
