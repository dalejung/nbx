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
    butt = 123
    nbx_interact()

error()
