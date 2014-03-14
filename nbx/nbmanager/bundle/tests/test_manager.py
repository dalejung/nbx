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
            nt.assert_items_equal(correct, bm.get_bundles(td))

fd = fake_file_system()
td = fd.__enter__()
bm = mmod.BundleManager()
model = bm.new_notebook()
model['name'] = 'new-name.ipynb'
model['path'] = td
files = {}
files['test.txt'] = 'text.txt'
model['__files'] = files

bm.save_notebook(model, model['name'], model['path'])


if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x', '--pdb'],
                  exit=False)
