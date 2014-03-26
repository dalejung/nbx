import os
import unittest
import nose.tools as nt
from IPython.nbformat import current
from IPython.html.services.notebooks.filenbmanager import FileNotebookManager
from IPython.utils.tempdir import TemporaryDirectory

from ..gist import model_to_files, GistService, Gister
from nbx.nbmanager.tests.common import *

class TestGist(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_model_to_files(self):
        with TemporaryDirectory() as td:
            fm = FileNotebookManager(notebook_dir=td)
            model = fm.create_notebook()
            model = fm.get_notebook(model['name'], model['path'])
            files = model_to_files(model)
            name = model['name']
            # files should only contain one file
            nt.assert_items_equal(files, [name])

            # add a file
            model['__files'] = {'file1.txt': 'file1txt content'}
            files = model_to_files(model)
            nt.assert_items_equal(files, [name, 'file1.txt'])
            nt.assert_equal(files['file1.txt']._InputFileContent__content,
                            'file1txt content')

class TestGistService(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    @require_github
    def test_get_gist(self):
        gs = GistService()
        gs.login(login, password)
        gist_id = '9751912'
        gist = gs.get_gist(gist_id)
        nt.assert_equal(gist.user.login, 'dalejung')

    @require_github
    def test_is_owned(self):
        """ check whether gist is owned by local account """
        gs = GistService()
        gs.login(login, password)
        gist_id = '9751912'
        gist = gs.get_gist(gist_id)
        if login != 'dalejung':
            nt.assert_false(gs.is_owned(gist))
        # note, until we do something that requires auth
        # it won't error
        gs.login('dalejung', 'fakepw')
        nt.assert_true(gs.is_owned(gist))

class TestGister(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_save(self):
        gist = makeFakeGist()
        gister = Gister(gist, None)

        # delete all files
        gister.save(files=None)
        nt.assert_equal(gist.edit.call_count, 1)
        description, files = gist.edit.call_args[0]
        for fn in files:
            nt.assert_is_none(files[fn])

        gist = makeFakeGist()
        gister = Gister(gist, None)
        # add a new file, edit a.ipynb
        gister.save(files={'new.txt':'new.txt content', 'a.ipynb':'new content'})
        description, files = gist.edit.call_args[0]
        nt.assert_items_equal(files, ['new.txt', 'a.ipynb', 'b.ipynb', 'test.txt'])

        for fn in files:
            if fn == 'new.txt':
                nt.assert_equal(files[fn], 'new.txt content')
            elif fn == 'a.ipynb':
                nt.assert_equal(files[fn], 'new content')
            else:
                nt.assert_is_none(files[fn])

with TemporaryDirectory() as td:
    fm = FileNotebookManager(notebook_dir=td)
    model = fm.create_notebook()
    model = fm.get_notebook(model['name'], model['path'])
    model['__files'] = {'file1.txt': 'file1txt content'}

    files = model_to_files(model)

gs = GistService()
gist_id = '9751912'
gs.login(login, password)
gist = gs.get_gist(gist_id)
hub = gs.accounts['dalejung']

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],
                  exit=False)
