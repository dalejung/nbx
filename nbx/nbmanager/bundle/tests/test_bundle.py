import os
import unittest
import nose.tools as nt

from .. import bundle as bmod
from .common import *

def wrap_bundles(path, cls):
    bundles = ['second.ipynb', 'test.ipynb']
    bundles = dict([(name, cls(name, td)) for name in bundles])
    return bundles


class TestBundle(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_files(self):
        """
        Test .files property
        """
        with fake_file_system() as td:
            bundles = wrap_bundles(td, bmod.Bundle)
            correct_files = {}
            correct_files['second.ipynb'] = ['second.ipynb', 'data.py']
            correct_files['test.ipynb'] = ['test.ipynb']

            for name, b in bundles.items():
                nt.assert_false(isinstance(b, bmod.NotebookBundle))
                correct = correct_files[b.name]
                nt.assert_items_equal(b.files, correct)

class TestNotebookBundle(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_files(self):
        """
        Test .files property
        """
        with fake_file_system() as td:
            bundles = wrap_bundles(td, bmod.NotebookBundle)
            correct_files = {}
            correct_files['second.ipynb'] = ['data.py']
            correct_files['test.ipynb'] = []
            for name, b in bundles.items():
                correct = correct_files[b.name]
                nt.assert_items_equal(b.files, correct)

    def test_notebook_content(self):
        """
        Test .notebook_content property
        """
        with fake_file_system() as td:
            bundles = wrap_bundles(td, bmod.NotebookBundle)
            for name, b in bundles.items():
                test = b.notebook_content['metadata']['filename']
                nt.assert_equal(test, b.name)

fd = fake_file_system()
td = fd.__enter__()
bundles = wrap_bundles(td, bmod.NotebookBundle)
b = bundles['second.ipynb']
#fd.__exit__(None, None, None)

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x', '--pdb'],
                  exit=False)
