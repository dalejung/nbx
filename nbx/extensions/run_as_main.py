"""
Eventually this should be an easy way to interactively run __main__ code but
wrapped inside of functions.

This comes from being annoyed when working interactively on code and:

1. dealing with return/continue/break syntax differences
2. linters not highlighting unsued variables since everything is in global.
3. no easy way to run line profiler on __main__ code.

For now i have nbx_interact. eventually would like to just put a decorator
on a function and have it rewritten to call nbx_interact at end and before
every return.

@run_as_main
def example(return_early):
    d = 1
    if return_early:
        return
    blahblah

if return_early is True, I want d to be brought into global.

Not 100% sure if there is some way to hook into the execution like via trace.
or if it makes sense to just rewrite the wrapped function with ast.
"""
import sys
import ast
import inspect

from asttools import (
    ast_source,
)

from nbx import nbx_interact

def run_as_main(func):
    return func

@run_as_main
def main():
    print('hi')


def error():
    dale = 1
    nbx_interact()

error()
