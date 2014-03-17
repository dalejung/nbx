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
            nt.assert_items_equal(correct, mmod.list_bundles(td))

class TestBundleManager(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_get_bundles(self):
        """
        Make sure we skip empty.ipynb
        """
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            correct = ['test.ipynb', 'second.ipynb']
            bundles = bm.get_bundles(td)
            nt.assert_items_equal(correct, bundles)

    def test_get_model(self):
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            correct = ['test.ipynb', 'second.ipynb']
            bundles = bm.get_bundles(td)

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
            bundles = bm.get_bundles(td)
            bundle = bundles['new-name.ipynb']
            nt.assert_items_equal(['test.txt', 'pandas.txt'], bundle.files)


fd = fake_file_system()
td = fd.__enter__()
bm = mmod.BundleManager()
model = bm.new_notebook()
model['name'] = 'new-name.ipynb'
model['path'] = td
files = {}
files['test.txt'] = 'test.txt content'
model['__files'] = files

bm.save_notebook(model, model['name'], model['path'])

bundles = bm.get_bundles(td)

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x', '--pdb'],
                  exit=False)
