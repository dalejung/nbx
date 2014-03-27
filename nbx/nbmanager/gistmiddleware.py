from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import (
    Dict, Unicode, Integer, List, Bool, Bytes,
    DottedObjectName, TraitError, Tuple,
)

from .gist import GistService, model_to_files
from .bundle.bundlenbmanager import BundleNotebookManager
from IPython.html.services.notebooks.filenbmanager import FileNotebookManager

class GistMiddleware(LoggingConfigurable):
    """
    This middleware will save to github if the notebook metadata contains a
    gist_id.

    This requires that the Gist is owned by an account we control.
    """
    github_accounts = List(Tuple, config=True,
                            help="List of Tuple(github_account, github_password)")

    def __init__(self, *args, **kwargs):
        super(GistMiddleware, self).__init__(*args, **kwargs)

        self.service = GistService()
        for user, pw in self.github_accounts:
            self.service.login(user, pw)

    def post_save_notebook(self, nbm, local_path, model, name, path):
        # for now only support bundlenbmanager
        if not isinstance(nbm, (BundleNotebookManager, FileNotebookManager)):
            return

        gist_id = model['content']['metadata'].get('gist_id', None)
        if gist_id is None:
            return
        gist = self.service.get_gist(gist_id)
        if not self.service.is_owned(gist):
            return

        try:
            # this is only applicable to bundles
            model = nbm.get_notebook(name, local_path, content=True, file_content=True)
        except:
            model = nbm.get_notebook(name, local_path, content=True)

        files = model_to_files(model)
        gist.save(description=name, files=files)
        msg = "Saved notebook {path} {name} to gist {gist_id}".format(name=name,
                                                            path=local_path,
                                                            gist_id=gist_id)
        self.log.info(msg)
