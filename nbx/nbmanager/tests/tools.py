from nose.tools import *

def assert_items_equal(*args):
    assert_equal(set(args[0]), set(args[1]))
