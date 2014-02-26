from nbx.nbmanager.gisthub import gisthub

class NotebookGist(object):
    def __init__(self, gist, gisthub=None):
        self.gist = gist
        self.gisthub = gisthub
        # unique identifier name
        self.suffix = "[{0}].ipynb".format(self.id)
        super(NotebookGist, self).__init__()

    _name = None
    @property
    def name(self):
        if self._name is None:
            self._name = self.gist.name
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        # recompute keyname

    @property
    def key_name(self):
        return self.name + ' ' + self.suffix

    def get_notebook_content(self):
        """
            Will return the first notebook in a gist
        """
        # refresh and grab file contents
        file = self.get_notebook_file()
        if file:
            return file.content

    def get_notebook_file(self):
        # iterate in sorted order so this is stable
        # don't know if the files order is defined per github api
        gist = self.gisthub.refresh_gist(self)
        for key in sorted(gist.files):
            file = gist.files[key]
            if file.filename.endswith(".ipynb"):
                return file

    def strip_gist_id(self, key_name):
        " small util to remove gist_id suffix "
        # really we're assuming this will only match once, seems fine
        return key_name.replace(' '+self.suffix, '')

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
            items = [NotebookGist(gist, self) for gist in gists]
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
