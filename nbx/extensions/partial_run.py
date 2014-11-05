"""
Currently `%run -m` will not bring back any variables if the module
execution errors. This will replicate the normal run behavior which 
acts like the code is executed in the IPython shell scope.
"""
import sys
from runpy import (_TempModule, _ModifiedArgv0, 
                   _get_module_details)

from IPython.core.interactiveshell import InteractiveShell, warn
from importlib._bootstrap import _SpecMethods

class TempModule:
    """
    Temporarily put module into sys.modules
    """
    def __init__(self, module):
        self.module = module
        self.mod_name = module.__name__
        self._saved_module = []

    def __enter__(self):
        mod_name = self.mod_name
        try:
            self._saved_module.append(sys.modules[mod_name])
        except KeyError:
            pass
        sys.modules[mod_name] = self.module
        return self

    def __exit__(self, *args):
        if self._saved_module:
            sys.modules[self.mod_name] = self._saved_module[0]
        else:
            del sys.modules[self.mod_name]
        self._saved_module = []

def _run_module_code(code, init_globals=None,
                    mod_name=None, mod_spec=None,
                    pkg_name=None, script_name=None):
    """Helper to run code in new namespace with sys modified"""
    fname = script_name if mod_spec is None else mod_spec.origin

    methods = _SpecMethods(mod_spec)
    module = methods.create()
    with TempModule(module) as temp_module, _ModifiedArgv0(fname):
        mod_globals = temp_module.module.__dict__
        try:
            methods.exec(module)
        except Exception as error:
            mod_globals['__run_module_error__'] = error
    # Copy the globals of the temporary module, as they
    # may be cleared when the temporary module goes away
    return mod_globals.copy()

def run_module(mod_name, init_globals=None,
               run_name=None, alter_sys=False):
    """Execute a module's code without importing it

       Returns the resulting top level namespace dictionary
    """
    mod_name, mod_spec, code = _get_module_details(mod_name)
    if run_name is None:
        run_name = mod_name
    if alter_sys:
        return _run_module_code(code, init_globals, run_name, mod_spec)
    else:
        # Leave the sys module alone
        return _run_code(code, {}, init_globals, run_name, mod_spec)

def safe_run_module(self, mod_name, where):
    """A safe version of runpy.run_module().

    This version will never throw an exception, but instead print
    helpful error messages to the screen.

    `SystemExit` exceptions with status code 0 or None are ignored.

    Parameters
    ----------
    mod_name : string
        The name of the module to be executed.
    where : dict
        The globals namespace.
    """
    try:
        try:
            run_globals = run_module(str(mod_name), run_name="__main__",
                                alter_sys=True)
            run_error = run_globals.get('__run_module_error__', None)
            run_globals.pop('__run_module_error__', None)
            # note, we update `where` regardless of error in module exec
            where.update(run_globals)
            if run_error:
                raise run_error
        except SystemExit as status:
            if status.code:
                raise
    except:
        self.showtraceback()
        warn('Unknown failure executing module: <%s>' % mod_name)

InteractiveShell.safe_run_module = safe_run_module
