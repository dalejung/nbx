import os.path
import datetime

from tornado import web
from notebook.notebook.handlers import NotebookHandler

from .bundle.bundlenbmanager import BundleNotebookManager
from .path_translate import translate_path_shim


"""
monkey patch the notebook handler so we can redirect
"""
@web.authenticated
def get(self, path):
    cm = self.contents_manager
    path = path.strip('/')
    base = path.split('/')[0]
    for alias, mgr in cm.managers.items():
        if not isinstance(mgr, WorkareaManager):
            continue

        if alias == base:
            entry = mgr.get_entry(path)
            url = os.path.join(entry['manager_path'], entry['path'], entry['name'])
            self.redirect("/notebooks/"+url)
            return

    return self._old_get(path)

NotebookHandler._old_get = NotebookHandler.get
NotebookHandler.get = get

import string
import random
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def notebook_walk_step(self, path):
    notebooks = self.list_notebooks(path)
    dirs = self.list_dirs(path)
    subdirs = []
    for dir_model in dirs:
        name = dir_model.get('name')
        if name.startswith('.') or name.startswith('_'):
            continue
        new_path = os.path.join(path, name)
        subdirs.append(new_path)
    return notebooks, subdirs

def notebook_walk(self, path):
    notebooks, subdirs = notebook_walk_step(self, path)
    if any([notebooks, subdirs]):
        yield path, notebooks, subdirs
    for dir in subdirs:
        yield from notebook_walk(self, dir)

class WorkareaManager(BundleNotebookManager):
    def __init__(self, *args, **kwargs):
        workarea_paths = kwargs.pop('workarea_paths')
        self.managers = {}
        for alias, path in workarea_paths.items():
            self.managers[alias] = BundleNotebookManager(root_dir=path)

        # simple notebook full path => random uuid
        self.notebook_registry = {}
        super().__init__(*args, **kwargs)

    def get_entry(self, path):
        key_length = 6
        key = path[-(key_length+7):-7]
        entry = self.notebook_registry.get(key)
        return entry

    def is_notebook(self, path):
        if path:
            return True

    def path_exists(self, path):
        return not path

    def file_exists(self, name, path):
        # no file for root
        if not name and not path:
            return False
        return True

    def list_notebooks(self, path):
        all_notebooks = []

        registry = self.notebook_registry
        for k, manager in self.managers.items():
            manager_notebooks = []
            for p, notebooks, subdirs in notebook_walk(manager, path):
                manager_notebooks.extend(notebooks)

            for nb in manager_notebooks:
                path_key = k + '/' + os.path.join(nb['path'], nb['name'])
                if path_key not in registry:
                    key = id_generator()
                    entry = {'key':key, 
                             'path_key':path_key, 
                             'path': nb['path'], 
                             'name': nb['name'],
                             'manager_path':k
                             }
                    registry[path_key] = entry
                    registry[key] = entry
                nb['key'] = registry[path_key]['key']

            all_notebooks.extend(manager_notebooks)

        if len(all_notebooks) == 0:
            return []

        assert all(map(lambda x: isinstance(x['last_modified'], datetime.datetime), all_notebooks))

        all_notebooks.sort(key=lambda x: x['last_modified'], reverse=True)

        import math
        digits = 0
        if all_notebooks:
            digits = int(math.log10(len(all_notebooks)))+1
        for i, notebook in enumerate(all_notebooks, 1):
            dir_prefix = notebook['path'].rsplit('/')[-1] 
            name = notebook['name']
            name = "{dir}/{name}".format(name=name, dir=dir_prefix)
            name = name.strip('/')

            i = str(i).zfill(digits)
            name = "{i}. {name}".format(i=i, name=name)
            notebook['name'] = name

        longest_name = max(map(lambda x: len(x['name']), all_notebooks))
        for notebook in all_notebooks:
            last_modified = notebook['last_modified']
            date_string = last_modified.strftime('%Y-%m-%d')
            today = datetime.datetime.now().date()
            if last_modified.date() == today:
                date_string = 'Today'
            if last_modified.date() == today - datetime.timedelta(1):
                date_string = 'Yesterday'
            time_string = last_modified.strftime('%H:%M')
            datetime_string = "{date_string} {time_string}".format(date_string=date_string,
                                                                   time_string=time_string)
            name = notebook['name'].ljust(longest_name)
            notebook['name'] = "{name} [{datetime_string}] [{key}].ipynb".format(datetime_string=datetime_string,
                                                                            name=name,
                                                                           key=notebook['key'])

        return all_notebooks

    def list_dirs(self, path):
        return []




