class NBXInteract(Exception):
    pass


def nbx_interact():
    """
    Utility func that will raise a special exception that causes partialrun to
    copy the frames local variables into global. Useful for dumping out
    function variables so you can debug in ipython without pdb.
    """
    # TODO add a check to see if we are running in a compatible env.
    raise NBXInteract()


RUN_AS_MAIN_CODES = set()


def run_as_main(func):
    """
    Decorate a func as pseudo main.

    1. Marks the function as being the frame where locals are globalized from.

    NOTES:
        Marking code by just tagging it might not be enough. Like what if
        something ends up being recursive?
    """
    code = func.__code__
    # TODO weakref this?
    RUN_AS_MAIN_CODES.add(code)
    return func


def is_code_run_as_main(code):
    return code in RUN_AS_MAIN_CODES


def find_run_as_main(f):
    while True:
        if f.f_code and is_code_run_as_main(f.f_code):
            return f

        # there is no more frames
        if not f.f_back:
            return False

        f = f.f_back
