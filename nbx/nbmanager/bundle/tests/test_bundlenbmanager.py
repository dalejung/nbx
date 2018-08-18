import os
from contextlib import contextmanager

from nbx.tools import assert_items_equal

from ..bundlenbmanager import BundleNotebookManager
from .common import fake_file_system


@contextmanager
def fake_manager():
    with fake_file_system() as td:
        manager = BundleNotebookManager()
        manager.root_dir = td
        yield manager


def bundletest(func):
    def test_func(self):
        with fake_manager() as mgr:
            func(self, mgr)
    return test_func


class TestBundleNotebookManager:

    @bundletest
    def test_list_dirs(self, mgr):
        """
        List the non notebook dirs.
        """
        dirs = mgr.list_dirs('')
        test_names = [model['name'] for model in dirs]
        assert_items_equal(
            test_names,
            ['empty.ipynb', 'not_notebook', 'testing']
        )

    @bundletest
    def test_list_notebooks(self, mgr):
        notebooks = mgr.list_notebooks('')
        test_names = [model['name'] for model in notebooks]
        assert_items_equal(test_names, ['second.ipynb', 'test.ipynb'])

        for notebook in notebooks:
            assert notebook['path'] == ''

    @bundletest
    def test_save_notebook(self, mgr):
        notebooks = mgr.list_notebooks('')
        dirs = mgr.list_dirs('')
        model = mgr.new_untitled(type='notebook')
        # the above returns the model returned from save, which does not
        # include content
        model = mgr.get_notebook(model['name'], model['path'], content=True)
        model['name'] = 'new-name.ipynb'
        model['path'] = 'testing'
        model['__files'] = {}
        model['__files']['file1.txt'] = 'file1.txt content'
        new_model = mgr.save_notebook(model, 'new-name.ipynb', 'testing')
        # save second time to trigger checkpoint creation
        new_model = mgr.save_notebook(model, 'new-name.ipynb', 'testing')

        # verify that we create a checkpoint if notebook exists and no
        # checkpoint exists
        checkpoints = mgr.list_checkpoints('new-name.ipynb', 'testing')
        assert len(checkpoints) == 1

        # check that files were saved
        nb_dir = os.path.join(mgr.root_dir, 'testing', 'new-name.ipynb')
        assert os.path.isdir(nb_dir)
        assert os.path.isfile(os.path.join(nb_dir, 'new-name.ipynb'))
        assert os.path.isfile(os.path.join(nb_dir, 'file1.txt'))

        assert new_model['path'] == model['path']
        assert new_model['name'] == model['name']
        assert_items_equal(new_model['__files'], ['file1.txt'])

    @bundletest
    def test_get_notebook(self, mgr):
        # test subdirectory get_notebook
        model = mgr.get_notebook('subtest.ipynb', 'testing')
        assert model['path'] == 'testing'

        # testing files
        model = mgr.get_notebook('second.ipynb')
        assert model['path'] == ''
        assert_items_equal(model['__files'], ['data.py'])
        assert model['__files']['data.py'] == None

        # testing with file_content
        model = mgr.get_notebook('second.ipynb', file_content=True)
        assert model['path'] == ''
        assert_items_equal(model['__files'], ['data.py'])
        assert model['__files']['data.py'] == '# data.py'

    @bundletest
    def test_update_notebook(self, mgr):
        # simulate a change name request
        model = mgr.get_notebook('second.ipynb')
        model['name'] = 'second_changed.ipynb'
        mgr.update_notebook(model, 'second.ipynb')
        new_model = mgr.get_notebook('second_changed.ipynb')
        assert new_model['name'] == 'second_changed.ipynb'

    @bundletest
    def test_get_checkpoint_path(self, mgr):
        checkpoint_path = mgr.get_checkpoint_path('cpid', 'dale.ipynb',
                                                  'subdir')
        correct = 'subdir/dale.ipynb/.ipynb_checkpoints/dale---cpid.ipynb'
        assert checkpoint_path == correct

    @bundletest
    def test_create_checkpoint(self, mgr):
        model = mgr.create_checkpoint('second.ipynb', '')
        cp_path = mgr.get_checkpoint_path(model['id'], 'second.ipynb', path='')
        os_cp_path = mgr._get_os_path(cp_path)
        # see that checkpoint was created
        assert os.path.isfile(os_cp_path)

    @bundletest
    def test_list_checkpoints(self, mgr):
        checkpoints = mgr.list_checkpoints('second.ipynb')
        # start with no checkpoints
        assert len(checkpoints) == 0
        model = mgr.create_checkpoint('second.ipynb', '')
        checkpoints = mgr.list_checkpoints('second.ipynb')
        assert len(checkpoints) == 1
        checkpoint = checkpoints[0]
        assert checkpoint['id'] == model['id']
