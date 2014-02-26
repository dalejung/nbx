import unittest
from mock import Mock
import nose.tools as nt

from nbx.nbmanager.notebook_gisthub import NotebookGistHub, NotebookGist
from nbx.nbmanager.tests.test_gist import generate_gisthub

def make_notebookgist():
    tg = Mock()
    tg.name = 'Test Notebook'
    tg.id = 123
    tg.tags = ['#dale']
    # fake files
    fi = Mock()
    fi.content = "nb content"
    fi2 = Mock()
    fi2.content = "nb content2"
    tg.files = {'a.ipynb': fi, 'test.ipynb': fi2, 'zz.ipynb': fi}
    # fake gisthub
    gisthub = Mock()
    gisthub.refresh_gist = lambda x: x
    nb = NotebookGist(tg, gisthub)
    return nb

class TestNotebookGist(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_notebookgist(self):
        nb = make_notebookgist()
        nt.assert_equal(nb.suffix, "[123].ipynb")
        nt.assert_equal(nb.key_name, "Test Notebook [123].ipynb")
        # test pass through via __getattr__
        nt.assert_equal(nb.id, 123)
        nt.assert_items_equal(nb.files.keys(), 
                              ['test.ipynb', 'a.ipynb', 'zz.ipynb'])

    def test_strip_gist_id(self):
        nb = make_notebookgist()
        key_name = nb.key_name
        name = nb.strip_gist_id(key_name)
        nt.assert_equal(nb.name, name)

    def test_key_name(self):
        " Test that key_name rebuilds when name is changed "
        nb = make_notebookgist()
        nb.name = "test"
        nt.assert_equal(nb.key_name, "test [123].ipynb")

    def test_notebook_content(self):
        nb = make_notebookgist()
        content = nb.get_notebook_content()
        nt.assert_equal(content, "nb content")

class TestNotebookGistHub(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        names = [
            "Test gist #frank #notebook", 
            "Frank bob number 2 #frank #bob #notebook", 
            "bob inactive #bob #inactive #notebook",
            "bob twin #bob #twin #notebook",
            "bob twin #bob #twin #notebook",
            "not a notebook #bob",
        ]

        gh = generate_gisthub(names)
        self.ngh = NotebookGistHub(gh)

    def test_query(self):
        results = self.ngh.query('#bob')
        test = results['#bob']
        for key, gist in test.items():
            # make sure we are keying by keyname and not gist.id
            nt.assert_equal(key, gist.key_name)

        names = [gist.name for gist in test.values()]
        # test that we always check for #notebook via filter_tag
        nt.assert_not_in('not a notebook', names)
        nt.assert_not_in('#notebook', results.keys())

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],
                  exit=False)   
