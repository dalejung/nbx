# MetaManager/GistNotebookManager 

`MetaManager` is a `NotebookManager` that allows you to plug in multiple backends at the same time. For example, one can support the default `FileNotebookManager` and a `GistNotebookManager`. The two backends will live at the top level as folders.

## GistNotebookManager

The `GistNotebookManager` supports `gist` backed notebooks. It supports the organization of notebook via tagging. We only support one notebook per gist and we use the `gist.description` for the `name` and `tags`. 

![Gist Dashboard](https://www.evernote.com/shard/s9/sh/eed510fb-3f5e-4770-93c0-95806dde7837/35f824e1a5659f6165d080c085f321d3/deep/0/gist-3Afakedale-.png)

### Description Format

The `gist.description` format that we support is:

`Notebook Name #notebook #inactive #pandas #ipython`

`#notebook` is required for `GistNotebookManager` to process the gist.

`#inactive` is an optional tag declaring the gist deleted.

`#pandas`, `#ipython` are the tags. This notebook would show up under both.

Visit [fakedale gists](https://gist.github.com/fakedale) to see what a proper gist would look like.

### Current Limitations

**Cannot create new tags**

First of all, a tag doesn't exist unless it contains a notebook. This isn't a big deal except the notebook frontend doesn't give us a way to create directories/tags. Until then, you will have to create new tags by creating a new notebook via gist.github.com. 

**Cannot create private gists**

`ipycli` had a separate button to create a private gist. Existing private gists are supported, but the gui needs to be modified to support the distinction between public/private notebooks

##  Install

Install `nbx` with `pip` or put in `pythonpath`.

Using the `GistNotebookManager` requires you install [PyGithub](https://github.com/jacquev6/PyGithub)

edit **ipython_notebook_config.py**

```
c = get_config()
c.NotebookApp.notebook_manager_class = "nbx.nbmanager.MetaManager"

c.MetaManager.github_accounts = []
c.MetaManager.github_accounts.append((github_login, github_password))
```

