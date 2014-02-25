import unittest
from  mock import Mock
import nose.tools as nt

from nbx.nbmanager.notebook_gisthub import NotebookGistHub, NotebookGist
from nbx.nbmanager.tests.test_gist import generate_gisthub

names = [
    "Test gist #frank #notebook", 
    "Frank bob number 2 #frank #bob #notebook", 
    "bob inactive #bob #inactive #notebook",
    "bob twin #bob #twin #notebook",
    "bob twin #bob #twin #notebook",
    "not a notebook #bob",
]

gh = generate_gisthub(names)
ngh = NotebookGistHub(gh)

class TestNotebookGistHub(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_query(self):
        results = ngh.query('#bob')
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
