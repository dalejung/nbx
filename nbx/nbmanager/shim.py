from IPython.html.services.contents.manager import ContentsManager

from .util import get_invoked_arg, set_invoked_arg, _path_split

API = ['save', 'update', 'delete', 'get', 'rename', 'file_exists', 'exists',
       'get_checkpoint_path', 'get_checkpoint_model', 'create_checkpoint',
       'list_checkpoints', 'restore_checkpoint', 'delete_checkpoint',
       'get_kernel_path']

class ShimManager(ContentsManager):
    """
    Provide backwards compat to ipython removing name from its api calls

    This could be done with inspect and a metaclass
    """
    def __init__(self, *args, **kwargs):
        self._shim_cache = {}
        self._manager = self.__shim_target__(*args, **kwargs)
        super().__init__(*args, **kwargs)

    def __getattribute__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)

        if name in self._shim_cache:
            return self._shim_cache[name]

        if self._should_shim(name):
            meth = self._shim(name)
            self._shim_cache[name] = meth
            return meth

        # local defined in shim class
        if name in self.__dict__:
            return object.__getattribute__(self, name)

        if hasattr(self._manager, name):
            return getattr(self._manager, name)

        return object.__getattribute__(self, name)

    def _should_shim(self, name):
        return name in API

class ContentsNameApiShim(ShimManager):

    def _shim(self, name):
        current_api = getattr(ContentsManager, name)
        legacy = getattr(self._manager, name)
        def method(self, *args, **kwargs):
            args = list(args) # make mutable
            old_path = path = get_invoked_arg(current_api, 'path', args, kwargs)
            name, path = _path_split(path)
            set_invoked_arg(legacy, 'name', name, args, kwargs)
            set_invoked_arg(legacy, 'path', path, args, kwargs)

            # see if we're getting a model. update the name and path
            # in model to represent the old way
            try:
                model = get_invoked_arg(current_api, 'model', args, kwargs)
                model_path = model.get('path', '')
                model_name, model_path = _path_split(model_path)
                model['path'] = model_path
                model['name'] = model_name
                set_invoked_arg(legacy, 'model', model, args, kwargs)
            except:
                pass

            try:
                ret = legacy(*args, **kwargs)
                return ret
            except Exception as e:
                # TODO add debugging prints here
                raise e
        method = method.__get__(self)
        return method

    def rename(self, old_path, new_path):
        new_name, new_path = _path_split(new_path)
        old_name, old_path = _path_split(old_path)
        return self._manager.rename(old_name, old_path, new_name, new_path)

def contents_api_name(cls):
    """ class decorator """
    shim = ContentsNameApiShim
    cls_name = cls.__name__ + 'Shimmed'
    dct = {'__shim_target__' : cls}
    wrapper = type(cls_name, (shim,), dct)
    return wrapper
