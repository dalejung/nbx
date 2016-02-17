import os
import io

import nbformat
from IPython.utils import tz


class Bundle(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.bundle_path = os.path.join(path, name)

    def __repr__(self):
        cname = self.__class__.__name__
        return "{cname}(name={name}, path={path})".format(cname=cname,
                                                          **self.__dict__)

    @property
    def files(self):
        try:
            root, dirs, files = next(os.walk(self.bundle_path))
            # filter out compiled files
            files = filter(lambda x: not x.endswith('.pyc'), files)
            files = list(files)
        except StopIteration:
            files = []
        return files

class NotebookBundle(Bundle):

    @property
    def notebook_content(self):
        filepath = os.path.join(self.bundle_path, self.name)
        with io.open(filepath, 'r', encoding='utf-8') as f:
            try:
                nb = nbformat.read(f, as_version=4)
            except Exception as e:
                nb = None
            return nb

    @property
    def files(self):
        files = super(NotebookBundle, self).files
        assert self.name in files
        files.remove(self.name)
        assert self.name not in files
        return files

    def get_model(self, content=True, file_content=True):
        os_path = os.path.join(self.bundle_path, self.name)
        info = os.stat(os_path)
        last_modified = tz.utcfromtimestamp(info.st_mtime)
        created = tz.utcfromtimestamp(info.st_ctime)
        # Create the notebook model.
        model = {}
        model['name'] = self.name
        model['path'] = self.path
        model['last_modified'] = last_modified
        model['created'] = created
        model['type'] = 'notebook'
        model['is_bundle'] = True
        model['content'] = None
        if content:
            model['content'] = self.notebook_content
        files = {}
        for fn in self.files:
            with open(os.path.join(self.bundle_path, fn), 'rb') as f:
                data = None
                if file_content:
                    try:
                        data = f.read().decode('utf-8')
                    except UnicodeDecodeError:
                        # TODO how to deal with binary data?
                        # right now we skip
                        continue
                files[fn] = data
        model['__files'] = files
        return model
