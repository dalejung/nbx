from nbx.nbmanager.gisthub import gisthub

class NotebookGist(object):
    def __init__(self, gist):
        self.gist = gist
        # unique identifier name
        self.suffix = " [{0}].ipynb".format(self.id)
        self.key_name = self.name + self.suffix
        super(NotebookGist, self).__init__()

    def strip_gist_id(self, name):
        suffix = " [{0}].ipynb".format(self.id)
        # really we're assuming this will only match once, seems fine
        return key_name.replace(suffix, '')

    def __getattr__(self, name):
        if hasattr(self.gist, name):
            return getattr(self.gist, name)
        raise AttributeError()

class NotebookGistHub(object):
    def __init__(self, gisthub):
        self.gisthub = gisthub

    def _wrap_results(self, results):
        wrapped = {}
        for key, gists in results.iteritems():
            # convert to NotebookGist
            items = [NotebookGist(gist) for gist in gists]
            # index by key_name
            items = dict([(gist.key_name, gist) for gist in items])
            wrapped[key] = items
        return wrapped

    def query(self, *args, **kwargs):
        kwargs['filter_tag'] = '#notebook'
        results = self.gisthub.query(*args, **kwargs)
        return self._wrap_results(results)

    def refresh_gist(self, gist):
        return self.gisthub.refresh_gist(gist)

def notebook_gisthub(user, password):
    g = gisthub(user, password)
    return NotebookGistHub(g)
