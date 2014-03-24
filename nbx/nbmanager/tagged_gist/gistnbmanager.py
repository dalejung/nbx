import itertools

from tornado import web

from IPython.html.services.notebooks.nbmanager import NotebookManager
from IPython.nbformat import current

from .notebook_gisthub import parse_tags

class GistNotebookManager(NotebookManager):
    """
    """
    def __init__(self, *args, **kwargs):
        self.gisthub = kwargs.pop('gisthub')
        super(GistNotebookManager, self).__init__(*args, **kwargs)

    def is_hidden(self, path):
        return False

    def path_exists(self, path):
        if path == '':
            return True
        tags = self.gist_query()
        return path in tags.keys()

    def get_dir_model(self, name):
        model ={}
        model['name'] = name
        model['path'] = name
        model['type'] = 'directory'
        return model

    def gist_query(self, tag=None):
        tags = self.gisthub.query(tag)
        if tag is None:
            # query and grab the inactive notebook. put them by themselves
            inactive = self.gisthub.query('#inactive', active=False)
            tags['#inactive'] = inactive['#inactive']
        return tags

    def gists_by_tag(self, tag):
        tagged = self.gist_query(tag)
        assert len(tagged) <= 1, "should only at most one tag"
        if not tagged:
            return {}
        gists = tagged.values()[0]
        return gists

    def list_dirs(self, path=''):
        # only return dirs for ''
        if path != '':
            return []
        tags = self.gist_query()
        dirs = []
        for name in tags.keys():
            model = self.get_dir_model(name)
            dirs.append(model)
        return dirs

    def list_notebooks(self, path=''):
        if path == '':
            return []

        # get notebooks by tag
        gists = self.gists_by_tag(path)
        notebooks = [self.get_notebook(gist.key_name, path, content=False) for gist in gists.values()]
        # sort by date, descending
        notebooks = sorted(notebooks, key=lambda x: x['last_modified'], reverse=True)
        return notebooks

    def notebook_exists(self, name, path=''):
        gist = self._get_gist(name, path)
        return gist is not None

    def _get_gist(self, name, path):
        # get notebooks by tag
        gists = self.gists_by_tag(path)
        if name not in gists:
            print 'gist not found', gists.keys(), name, path
        return gists.get(name, None)

    def get_notebook(self, name, path='', content=True):
        """ Takes a path and name for a notebook and returns its model

        Parameters
        ----------
        name : str
            the name of the notebook
        path : str
            the URL path that describes the relative path for
            the notebook

        Returns
        -------
        model : dict
            the notebook model. If contents=True, returns the 'contents'
            dict in the model as well.
        """
        path = path.strip('/')
        if not self.notebook_exists(name=name, path=path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % name)
        gist = self._get_gist(name, path)
        # Create the notebook model.
        model ={}
        model['name'] = name
        model['path'] = path
        model['last_modified'] = gist.updated_at
        model['created'] = gist.created_at
        model['type'] = 'notebook'
        if content:
            notebook_content = gist.notebook_content
            try:
                nb = current.reads(notebook_content, u'json')
            except Exception as e:
                raise web.HTTPError(400, u"Unreadable Notebook: %s %s %s" % (path, name, e))
            self.mark_trusted_cells(nb, path, name)

            # add gist id if public.
            if gist.public:
                nb['metadata']['gist_id'] = gist.id
            model['content'] = nb
        return model

    def basename_exists(self, name, path):
        """
        notebook_exists checks notebook names in the form of:
            Notebook Name [gistid]
        basename_exists checks on names without suffix. i.e.:
            Notebook Name
        """
        gists = self.gists_by_tag(path)
        for key, gist in gists.iteritems():
            if gist.name == name:
                return True
        return False

    def increment_filename(self, basename, path=''):
        """Increment a notebook filename without the .ipynb to make it unique.

        Parameters
        ----------
        basename : unicode
            The name of a notebook without the ``.ipynb`` file extension.
        path : unicode
            The URL path of the notebooks directory

        Returns
        -------
        name : unicode
            A notebook name (with the .ipynb extension) that starts
            with basename and does not refer to any existing notebook.
        """
        path = path.strip('/')
        for i in itertools.count():
            name = u'{basename}{i}'.format(basename=basename, i=i)
            if not self.basename_exists(name, path):
                break
        return name

    def save_notebook(self, model, name='', path=''):
        """Save the notebook model and return the model with no content."""
        path = path.strip('/')

        if 'content' not in model:
            raise web.HTTPError(400, u'No notebook JSON data provided')

        if not path:
            raise web.HTTPError(400, u'We require path for saving.')

        gist = self._get_gist(name, path)
        if gist is None:
            tags = parse_tags(name)
            if path:
                tags.append(path)
            content = current.writes(model['content'], format=u'json')
            gist = self.gisthub.create_gist(name, tags, content)

        # One checkpoint should always exist
        #if self.notebook_exists(name, path) and not self.list_checkpoints(name, path):
        #    self.create_checkpoint(name, path)

        new_path = model.get('path', path).strip('/')
        new_name = model.get('name', name)

        if path != new_path:
            raise web.HTTPError(400, u'Gist backend does not support path change')

        # Save the notebook file
        nb = current.to_notebook_json(model['content'])

        # remove [gist_id] if we're being sent old key_name
        gist.name = gist.strip_gist_id(new_name)
        gist.notebook_content = nb

        self.check_and_sign(nb, new_path, new_name)

        if 'name' in nb['metadata']:
            nb['metadata']['name'] = u''
        try:
            self.log.debug("Autosaving notebook %s %s", path, name)
            self.gisthub.save(gist)
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while autosaving notebook: %s %s %s' % (path, name, e))

        # NOTE: since gist.name might not have [gist_id] suffix on rename
        # we use gist.key_name
        model = self.get_notebook(gist.key_name, new_path, content=False)
        return model

    def update_notebook(self, model, name, path=''):
        """Update the notebook's path and/or name"""
        path = path.strip('/')
        gist = self._get_gist(name, path)
        new_name = model.get('name', name)

        new_path = model.get('path', path).strip('/')
        if path != new_path :
            raise web.HTTPError(400, u'Gist backend does not support path change')

        # remove [gist_id] if we're being sent old key_name
        gist.name = gist.strip_gist_id(new_name)

        try:
            self.log.debug("Renaming notebook %s->%s", name, new_name)
            self.gisthub.save(gist)
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while renaming notebook: %s %s %s' % (path, name, e))
        # NOTE: since gist.name might not have [gist_id] suffix on rename
        # we use gist.key_name
        model = self.get_notebook(gist.key_name, new_path, content=False)
        return model

    def delete_notebook(self, name, path=''):
        """Delete notebook by name and path."""
        path = path.strip('/')
        gist = self._get_gist(name, path)
        gist.active = False
        try:
            self.log.debug("Deleting notebook %s %s", path, name)
            self.gisthub.save(gist)
        except Exception as e:
            raise web.HTTPError(400, u'Unexpected error while deleting notebook: %s %s %s' % (path, name, e))

    def get_checkpoint_model(self, commit):
        """construct the info dict for a given checkpoint"""
        info = dict(
            id = commit['id'],
            last_modified = commit['commit_date'],
        )
        return info

    def list_checkpoints(self, name, path=''):
        " each commit is a checkpoint "
        path = path.strip('/')
        gist = self._get_gist(name, path)
        revisions = gist.revisions
        checkpoints = map(self.get_checkpoint_model, revisions)
        return checkpoints

    def restore_checkpoint(self, checkpoint_id, name, path=''):
        """restore a notebook to a checkpointed state"""
        path = path.strip('/')
        self.log.info("restoring Notebook %s from checkpoint %s", name, checkpoint_id)
        gist = self._get_gist(name, path)
        for commit in gist.history:
            if checkpoint_id == commit['id']:
                return commit

    def info_string(self):
        return ''
