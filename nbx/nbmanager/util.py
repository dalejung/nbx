import inspect

def _path_split(path):
    bits = path.rsplit('/', 1)
    path = ''
    name = bits.pop()
    if bits:
        path = bits[0]
    return name, path

def get_invoked_arg(func, name, args, kwargs):
    var = None
    if name in kwargs:
        var = kwargs[name]
        return var

    argspec = inspect.getargspec(func)
    if name not in argspec.args:
        raise Exception('{name} was not found in invoked function'.format(name=name))

    index = argspec.args.index(name)
    # we're assuming self is not in *args for method calls
    if argspec.args[0] == 'self':
        index -= 1
    var = args[index]
    return var

def set_invoked_arg(func, name, value, args, kwargs):
    """
    Based on a target argspec, we try to place the param
    value in the correct args/kwargs spot so that it works
    in the target.
    """
    if isinstance(args, tuple):
        raise Exception("args must be a list")

    # handle functools.wraps functions. specifically the middleware
    if hasattr(func, '__wrapped__'):
        argspec = inspect.getargspec(func.__wrapped__)
    else:
        argspec = inspect.getargspec(func)

    # assume that if var is in kwargs, it should stay there.
    # possible that source func had name in kwargs, but target has
    # the name in args (positionally). not handling for now
    if name in kwargs or name not in argspec.args:
        kwargs[name] = value
        return

    index = argspec.args.index(name)
    num_args = len(argspec.args)
    # we're assuming self is not in args for method calls
    if argspec.args[0] == 'self':
        index -= 1
        num_args -= 1

    if len(args) == num_args:
        args[index] = value
    else:
        args.insert(index, value)

    return args, kwargs

