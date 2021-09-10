class NBXInteract(Exception):
    pass


def nbx_interact():
    """
    Utility func that will raise a special exception that causes partialrun to
    copy the frames local variables into global. Useful for dumping out
    function variables so you can debug in ipython without pdb.
    """
    raise NBXInteract()
