from mock import Mock

from ..gisthub import TaggedGist, GistHub
from nbx.nbmanager.tests.common import hub, require_github, makeFakeGist


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


class TestTaggedGist:

    def test_from_gist(self):
        gist = Mock()
        gist.description = "Dale Name #notebook #hello"

        tg = TaggedGist.from_gist(gist)
        assert_equals(tg.name, "Dale Name")
        assert_items_equal(tg.tags, ['#notebook', '#hello'])
        assert_true(tg.active)

        gist = Mock()
        gist.description = "Dale Name #notebook #inactive"

        tg = TaggedGist.from_gist(gist)
        assert_equals(tg.name, "Dale Name")
        assert_items_equal(tg.tags, ['#notebook'])

        # explicitly test system tags
        assert_in('#inactive', TaggedGist.system_tags)
        assert_not_in('#inactive', tg.tags)
        assert_false(tg.active)

    def test_files(self):
        gist = Mock()
        gist.description = "Dale Name #notebook #hello"
        gist.files = object()

        tg = TaggedGist.from_gist(gist)
        assert_is(tg.files, gist.files)

    def test_revisions_for_file(self):
        # TODO not a huge fan of how I mock github.Gist objects
        gist = makeFakeGist()
        tg = TaggedGist.from_gist(gist)
        a_revs = tg.revisions_for_file('a.ipynb')
        # should only have 2 revisions for a.ipynb
        assert_equal(len(a_revs), 2)
        # make sure we got the right ones
        for state in a_revs:
            assert_in('a.ipynb', state.raw_data['files'])

    def test_get_revision_file(self):
        gist = makeFakeGist()
        tg = TaggedGist.from_gist(gist)
        fo = tg.get_revision_file(0, 'a.ipynb')
        correct = "{fn}_{id}_revision_content".format(fn='a.ipynb', id=0)
        assert_equal(fo['content'], correct)

class TestGistHub:

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
        assert_equals(len(active), 5)
        test_names = [g.name for g in active]
        valid = ['Test gist', 'Frank bob number 2',
                'bob twin', 'bob twin', 'bob inactive']
        assert_items_equal(test_names, valid)

        # True
        active = gh._filter_active(gists, True)
        assert_equals(len(active), 4)
        test_names = [g.name for g in active]
        valid = ['Test gist', 'Frank bob number 2', 'bob twin', 'bob twin']
        assert_items_equal(test_names, valid)

        # false
        active = gh._filter_active(gists, False)
        assert_equals(len(active), 1)
        test_names = [g.name for g in active]
        valid = ['bob inactive']
        assert_items_equal(test_names, valid)

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
        assert_equals(len(twins), 2)
        test_names = [g.name for g in twins]
        valid = ['bob twin', 'bob twin']
        assert_items_equal(test_names, valid)

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
        # will return both #inactive and #bob
        assert_equals(len(list(test.keys())), 2)
        assert_equals(len(test['#bob']), 1)
        valid = ['bob inactive']
        test_names = [g.name for g in test['#bob']]
        assert_items_equal(test_names, valid)

        # filtering inactive with bob, which shoudl return same as above
        test = gh.query(active=False, filter_tag='bob', drop_filter=False)
        assert_equals(len(list(test.keys())), 2)
        assert_equals(len(test['#bob']), 1)
        valid = ['bob inactive']
        test_names = [g.name for g in test['#bob']]
        assert_items_equal(test_names, valid)

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
        assert_items_equal(list(test.keys()), ['#bob'])
        bobs = test['#bob']
        assert_equal(len(bobs), 2)
