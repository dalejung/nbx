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
        {filename: github.InputFileContent(file_content)}
    """
    files = {}
    name = model['name']
    content = current.writes(model['content'], format=u'json')
    f = github.InputFileContent(content)
    files[name] = f


    __files = model.get('__files', {})
    for fn, fn_content in __files.iteritems():
        f = github.InputFileContent(fn_content)
        files[fn] = f
    return files

class GistService(object):
    """
    Keeps track of github accounts and gists.
    """
    def __init__(self):
        self.hub = github.Github()
        self.accounts = {}
        self.default = None
        self.gist_cache = {}

    def login(self, login, password):
        # if account already
        if login in self.accounts:
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
        # if we're
        owner = self.get_owner(gist)
        if owner is not None:
            gist = owner.get_gist(gist_id)
        gist = Gister(gist, self)
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

class Gister(object):
    def __init__(self, gist, service):
        self.gist = gist
        self.service = service

    @property
    def user(self):
        return self.gist.user

    def edit(self, description=None, files=None, force=False):
        """
        Wrapper around github.Gist.edit. If nothing has changed
        we will not save unless `force` is true.
        """
        if description is None:
            description = self.gist.description
        dirty = False
        for fn, fobj in self.gist.files.iteritems():
            # if file is missing, means we leave it alone
            if fn not in files:
                continue
            new_content = files[fn]
            if new_content != fobj.content:
                dirty = True
                break
        if description != self.gist.description:
            dirty = True
        #
        if dirty or force:
            self.gist.edit(description, files)

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
