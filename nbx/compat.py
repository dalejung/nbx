import sys

PY3 = (sys.version_info[0] >= 3)

if PY3:
    string_types = str,
    binary_types = bytes,
else:
    string_types = basestring,
    binary_types = str,
