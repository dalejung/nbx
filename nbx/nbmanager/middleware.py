import inspect
import functools

def manager_hook(func):
    """
    decorator to route manager method calls to middleware.


    # wrap manager call
    @manager_hook
    def save_notebook(self, model, path):
        pass

    # middleware to catch those hooks
    class Middleware(object):
        def pre_save_notebook(self, nbm, local_path, model, path):
            pass

        def post_save_notebook(self, nbm, local_path, model, path):
            pass
    """
    func_name = func.__name__
    argspec = inspect.getargspec(func)
    path_index = argspec.args.index('path') 
    path_index -= 1 # skip self
    @functools.wraps(func)
    def _wrapped(self, *args, **kwargs):
        # grab path based on argspec
        if len(args) > path_index:
            path = args[path_index]
        else:
            path = kwargs.get('path')
        nbm, meta = self._nbm_from_path(path)
        local_path = meta.path
        # call pre hook
        self.dispatch_middleware('pre_'+func_name, nbm, local_path, *args, **kwargs)
        res = func(self, *args, **kwargs)
        # call post hook
        # TODO: I should pass in res to post hook?
        self.dispatch_middleware('post_'+func_name, nbm, local_path, *args, **kwargs)
        return res
    return _wrapped

