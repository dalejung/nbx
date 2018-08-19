import os
import pytest

from nbx.tools import assert_items_equal

from .. import manager as mmod
from .common import fake_file_system


class TestManager:

    def test_list_bundles(self):
        """
        Make sure we skip empty.ipynb
        """
        with fake_file_system() as td:
            correct = ['test.ipynb', 'second.ipynb']
            correct = (os.path.join(td, name) for name in correct)
            assert_items_equal(correct, mmod._list_bundles(td))


class TestBundleManager:

    def test_list_dirs(self):
        """
        List the non notebook dirs.
        """
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            dirs = bm.list_dirs(td)
            assert_items_equal(dirs,
                               ['empty.ipynb', 'not_notebook', 'testing'])

    def test_list_bundles(self):
        """
        Make sure we skip empty.ipynb
        """
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            correct = ['test.ipynb', 'second.ipynb']
            bundles = bm.list_bundles_by_name(td)
            assert_items_equal(correct, bundles)

    def test_get_model(self):
        """
        """
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            bundles = bm.list_bundles_by_name(td)

            # test model and files
            second = bundles['second.ipynb']
            smodel = second.get_model()
            assert_items_equal(['data.py'], smodel['__files'])
            assert smodel['__files']['data.py'] == '# data.py'

            test = bundles['test.ipynb']
            tmodel = test.get_model()
            assert_items_equal([], tmodel['__files'])

    def test_save_notebook(self):
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            model = bm._new_notebook()
            model['name'] = 'new-name.ipynb'
            model['path'] = os.path.join(td, model['name'])
            files = {}
            files['test.txt'] = 'test.txt content'
            files['pandas.txt'] = 'pandas.txt content'
            model['__files'] = files

            bm.save_notebook(model, model['path'])

            # test directly against file system
            bundle_path = os.path.join(td, 'new-name.ipynb')
            assert os.path.isdir(bundle_path)
            nb_path = os.path.join(bundle_path, 'new-name.ipynb')
            assert os.path.isfile(nb_path)
            assert os.path.isfile(os.path.join(bundle_path, 'test.txt'))
            with open(os.path.join(bundle_path, 'test.txt')) as f:
                assert f.read() == 'test.txt content'
            assert os.path.isfile(os.path.join(bundle_path, 'pandas.txt'))
            with open(os.path.join(bundle_path, 'pandas.txt')) as f:
                assert f.read() == 'pandas.txt content'

            # now test against the bundle
            bundles = bm.list_bundles(td)
            bundle = bundles[os.path.join(td, 'new-name.ipynb')]
            assert_items_equal(['test.txt', 'pandas.txt'], bundle.files)

            # assert that saving with different files does not delete the
            # local files
            del model['__files']['test.txt']
            model['__files']['test2.txt'] = 'test2.txt content'
            bm.save_notebook(model, model['path'])
            # assert that we don't delete previous file
            assert_items_equal(['test2.txt', 'test.txt', 'pandas.txt'],
                               bundle.files)

    def test_rename_notebook(self):
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            notebooks = bm.list_bundles(td)
            notebook_names = [nb.name for nb in notebooks.values()]
            assert_items_equal(['second.ipynb', 'test.ipynb'], notebook_names)
            bm.rename_notebook(
                os.path.join(td, 'second.ipynb'),
                os.path.join(td, 'second_changed.ipynb')
            )
            notebooks_after = bm.list_bundles(td)
            notebook_after_names = [nb.name for nb in notebooks_after.values()]
            assert_items_equal(['second_changed.ipynb', 'test.ipynb'],
                               notebook_after_names)

        # existing notebook error
        with fake_file_system() as td:
            bm = mmod.BundleManager()

            def test_func():
                bm.rename_notebook(
                    os.path.join(td, 'second.ipynb'),
                    os.path.join(td, 'test.ipynb'),
                )

            with pytest.raises(Exception,
                               match="Notebook bundle already exists"):
                test_func()

        # test moving directories
        # second.ipynb/ -> testing/second.ipynb/
        with fake_file_system() as td:
            bm = mmod.BundleManager()

            orig_path = os.path.join(td, 'second.ipynb', 'second.ipynb')
            with open(orig_path) as orig:
                orig_content = orig.read()

            bm.rename_notebook(
                os.path.join(td, 'second.ipynb'),
                os.path.join(td, 'testing', 'second.ipynb')
            )

            moved_path = os.path.join(td, 'testing', 'second.ipynb',
                                      'second.ipynb')
            with open(moved_path) as moved:
                moved_content = moved.read()

            assert orig_content == moved_content

    def test_copy_notebook_file(self):
        with fake_file_system() as td:
            bm = mmod.BundleManager()
            source_path = os.path.join(td, 'second.ipynb')
            copy_path = os.path.join(td, 'bob.ipynb')
            bm.copy_notebook_file(source_path, copy_path)
            assert os.path.isfile(copy_path)
            nb_path = os.path.join(td, 'second.ipynb', 'second.ipynb')
            with open(nb_path) as orig, open(copy_path) as cp:
                orig_content = orig.read()
                copy_content = cp.read()
                assert orig_content == copy_content
