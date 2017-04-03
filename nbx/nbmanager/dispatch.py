"""
Tools to help create dispatched methods for the Contents API.

The Contents api has a single function like save, get_model that
handles multiple types (file, notebook, dir).

The main logic is in normal functions that the Mixin wraps. This is so the
logic can be used easily in the Middleware object.

Not 100% on this.
"""
def _model_type_from_path(self, path):
    if self.is_dir(path):
        model_type = 'dir'
    elif self.is_notebook(path):
        model_type = 'notebook'
    else:
        model_type = 'file'
    return model_type

def dispatch_method(self, hook, model_type, *args, **kwargs):
    # call type specific hook
    method_name = "{hook}_{type}".format(hook=hook, type=model_type)
    method = getattr(self, method_name, None)
    if method:
        return method(*args, **kwargs)

    # try default
    default_name = '{hook}_default'.format(hook=hook)
    try:
        default_method = getattr(self, default_name)
    except:
        raise AttributeError("Could not find method for {0} {1}".format(hook, model_type))
    return default_method(*args, **kwargs)

def get(self, path='', content=True, dispatcher=dispatch_method, **kwargs):
    """
    Relies on:
        is_dir
        is_notebook
    """
    path = path.strip('/')

    model_type = _model_type_from_path(self, path)
    return dispatcher(self, 'get', model_type,
                            path=path, content=content, **kwargs)

def save(self, model, path='', dispatcher=dispatch_method):
    if 'type' not in model:
        raise Exception(u"Model has no file type")
    model_type = model['type']
    return dispatcher(self, 'save', model_type, model, path=path)

def update(self, model, path='', dispatcher=dispatch_method):
    # right now, ipython only supports notebook renames via PATCH
    model_type = 'notebook'
    return dispatcher(self, 'update', model_type, model, path=path)

def delete(self, path='', dispatcher=dispatch_method):
    model_type = _model_type_from_path(self, path)
    return dispatcher(self, 'delete', model_type, path=path)

class DispatcherMixin(object):
    """
    This Mixin class handles the dispatching of Contents API calls to
    model type specific methods.

    i.e. get_model for a directory would call get_model_dir
    """

    def save(self, model, path=''):
        return save(self, model, path,
                             dispatcher=self.dispatch_method.__func__)

    def update(self, model, path=''):
        return update(self, model, path,
                             dispatcher=self.dispatch_method.__func__)

    def delete(self, path=''):
        return delete(self, path,
                             dispatcher=self.dispatch_method.__func__)

    def get(self, path='', content=True, **kwargs):
        return get(self, path, content,
                                  dispatcher=self.dispatch_method.__func__, **kwargs)

    def dispatch_method(self, hook, model_type, *args, **kwargs):
        return dispatch_method(self, hook, model_type, *args, **kwargs)
