from tornado import web

from IPython.html.services.notebooks.nbmanager import NotebookManager
from IPython.nbformat import current

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
        return tags

    def gists_by_tag(self, tag):
        tagged = self.gist_query(tag)
        assert len(tagged) <= 1, "should only at most one tag"
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
        return notebooks

    def notebook_exists(self, name, path=''):
        gist = self._get_gist(name, path)
        return gist is not None

    def _get_gist(self, name, path):
        # get notebooks by tag
        gists = self.gists_by_tag(path)
        if name not in gists:
            print gists.keys(), name, path
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

            # save gist_id
            # nb['metadata']['gist_id'] = gist.id
            model['content'] = nb
        return model

    def save_notebook(self, model, name='', path=''):
        """Save the notebook model and return the model with no content."""
        path = path.strip('/')

        gist = self._get_gist(name, path)
        if 'content' not in model:
            raise web.HTTPError(400, u'No notebook JSON data provided')

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

        model = self.get_notebook(new_name, new_path, content=False)
        return model

    def update_notebook(self, model, name, path=''):
        """Update the notebook's path and/or name"""
        path = path.strip('/')
        gist = self._get_gist(name, path)
        new_name = model.get('name', name)

        # normalize to get real names
        new_name = gist.strip_gist_id(new_name)
        name = gist.strip_gist_id(name)

        new_path = model.get('path', path).strip('/')
        if path != new_path or name != new_name:
            self.rename_notebook(name, path, new_name, new_path)
        model = self.get_notebook(new_name, new_path, content=False)
        return model

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
