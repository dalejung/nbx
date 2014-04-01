# Features 

* MetaManager, allows multiple `NotebookManager`.
* Gist backend
* Bundle backend
* Gist middleware (will save notebooks to gist on every save)
* `standalone` handler Allows ipython to serve pages that connect to kernel but don't exist within the notebook interface. 
* vim keymapping

# Setup

Install the github package.

```
git clone git@github.com:dalejung/nbx.git
pip install ./nbx`
```

Example `ipython_notebook_config.py`

```
c = get_config()

c.NotebookApp.webapp_settings = {}
c.NotebookApp.webapp_settings['custom_handlers'] = ['nbx.handlers.test']

# allow requests from non origin. Needed for standalone handler
headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET,PUT,POST,DELETE,OPTIONS",
    "Access-Control-Allow-Headers":"Content-Type, Depth, User-Agent, X-File-Size, X-Requested-With, X-Requested-By, If-Modified-Since, X-File-Name, Cache-Control",
}
c.NotebookApp.webapp_settings['headers'] = headers

# IMPORTANT. This is how many of the monkey patches are loaded from
c.NotebookApp.notebook_manager_class = "nbx.nbmanager.metamanager.MetaManager"

# github accounts for gist backend
c.MetaManager.github_accounts = []
c.MetaManager.github_accounts.append(('user', 'password'))

# Add additional file based notebook dirs
c.MetaManager.file_dirs = {}
c.MetaManager.file_dirs['other-dir'] = '~/Dropbox/notebooks'

# Add bundle notebooks
c.MetaManager.bundle_dirs = {}
c.MetaManager.bundle_dirs['bundle_test'] = '~/Dropbox/bundles'

# added github accounts to gist middleware
c.GistMiddleware.github_accounts = []
c.GistMiddleware.github_accounts.append(('user', 'login'))

# add middleware
c.MetaManager.manager_middleware = {}
c.MetaManager.manager_middleware['gist'] = 'nbx.nbmanager.gistmiddleware.GistMiddleware'
```

# nbx cli tools

Command line tools to manage notebook sessions.

```
usage: nbx [-h] [--host HOST] [--port PORT] [action] [target]

positional arguments:
  action
  target
```

[Expanded Docs](nbx/cli/README.md)
