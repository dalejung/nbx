from IPython.html.notebookapp import NotebookWebApplication

def load_handlers(name):
    """Load the (URL pattern, handler) tuples for each component."""
    if name.startswith('.'):
        name = 'IPython.html' + name
    mod = __import__(name, fromlist=['default_handlers'])
    return mod.default_handlers

def enable_custom_handlers():
    """
    Figured out a trojan horse to enable the following PR.
    https://github.com/ipython/ipython/pull/5190
    Just in case it doesn't go through.
    """
    old_init_handlers = NotebookWebApplication.init_handlers

    def init_handlers(self, settings):

        handlers = []
        # Allow for custom handlers via config
        custom_handlers = settings.get("custom_handlers", {})
        for mname in custom_handlers:
            try:
                handlers.extend(load_handlers(mname))
            except:
                # TODO what to on error?
                raise
        # note that the base init_handlers has a 404 catch all
        # it needs to always be last
        handlers.extend(old_init_handlers(self, settings))
        return handlers

    NotebookWebApplication.init_handlers = init_handlers
