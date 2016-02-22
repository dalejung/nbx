import six


def load_ipython_extension(shell):
    # only run for python 3, or else syntax errors
    if not six.PY3:
        return
    from ._partial_run import safe_run_module
    shell.safe_run_module = safe_run_module.__get__(shell)
