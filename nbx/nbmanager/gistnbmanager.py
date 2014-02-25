from IPython.html.services.notebooks.nbmanager import NotebookManager


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
        tags = self.gisthub.query(tag, filter_tag='#notebook')
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
        # get notebooks by tag
        gists = self.gists_by_tag(path)
        ret = name in gists
        return ret

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
        # Create the notebook model.
        model ={}
        model['name'] = name
        model['path'] = path
        #model['last_modified'] = last_modified
        #model['created'] = created
        model['type'] = 'notebook'
        if content:
            print 'content', name
            with io.open(os_path, 'r', encoding='utf-8') as f:
                try:
                    nb = current.read(f, u'json')
                except Exception as e:
                    raise web.HTTPError(400, u"Unreadable Notebook: %s %s" % (os_path, e))
            self.mark_trusted_cells(nb, path, name)
            model['content'] = nb
        return model

    def info_string(self):
        return ''
