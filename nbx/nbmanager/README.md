# MetaManager`/`GistNBManager 



##  Install

Install `nbx` with `pip` or put in `pythonpath`.

Using the `GistNBManager` requires you install [PyGithub](https://github.com/jacquev6/PyGithub)

edit **ipython_notebook_config.py**

```
c = get_config()
c.NotebookApp.notebook_manager_class = "nbx.nbmanager.MetaManager"

c.MetaManager.github_accounts = []
c.MetaManager.github_accounts.append((github_login, github_password))
```
