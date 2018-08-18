from ..notebook_gisthub import NotebookGistHub, NotebookGist
from ..gisthub import GistHub, TaggedGist
from .test_gisthub import generate_gisthub
from nbx.nbmanager.tests.common import (
    hub,
    require_github,
    makeFakeGist,
    make_notebookgist,
    TestGistHub
)


class TestNotebookGist:

    def test_notebookgist(self):
        nb = make_notebookgist()
        assert_equal(nb.suffix, "[123].ipynb")
        assert_equal(nb.key_name, "Test Gist [123].ipynb")
        # test pass through via __getattr__
        assert_equal(nb.id, 123)
        assert_items_equal(nb.files.keys(),
                              ['a.ipynb', 'b.ipynb', 'test.txt'])

    def test_strip_gist_id(self):
        nb = make_notebookgist()
        key_name = nb.key_name
        name = nb.strip_gist_id(key_name)
        assert_equal(nb.name, name)

    def test_key_name(self):
        " Test that key_name rebuilds when name is changed "
        nb = make_notebookgist()
        nb.name = "test"
        assert_equal(nb.key_name, "test [123].ipynb")

    def test_notebook_content(self):
        nb = make_notebookgist()
        content = nb.notebook_content
        assert_equal(content, "a.ipynb content")

        nb.notebook_content = 'new nb content'
        assert_equal(nb.notebook_content, 'new nb content')

    def test_generate_payload(self):
        nb = make_notebookgist()
        payload = nb._generate_payload()
        assert_items_equal(payload['files'].keys(), ['a.ipynb'])

        nb.notebook_content = 'new nb content'
        assert_equal(nb.notebook_content, 'new nb content')

    def test_generate_description(self):
        """
        NotebookGist._generate_description will generate a proper
        description string to reflect name, active, and tags
        """
        nb = make_notebookgist()
        # make sure notebook isn't in tags
        assert_not_in('#notebook', nb.tags)
        desc = nb._generate_description()
        # the description should insert the #notebook tag
        assert_in('#notebook', desc)


        # test that inactive gets added
        assert_not_in('#inactive', desc)
        nb.active = False
        test = nb._generate_description()
        assert_in('#inactive', test)

        # change name
        nb.name = "WOO"
        test = nb._generate_description()
        assert_equal(test, "WOO #notebook #inactive #pandas #woo")

        # change tags
        nb.tags = ["#newtag"]
        test = nb._generate_description()
        assert_equal(test, "WOO #notebook #inactive #newtag")

    def test_get_revision_content(self):
        nb = make_notebookgist()
        revisions = nb.revisions
        # a.ipynb is only revision 0 and 1
        keys = map(lambda x: x['id'], revisions)
        assert_list_equal(list(keys), [0,1])
        assert_equal(nb.get_revision_content(0), "a.ipynb_0_revision_content")
        assert_equal(nb.get_revision_content(1), "a.ipynb_1_revision_content")

    def test_save(self):
        # test content/name change
        nb = make_notebookgist()
        gisthub = nb.gisthub
        nb.notebook_content = 'test'
        nb.name = "BOB"
        gisthub.save(nb)
        assert_equal(nb.gist.edit.call_count, 1)
        args = nb.gist.edit.call_args[0]
        fo = args[1]['a.ipynb']
        assert_equal(fo._InputFileContent__content, 'test')
        assert_equal(args[0], "BOB #notebook #pandas #woo")

        nb.active = False
        gisthub.save(nb)
        assert_equal(nb.gist.edit.call_count, 2)
        args = nb.gist.edit.call_args[0]
        fo = args[1]['a.ipynb']
        assert_equal(fo._InputFileContent__content, 'test')
        assert_equal(args[0], "BOB #notebook #inactive #pandas #woo")


def setup_notebookgisthub():
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
    return ngh


class TestNotebookGistHub:

    def test_query(self):
        ngh = setup_notebookgisthub()
        results = ngh.query('#bob')
        test = results['#bob']
        for key, gist in test.items():
            # make sure we are keying by keyname and not gist.id
            assert_equal(key, gist.key_name)

        names = [gist.name for gist in test.values()]
        # test that we always check for #notebook via filter_tag
        assert_not_in('not a notebook', names)
        assert_not_in('#notebook', results.keys())

    @require_github
    def test_live_query(self):
        gisthub = GistHub(hub)
        nbhub = NotebookGistHub(gisthub)
        nbhub.query()
