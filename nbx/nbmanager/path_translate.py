from notebook.services.contents.manager import ContentsManager

from .shim import ShimManager
from .util import get_invoked_arg, set_invoked_arg, _path_split

class PathTranslateShim(ShimManager):
    """
    Provide backwards compat to ipython removing name from its api calls

    This could be done with inspect and a metaclass
    """
    def __init__(self, *args, **kwargs):
        self._shim_cache = {}
        self._manager = self.__shim_target__(*args, **kwargs)
        super().__init__(*args, **kwargs)

    def _should_shim(self, name):
        if name in ['get_notebook']:
            return True
        return False

    def _shim(self, name):
        legacy = getattr(self._manager, name)
        def method(self, *args, **kwargs):
            args = list(args) # make mutable
            old_name = name = get_invoked_arg(legacy, 'name', args, kwargs)
            name = self.translate_path(name)
            name, path = _path_split(name)
            set_invoked_arg(legacy, 'name', name, args, kwargs)
            set_invoked_arg(legacy, 'path', path, args, kwargs)

            # see if we're getting a model. update the name and name
            # in model to represent the old way
            try:
                model = get_invoked_arg(legacy, 'model', args, kwargs)
                model_name = model.get('name', '')
                model_name = self.translate_path(model_name)
                model_name, model_path = _path_split(model_name)
                model['name'] = model_name
                model['path'] = model_path
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

    def translate_path(self, path):
        raise NotImplemented()

def translate_path_shim(cls):
    """ class decorator """
    shim = PathTranslateShim
    cls_name = cls.__name__ + 'Shimmed'
    dct = {'__shim_target__' : cls}
    wrapper = type(cls_name, (shim,), dct)
    return wrapper

