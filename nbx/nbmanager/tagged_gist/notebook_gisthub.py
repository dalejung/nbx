import github

from IPython import nbformat

from .gisthub import gisthub, _hashtags
import nbx.compat as compat

def parse_tags(desc):
    # real tags and not system-like tags
    tags = _hashtags(desc)
    if '#notebook' in tags:
        tags.remove('#notebook')
    if '#inactive' in tags:
        tags.remove('#inactive')
    return tags

class NotebookGist(object):
    """
    A single notebook abstraction over Gist. Normally a gist can have
    mutliple files. A notebook gist pretends to be a single file.
    """
    # instead of having a bunch of @property getters, define
    # attrs to grab from .gist here.
    _gist_attrs = ['id', 'files', 'active', 'edit', 'updated_at',
                   'created_at', 'public']

    def __init__(self, gist, gisthub):
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

    _tags = None
    @property
    def tags(self):
        if self._tags is None:
            self._tags = self.gist.tags[:]
            if '#notebook' in self._tags:
                self._tags.remove('#notebook')
        return self._tags

    @tags.setter
    def tags(self, tags):
        self._tags = tags

    def __getattr__(self, name):
        if name in self._gist_attrs:
            return getattr(self.gist, name)
        raise AttributeError("{name} not found on .gist".format(name=name))

    _notebook_content = None
    @property
    def notebook_content(self):
        if self._notebook_content is None:
            # refresh and grab file contents
            file = self._get_notebook_file()
            if file:
                self._notebook_content = file.content
        return self._notebook_content

    @notebook_content.setter
    def notebook_content(self, content):
        if isinstance(content, compat.string_types):
            self._notebook_content = content
            return

        try:
            # maybe this is a notebook
            content = nbformat.writes(content, version=nbformat.NO_CONVERT)
            self._notebook_content = content
        except:
            raise

    @property
    def revisions(self):
        # only return revisions for the .ipynb file
        fn = self._get_notebook_file()
        revisions = self.gist.revisions_for_file(fn.filename)
        # convert to basic commit log. Dont' want NotebookManager
        # needing to know github.GistHistoryState internals
        commits = []
        for state in revisions:
            commit = {
                'id': state.version,
                'commit_date': state.committed_at
            }
            commits.append(commit)
        return commits

    def get_revision_content(self, commit_id):
        fobj = self._get_notebook_file()
        rev_fobj = self.gist.get_revision_file(commit_id, fobj.filename)
        return rev_fobj['content']

    def _refresh(self):
        self.gist = self.gisthub.refresh_gist(self)

    def _get_notebook_file(self):
        """
            Will return the first notebook in a gist.
            Iterate in sorted order so this is stable
            don't know if the files order is defined per github api
        """
        self._refresh()
        for key in sorted(self.gist.files):
            file = self.gist.files[key]
            if file.filename.endswith(".ipynb"):
                return file

    def _edit(self, desc=None, files=None):
        if desc is None:
            desc = self.description
        self.gist.edit(desc, files)

    def _generate_payload(self):
        " Gather payload to sent to Github. "
        gfile = self._get_notebook_file()
        file = github.InputFileContent(self.notebook_content)
        files = {gfile.filename: file}
        description = self._generate_description()
        return {'files':files, 'description': description}

    def _generate_description(self):
        """ genrate the Gist description. """
        name = self.name
        # system type of tags
        tags = ['#notebook']
        if not self.active:
            tags.append('#inactive')

        # add the normal tags
        tags += self.tags

        tagstring = " ".join(tags)
        description = "{name} {tags}".format(name=name, tags=tagstring)
        return description

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
        for key, gists in results.items():
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

    def save(self, gist):
        payload = gist._generate_payload()
        gist._edit(payload['description'], payload['files'])
        self.gisthub.update_gist(gist.gist)

    def create_gist(self, name, tags, content='', public=True):
        gist = self.gisthub.create_gist(name, tags, content, public)
        nb = NotebookGist(gist, self)
        return nb

def notebook_gisthub(user, password):
    g = gisthub(user, password)
    return NotebookGistHub(g)
