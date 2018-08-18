from contextlib import contextmanager

from IPython.utils.tempdir import TemporaryDirectory
from notebook.services.contents.filemanager import FileContentsManager

from nbx.tools import assert_items_equal

from ..gist import model_to_files, GistService, Gister
from nbx.nbmanager.tests.common import (
    login,
    password,
    require_github,
    makeFakeGist
)


class TestGist:

    def test_model_to_files(self):
        with TemporaryDirectory() as td:
            fm = FileContentsManager(root_dir=td)
            model = fm.new_untitled(type='notebook')
            model['path'] = ''
            # need content
            model = fm.get_model(model['name'], model['path'])
            files = model_to_files(model)
            name = model['name']
            # files should only contain one file
            assert_items_equal(files, [name])

            # add a file
            model['__files'] = {'file1.txt': 'file1txt content'}
            files = model_to_files(model)
            assert_items_equal(files, [name, 'file1.txt'])
            assert files['file1.txt'] == 'file1txt content'


@contextmanager
def create_gist_context(*args, **kwargs):
    """
    contextmanager that creates a gist and makes sure to delete it
    """
    delete_after = kwargs.pop('delete_after', True)
    gs = GistService()
    gs.login(login, password)
    gist = gs.create_gist(*args, **kwargs)
    yield gist
    if delete_after:
        gist.delete()


class TestGistService:

    @require_github
    def test_get_gist(self):
        gs = GistService()
        gs.login(login, password)
        gist_id = '6705707'
        gist = gs.get_gist(gist_id)
        assert gist.owner.login == 'dalejung'

    @require_github
    def test_create_gist(self):
        with create_gist_context() as gist:
            assert gist.public is True

        with create_gist_context(public=False) as gist:
            assert gist.public is False

        with create_gist_context(public=False, description="nbx test") as gist:
            assert gist.public is False
            assert gist.description == "nbx test"
            assert gist.owner.login == login

        files = {'bob2.txt': 'bob2.txt content'}
        with create_gist_context(public=False, files=files) as gist:
            assert_items_equal(gist.files, ['bob2.txt'])

    @require_github
    def test_edit_gist(self):
        with create_gist_context() as gist:
            updated_at = gist.gist.updated_at
            old_desc = gist.description
            # the following should not change the gist
            gist.edit()
            assert gist.gist.updated_at == updated_at
            gist.edit(old_desc)
            assert gist.gist.updated_at == updated_at
            gist.edit(old_desc, files={'empty.txt':
                                       'empty file created by nbx'})
            assert gist.gist.updated_at == updated_at

            # change desc
            gist.edit('new desc',
                      files={'empty.txt': 'empty file created by nbx'})
            assert gist.description == 'new desc'
            assert len(gist.gist.history) == 2

            # add file
            gist.edit('new desc', files={'new.txt': 'new stuff'})
            # TODO: Need to deepdive and see why the assert fails. #15
            assert_items_equal(gist.files, ['empty.txt', 'new.txt'])
            assert len(gist.gist.history) == 3

            # don't modify the new txt. should be no change
            gist.edit('new desc', files={'new.txt': 'new stuff'})
            assert len(gist.gist.history) == 3

            # force a non change commit
            gist.edit('new desc', files={'new.txt': 'new stuff'}, force=True)
            assert len(gist.gist.history) == 4

            # modify the new file
            gist.edit('new desc', files={'new.txt': 'new stuff222'})
            assert len(gist.gist.history) == 5

    @require_github
    def test_is_owned(self):
        """ check whether gist is owned by local account """
        gs = GistService()
        gs.login(login, password)
        gist_id = '6705707'
        gist = gs.get_gist(gist_id)
        if login != 'dalejung':
            assert not gs.is_owned(gist)
        # note, until we do something that requires auth
        # it won't error
        gs.login('dalejung', 'fakepw')
        assert gs.is_owned(gist)


class TestGister:

    def test_save(self):
        gist = makeFakeGist()
        gister = Gister(gist, None)

        # delete all files
        gister.save(files=None)
        assert gist.edit.call_count == 1
        description, files = gist.edit.call_args[0]
        for fn in files:
            assert files[fn] is None

        gist = makeFakeGist()
        gister = Gister(gist, None)
        # add a new file, edit a.ipynb
        gister.save(
            files={'new.txt': 'new.txt content', 'a.ipynb': 'new content'}
        )
        description, files = gist.edit.call_args[0]
        assert_items_equal(files,
                           ['new.txt', 'a.ipynb', 'b.ipynb', 'test.txt'])

        for fn in files:
            f = files[fn]
            if fn == 'new.txt':
                assert f._InputFileContent__content == 'new.txt content'
            elif fn == 'a.ipynb':
                assert f._InputFileContent__content == 'new content'
            else:
                assert f is None

    @require_github
    def test_save_gist_live(self):
        gs = GistService()
        gs.login(login, password)
        gist = gs.create_gist()
        try:
            pass
        finally:
            gist.delete()

    def test_is_dirty(self):
        old_desc = 'Test Gist #notebook #pandas #woo'
        gist = makeFakeGist()
        gister = Gister(gist, None)

        # change desc
        assert gister._is_dirty('changed desc', files={})

        # no change
        assert not gister._is_dirty(old_desc, files={})

        # new file
        assert gister._is_dirty(old_desc, files={'new file.txt': 'ewn'})

        # change existing
        assert gister._is_dirty(old_desc, files={'a.ipynb': 'ewn'})

        # same as previous file content
        assert not gister._is_dirty(old_desc,
                                    files={'a.ipynb': 'a.ipynb content'})
