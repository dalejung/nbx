import unittest
from mock import Mock
import nose.tools as nt

from nbx.nbmanager.notebook_gisthub import NotebookGistHub, NotebookGist
from nbx.nbmanager.gisthub import GistHub, TaggedGist
from nbx.nbmanager.tests.test_gist import generate_gisthub
from nbx.nbmanager.tests.common import hub, require_github, makeFakeGist

def make_notebookgist():
    tg = Mock()
    tg.name = 'Test Notebook'
    tg.id = 123
    tg.tags = ['#dale']
    tg.public = True
    tg.active = True
    # fake files
    fi = Mock()
    fi.content = "nb content"
    fi.filename = 'a.ipynb'
    fi2 = Mock()
    fi2.content = "nb content2"
    tg.files = {'a.ipynb': fi, 'test.ipynb': fi2, 'zz.ipynb': fi}
    # fake gisthub
    gisthub = Mock()
    gisthub.refresh_gist = lambda x: x.gist
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
        content = nb.notebook_content
        nt.assert_equal(content, "nb content")

        nb.notebook_content = 'new nb content'
        nt.assert_equal(nb.notebook_content, 'new nb content')

    def test_generate_payload(self):
        nb = make_notebookgist()
        payload = nb._generate_payload()
        nt.assert_items_equal(payload['files'].keys(), ['a.ipynb'])

        nb.notebook_content = 'new nb content'
        nt.assert_equal(nb.notebook_content, 'new nb content')

    def test_generate_description(self):
        """
        NotebookGist._generate_description will generate a proper
        description string to reflect name, active, and tags
        """
        tagged_gist = Mock()
        tagged_gist.name = "Test Notebook"
        tagged_gist.tags = ["#pandas", "#woo"]
        tagged_gist.description = "Test Notebook #notebook #pandas #woo"
        nb = NotebookGist(tagged_gist)
        # make sure notebook isn't in tags
        nt.assert_not_in('#notebook', nb.tags)
        desc = nb._generate_description()
        # the description should insert the #notebook tag
        nt.assert_in('#notebook', desc)


        # test that inactive gets added
        nt.assert_not_in('#inactive', desc)
        nb.active = False
        test = nb._generate_description()
        nt.assert_in('#inactive', test)

        # change name
        nb.name = "WOO"
        test = nb._generate_description()
        nt.assert_equal(test, "WOO #notebook #inactive #pandas #woo")

        # change tags
        nb.tags = ["#newtag"]
        test = nb._generate_description()
        nt.assert_equal(test, "WOO #notebook #inactive #newtag")

    def test_get_revision_content(self):
        gist = makeFakeGist()
        tagged_gist = TaggedGist.from_gist(gist)
        nb = NotebookGist(tagged_gist)
        revisions = nb.revisions
        # a.ipynb is only revision 0 and 1
        keys = map(lambda x: x['id'], revisions)
        nt.assert_list_equal(keys, [0,1])
        nt.assert_equal(nb.get_revision_content(0), "a.ipynb_0_revision_content")
        nt.assert_equal(nb.get_revision_content(1), "a.ipynb_1_revision_content")

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

    @require_github
    def test_live_query(self):
        gisthub = GistHub(hub)
        nbhub = NotebookGistHub(gisthub)
        nbhub.query()

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x'],
                  exit=False)   
