import github
import pandas as pd
from mock import Mock

from nbx.nbmanager.notebook_gisthub import NotebookGist
from nbx.nbmanager.gisthub import TaggedGist

hub = None
try:
    import GithubCredentials
    login = GithubCredentials.login
    password = GithubCredentials.password
    hub = github.Github(login, password, user_agent="nbx")
except:
   #hub = Mock()
   pass

def require_github(func):
    if hub is None:
        return lambda s: None
    return func

class TestGistHub(object):
    def refresh_gist(self, gist):
        return gist.gist

def makeFakeGist():
    gist = Mock()
    gist.description = "Test Gist #notebook #pandas #woo"
    gist.id = 123
    # fake files
    filenames = ['a.ipynb', 'b.ipynb', 'test.txt']
    files = {}
    for fn in filenames:
        fo = Mock()
        fo.filename = fn
        fo.content = fn+" content"
        files[fn] = fo

    gist.files = files
    # fake history
    history = []
    dates = pd.date_range("2000", freq="D", periods=4).to_pydatetime()
    for i, date in enumerate(dates):
        state = Mock()
        state.version = i
        state.committed_at = date
        raw_data = {}
        files = {}
        for fn in filenames:
            fo = {
                'content': "{fn}_{i}_revision_content".format(fn=fn, i=i),
                'filename': fn,
            }
            files[fn] = fo
        # after 2, don't include 'a.ipynb'
        if i >= 2:
            del files['a.ipynb']

        raw_data['files'] = files
        state.raw_data = raw_data
        history.append(state)

    gist.history = history

    return gist

def make_notebookgist():
    gist = makeFakeGist()
    tg = TaggedGist.from_gist(gist)
    # fake gisthub
    gisthub = TestGistHub()
    nb = NotebookGist(tg, gisthub)
    nb.tags.remove("#notebook")
    return nb
