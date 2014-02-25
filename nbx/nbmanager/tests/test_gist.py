import unittest
from  mock import Mock
import nose.tools as nt

import nbx.nbmanager.GithubCredentials as GithubCredentials
from nbx.nbmanager.gisthub import TaggedGist, GistHub

def generate_tagged_gists(names):
    mocks = []
    for id, name in enumerate(names, 1):
        mock = Mock()
        mock.description = name
        mock.id = id
        mocks.append(mock)

    tagged_gists = [(mock.id, TaggedGist.from_gist(mock))
                    for mock in mocks if mock.description]
    tagged_gists = dict(tagged_gists)
    return tagged_gists

def generate_gisthub(names):
    gists = generate_tagged_gists(names)
    gh = GistHub(Mock())
    gh._tagged_gists = gists
    return gh

class TestTaggedGist(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_from_gist(self):
        gist = Mock()
        gist.description = "Dale Name #notebook #hello"

        tg = TaggedGist.from_gist(gist)
        nt.assert_equals(tg.name, "Dale Name")
        nt.assert_items_equal(tg.tags, ['#notebook', '#hello'])
        nt.assert_true(tg.active)

        gist = Mock()
        gist.description = "Dale Name #notebook #inactive"

        tg = TaggedGist.from_gist(gist)
        nt.assert_equals(tg.name, "Dale Name")
        nt.assert_items_equal(tg.tags, ['#notebook'])

        # explicitly test system tags
        nt.assert_in('#inactive', TaggedGist.system_tags)
        nt.assert_not_in('#inactive', tg.tags) 
        nt.assert_false(tg.active)

    def test_files(self):
        gist = Mock()
        gist.description = "Dale Name #notebook #hello"
        gist.files = object()

        tg = TaggedGist.from_gist(gist)
        nt.assert_is(tg.files, gist.files)

class TestGistHub(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def runTest(self):
        pass

    def setUp(self):
        pass

    def test_filter_active(self):
        names = [
            "Test gist #frank", 
            "Frank bob number 2 #frank #bob", 
            "bob inactive #bob #inactive",
            "bob twin #bob #twin",
            "bob twin #bob #twin",
        ]

        gh = generate_gisthub(names)
        gists = gh._tagged_gists.values()
        # None
        active = gh._filter_active(gists, None)
        nt.assert_equals(len(active), 5)
        test_names = [g.name for g in active]
        valid = ['Test gist', 'Frank bob number 2', 
                'bob twin', 'bob twin', 'bob inactive']
        nt.assert_items_equal(test_names, valid)

        # True
        active = gh._filter_active(gists, True)
        nt.assert_equals(len(active), 4)
        test_names = [g.name for g in active]
        valid = ['Test gist', 'Frank bob number 2', 'bob twin', 'bob twin']
        nt.assert_items_equal(test_names, valid)

        # false
        active = gh._filter_active(gists, False)
        nt.assert_equals(len(active), 1)
        test_names = [g.name for g in active]
        valid = ['bob inactive']
        nt.assert_items_equal(test_names, valid)

    def test_filter_tag(self):
        names = [
            "Test gist #frank", 
            "Frank bob number 2 #frank #bob", 
            "bob inactive #bob #inactive",
            "bob twin #bob #twin",
            "bob twin #bob #twin",
        ]

        gh = generate_gisthub(names)
        gists = gh._tagged_gists.values()

        twins = gh._filter_tag(gists, 'twin')
        nt.assert_equals(len(twins), 2)
        test_names = [g.name for g in twins]
        valid = ['bob twin', 'bob twin']
        nt.assert_items_equal(test_names, valid)

    def test_query(self):
        names = [
            "Test gist #frank", 
            "Frank bob number 2 #frank #bob", 
            "bob inactive #bob #inactive",
            "bob twin #bob #twin",
            "bob twin #bob #twin",
        ]
        gh = generate_gisthub(names)
        gists = gh._tagged_gists.values()

        # inactive
        test = gh.query(active=False)
        nt.assert_equals(len(test.keys()), 1)
        nt.assert_equals(len(test['#bob']), 1)
        valid = ['bob inactive']
        test_names = [g.name for g in test['#bob']]
        nt.assert_items_equal(test_names, valid)

        # filtering inactive with bob, which shoudl return same as above
        test = gh.query(active=False, filter_tag='bob', drop_filter=False)
        nt.assert_equals(len(test.keys()), 1)
        nt.assert_equals(len(test['#bob']), 1)
        valid = ['bob inactive']
        test_names = [g.name for g in test['#bob']]
        nt.assert_items_equal(test_names, valid)

        # query filer_tag
        names = [
            "Test gist #frank", 
            "Frank bob number 2 #frank #bob", 
            "bob inactive #bob #inactive",
            "bob twin #bob #twin",
            "bob twin #bob #twin",
        ]
        gh = generate_gisthub(names)

        # filtering only by #twin should get just the bob twins
        test = gh.query(filter_tag='twin')
        nt.assert_items_equal(test.keys(), ['#bob'])
        bobs = test['#bob']
        nt.assert_equal(len(bobs), 2)

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],
                  exit=False)   
