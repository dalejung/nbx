import os
import unittest
import nose.tools as nt
from IPython.nbformat import current
from IPython.html.services.notebooks.filenbmanager import FileNotebookManager
from IPython.utils.tempdir import TemporaryDirectory
import github

from ..gist import model_to_files

class TestGist(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

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


if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],
                  exit=False)
