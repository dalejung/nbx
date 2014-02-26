import github

from nbx.nbmanager.gisthub import gisthub
from IPython.nbformat import current

class NotebookGist(object):
    """
    A single notebook abstraction over Gist. Normally a gist can have
    mutliple files. A notebook gist pretends to be a single file.
    """
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

    def __getattr__(self, name):
        if hasattr(self.gist, name):
            return getattr(self.gist, name)
        print self.gist
        raise AttributeError("{name} not found on .gist".format(name=name))

    _notebook_content = None
    @property
    def notebook_content(self):
        if self._notebook_content is None:
            # refresh and grab file contents
            file = self.get_notebook_file()
            if file:
                self._notebook_content = file.content
        return self._notebook_content

    @notebook_content.setter
    def notebook_content(self, content):
        if isinstance(content, basestring):
            self._notebook_content = content
            return

        try:
            # maybe this is a notebook
            content = current.writes(content, format=u'json')
            self._notebook_content = content
        except: 
            raise

    def refresh(self):
        self.gist = self.gisthub.refresh_gist(self)

    def get_notebook_file(self):
        """
            Will return the first notebook in a gist.
            Iterate in sorted order so this is stable
            don't know if the files order is defined per github api
        """
        self.refresh()
        for key in sorted(self.gist.files):
            file = self.gist.files[key]
            if file.filename.endswith(".ipynb"):
                return file

    def edit(self, desc=None, files=None):
        if desc is None:
            desc = self.description
        self.gist.edit(desc, files)

    def generate_payload(self):
        " Gather payload to sent to Github. "
        gfile = self.get_notebook_file()
        file = github.InputFileContent(self.notebook_content)
        files = {gfile.filename: file}
        description = self.generate_description()
        return {'files':files, 'description': description}

    def generate_description(self):
        # TODO
        # Combine name, tags, etc and generate description
        # Needed if name or tags is changed.
        return self.description

    def save(self):
        payload = self.generate_payload()
        self.edit(payload['description'], payload['files'])

    def __repr__(self):
        out = "NotebookGist(name={name}, active={active}, " + \
               "public={public}, tags={tags})"
        return out.format(public=self.public, name=self.name, 
                          tags=self.tags, active=self.active)

    def strip_gist_id(self, key_name):
        " small util to remove gist_id suffix "
        # really we're assuming this will only match once, seems fine
        return key_name.replace(' '+self.suffix, '')

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
