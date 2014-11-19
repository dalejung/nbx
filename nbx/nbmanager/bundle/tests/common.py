import os
import io
from contextlib import contextmanager

from IPython.utils.tempdir import TemporaryDirectory
from IPython import nbformat
current = nbformat.v4

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def new_notebook(metadata, filepath):
    content = current.new_notebook(metadata=metadata)
    nb = current.to_notebook_json(content)
    with io.open(filepath, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f, version=nbformat.NO_CONVERT)

@contextmanager
def fake_file_system():
    with TemporaryDirectory() as td:
        """
        ./bob.ipynb
        ./test.ipynb/test.ipynb
        ./not_notebook/
        ./testing/
        """
        touch(os.path.join(td, 'bob.ipynb'))
        # make bundle
        nb_dir = os.path.join(td, 'test.ipynb')
        os.mkdir(nb_dir)

        metadata = {'filename':'test.ipynb'}
        new_notebook(metadata, os.path.join(nb_dir, 'test.ipynb'))

        # make second bundle
        nb_dir = os.path.join(td, 'second.ipynb')
        os.mkdir(nb_dir)

        metadata = {'filename':'second.ipynb'}
        new_notebook(metadata, os.path.join(nb_dir, 'second.ipynb'))

        with open(os.path.join(nb_dir, 'data.py'), 'w') as f:
            f.write('# data.py')

        # make empty .ipynb dir that shouldn't count as notebook
        os.mkdir(os.path.join(td, 'empty.ipynb'))

        # regular dirs
        os.mkdir(os.path.join(td, 'not_notebook'))
        os.mkdir(os.path.join(td, 'testing'))

        nb_dir = os.path.join(td, 'testing', 'subtest.ipynb')
        os.mkdir(nb_dir)
        metadata = {'filename':'subtest.ipynb'}
        new_notebook(metadata, os.path.join(nb_dir, 'subtest.ipynb'))

        yield td

        pass
