import os
import unittest
import nose.tools as nt

import nbx.nbmanager.bundle.manager as mmod
reload(mmod)
from common import *

class TestManager(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_list_bundles(self):
        """
        Make sure we skip empty.ipynb
        """
        with fake_file_system() as td:
            correct = ['test.ipynb', 'second.ipynb']
            nt.assert_items_equal(correct, mmod._list_bundles(td))

class TestBundleManager(unittest.TestCase):

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
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            dirs = bm.list_dirs(td)
            nt.assert_items_equal(dirs, ['empty.ipynb', 'not_notebook', 'testing'])

    def test_list_bundles(self):
        """
        Make sure we skip empty.ipynb
        """
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            correct = ['test.ipynb', 'second.ipynb']
            bundles = bm.list_bundles(td)
            nt.assert_items_equal(correct, bundles)

    def test_get_model(self):
        """
        """
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            correct = ['test.ipynb', 'second.ipynb']
            bundles = bm.list_bundles(td)

            # test model and files
            second = bundles['second.ipynb']
            smodel = second.get_model()
            nt.assert_items_equal(['data.py'], smodel['__files'])
            nt.assert_equal(smodel['__files']['data.py'], '# data.py')

            test = bundles['test.ipynb']
            tmodel = test.get_model()
            nt.assert_items_equal([], tmodel['__files'])

    def test_save_notebook(self):
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            model = bm.new_notebook()
            model['name'] = 'new-name.ipynb'
            model['path'] = td
            files = {}
            files['test.txt'] = 'test.txt content'
            files['pandas.txt'] = 'pandas.txt content'
            model['__files'] = files

            bm.save_notebook(model, model['name'], model['path'])

            # test directly against file system
            bundle_path = os.path.join(td, 'new-name.ipynb')
            nt.assert_true(os.path.isdir(bundle_path))
            nb_path = os.path.join(bundle_path, 'new-name.ipynb')
            nt.assert_true(os.path.isfile(nb_path))
            nt.assert_true(os.path.isfile(os.path.join(bundle_path, 'test.txt')))
            with open(os.path.join(bundle_path, 'test.txt')) as f:
                nt.assert_equal(f.read(), 'test.txt content')
            nt.assert_true(os.path.isfile(os.path.join(bundle_path, 'pandas.txt')))
            with open(os.path.join(bundle_path, 'pandas.txt')) as f:
                nt.assert_equal(f.read(), 'pandas.txt content')

            # now test against the bundle
            bundles = bm.list_bundles(td)
            bundle = bundles['new-name.ipynb']
            nt.assert_items_equal(['test.txt', 'pandas.txt'], bundle.files)

            # assert that saving with different files does not delete the
            # local files
            del model['__files']['test.txt']
            model['__files']['test2.txt'] = 'test2.txt content'
            bm.save_notebook(model, model['name'], model['path'])
            # assert that we don't delete previous file
            nt.assert_items_equal(['test2.txt', 'test.txt', 'pandas.txt'], bundle.files)

    def test_rename_notebook(self):
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            notebooks = bm.list_bundles(td)
            nt.assert_items_equal(['second.ipynb', 'test.ipynb'], notebooks)
            bm.rename_notebook('second.ipynb', td, 'second_changed.ipynb', td)
            notebooks_after = bm.list_bundles(td)
            nt.assert_items_equal(['second_changed.ipynb', 'test.ipynb'], notebooks_after)

        # existing notebook error
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            test_func = lambda: bm.rename_notebook('second.ipynb', td, 'test.ipynb', td)
            nt.assert_raises_regexp(Exception, "Notebook bundle already exists", test_func)

        # don't support moving errors
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            test_func = lambda: bm.rename_notebook('second.ipynb', td, 'second.ipynb', os.path.join(td, 'testing'))
            nt.assert_raises_regexp(NotImplementedError, "Moving directories not", test_func)

    def test_copy_notebook_file(self):
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            notebooks = bm.list_bundles(td)
            copy_path = os.path.join(td, 'bob.ipynb')
            bm.copy_notebook_file('second.ipynb', td, copy_path)
            nt.assert_true(os.path.isfile(copy_path))
            nb_path = os.path.join(td, 'second.ipynb', 'second.ipynb')
            with open(nb_path) as orig, open(copy_path) as cp:
                orig_content = orig.read()
                copy_content = cp.read()
                nt.assert_equal(orig_content, copy_content)


fd = fake_file_system()
td = fd.__enter__()
bm = mmod.BundleManager()

notebooks = bm.list_bundles(td)
bm.copy_notebook_file('second.ipynb', td, os.path.join(td, 'bob.ipynb'))

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x', '--pdb'],
                  exit=False)
