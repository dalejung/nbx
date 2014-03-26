from IPython.nbformat import current
import github

_missing = object()

def model_to_files(model):
    """
    Converts a IPython notebook model to a github.Gist `files` dict.
    Parameters
    __________
    model : dict
        Notebook model as specified by the NotebookManager. There is
        an additional `__files` dict of the form {filename: file_content}

    Returns
    -------
    files : dict
        {filename: content}
        Note: changed files dict values to be strings.
    """
    files = {}
    name = model['name']
    content = current.writes(model['content'], format=u'json')
    files[name] = content


    __files = model.get('__files', {})
    for fn, content in __files.iteritems():
        files[fn] = content
    return files

def _github_files(files):
    """ wrap basestring content into github.InputFilecontent """
    new_files = {}
    for fn, content in files.items():
        if isinstance(content, basestring):
            content = github.InputFileContent(content)
        new_files[fn] = content
    return new_files

class GistService(object):
    """
    Keeps track of github accounts and gists.
    """
    def __init__(self):
        self.accounts = {}
        self.default = None
        self.gist_cache = {}

    @property
    def hub(self):
        """
        This is for non-user requests. We use a default logged hub
        due to the Rate Limit imposed on anonymous hubs
        """
        return self.accounts[self.default]

    def login(self, login, password):
        if self.default is None:
            self.default = login
        # if account already
        if login in self.accounts:
            print "Alredy logged in"
            return
        hub = github.Github(login, password, user_agent="nbx")
        self.accounts[login] = hub

    def get_gist(self, gist_id, refresh=False):
        if gist_id not in self.gist_cache or refresh:
            gist = self._get_gist(gist_id)
            self.gist_cache[gist_id] = gist
        return self.gist_cache[gist_id]

    def _get_gist(self, gist_id):
        """
        Returns Gist object. If we own the Gist, we return the authenticated
        Gist. Otherwise return a read-only Gist.
        """
        gist = self.hub.get_gist(gist_id)
        owner = self.get_owner(gist)
        if owner is not None and owner is not self.hub:
            print 'grabbed from hub'
            gist = owner.get_gist(gist_id)
        gist = Gister(gist, self)
        return gist

    def create_gist(self, description=None, files=None, public=True, login=None):
        if login is None:
            login = self.default
        if description is None:
            description = "nbx created gist"
        if files is None:
            files = {'empty.txt':'empty file created by nbx'}

        hub = self.accounts[login]
        files = _github_files(files)
        gist = hub.get_user().create_gist(public, files, description)
        assert gist.user.login == login
        gist = self.get_gist(gist.id)
        return gist

    def is_owned(self, gist):
        """
        Checks if the gist is ownd by an account we manage.
        """
        owner = self.get_owner(gist)
        return owner is not None

    def get_owner(self, gist):
        login = gist.user.login
        return self.accounts.get(login, None)

    def gist_deleted(self, gist):
        del self.gist_cache[gist.id]

class Gister(object):
    """
    Gister is just to differentiate from github.Gist
    """
    def __init__(self, gist, service):
        self.gist = gist
        self.service = service

        self.id = gist.id

    @property
    def public(self):
        return self.gist.public

    @property
    def description(self):
        return self.gist.description

    @property
    def files(self):
        return self.gist.files

    @property
    def user(self):
        return self.gist.user

    def edit(self, description=None, files=None, force=False):
        """
        Wrapper around github.Gist.edit. If nothing has changed
        we will not save unless `force` is true.
        """
        if description is None:
            description = self.description
        if files is None:
            files = {}

        dirty = self._is_dirty(description, files)
        files = _github_files(files)
        if dirty or force:
            self.gist.edit(description, files)

    def delete(self):
        self.gist.delete()
        self.service.gist_deleted(self)

    def _is_dirty(self, description, files):
        """
        Check whether the description/files would change the current
        gist
        """
        if description != self.gist.description:
            return True

        for fn, content in files.items():
            # new file
            if fn not in self.gist.files:
                return True

            old_content = self.gist.files[fn].content
            if content != old_content:
                return True
        return False

    def save(self, description=None, files=_missing, force=False):
        """
        Similar to edit except it assumes that `files` represents all
        files. So if a file is missing from `files` then it will be deleted.
        """
        if files is _missing:
            raise Exception("files must be explicitly passed in")

        if files is None:
            files = {}

        for fn, fobj in self.gist.files.iteritems():
            if fn not in files:
                files[fn] = None # mark for deletion

        self.edit(description, files=files, force=force)

    def pull(self):
        self.gist = self.service.get_gist(self.gist.id)
