from .. import bundle as bmod
from .common import fake_file_system

from nbx.tools import assert_items_equal


def wrap_bundles(td, cls):
    bundles = ['second.ipynb', 'test.ipynb']
    bundles = dict([(name, cls(name, td)) for name in bundles])
    return bundles


class TestBundle:

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
                assert not isinstance(b, bmod.NotebookBundle)
                correct = correct_files[b.name]
                assert_items_equal(list(b.files), correct)


class TestNotebookBundle:

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
                assert_items_equal(b.files, correct)

    def test_notebook_content(self):
        """
        Test .notebook_content property
        """
        with fake_file_system() as td:
            bundles = wrap_bundles(td, bmod.NotebookBundle)
            for name, b in bundles.items():
                test = b.notebook_content['metadata']['filename']
                assert test == b.name
