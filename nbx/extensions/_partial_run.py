"""
Currently `%run -m` will not bring back any variables if the module
execution errors. This will replicate the normal run behavior which 
acts like the code is executed in the IPython shell scope.
"""
import sys
from runpy import (_ModifiedArgv0, _TempModule,
                   _get_module_details, _run_code)

from IPython.core.interactiveshell import warn
from nbx import (
    NBXInteract,
    find_run_as_main,
)


def get_f_locals_from_exception(frames_back=None):
    f = get_frame_from_exception(frames_back)
    return f.f_locals.copy()


def get_frame_from_exception(frames_back=None):
    tb = sys.exc_info()[2]
    f = find_correct_frame(tb, frames_back)
    return f


def find_correct_frame(tb, frames_back=None):
    """
    Logic to find the correct frame to globalize their local variables.
    """
    while 1:
        if not tb.tb_next:
            break
        tb = tb.tb_next
    f = tb.tb_frame
    # TODO reliable to just skip based on tb.tb_frame.f_code.co_name to skp
    # nbx_interact?
    # TODO check RUN_AS_MAIN
    if frames_back is not None:
        for x in range(frames_back):
            f = f.f_back
    else:
        # this is usually needed for real exception that occur deeper in the
        # stack. we don't want to globalize locals *where* the exception
        # occurs because that can be inside library code.
        main_f = find_run_as_main(f)
        if main_f:
            f = main_f
    return f


def _run_module_code(code, init_globals=None,
                     mod_name=None, mod_spec=None,
                     pkg_name=None, script_name=None):
    """Helper to run code in new namespace with sys modified"""
    fname = script_name if mod_spec is None else mod_spec.origin

    with _TempModule(mod_name) as temp_module, _ModifiedArgv0(fname):
        mod_globals = temp_module.module.__dict__
        try:
            _run_code(code, mod_globals, init_globals,
                      mod_name, mod_spec, pkg_name, script_name)
        except Exception as error:
            if isinstance(error, NBXInteract):
                f = get_frame_from_exception(frames_back=1)
            else:
                mod_globals['__run_module_error__'] = error
                # TODO make this configurable.
                # assuming
                f = get_frame_from_exception()

            f_locals = f.f_locals.copy()
            mod_globals.update(f_locals)
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
    raise Exception("alter_sys must be true")


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
    except Exception:
        self.showtraceback(tb_offset=3)
        warn('Unknown failure executing module: <%s>' % mod_name)
