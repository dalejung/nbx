#!/usr/bin/env python

import nbx.client as client
import urllib2
import urllib

PORT = 8888
HOST = "127.0.0.1"

def open_notebook(fullpath):
    if os.path.isfile(fullpath):
        print 'found file'
        open_url(fullpath)
        return

    path, file = os.path.split(fullpath)
    if not file.endswith('ipynb'):
        file = file + '.ipynb'

    print 'opening new notebook'
    fullpath = os.path.join(path, file)
    new_url(fullpath)

def add_notebooks(action, filepath, cwd):
    fullpath = os.path.join(cwd, filepath)
    if action == "notebook":
        open_notebook(fullpath)
    elif action == "add-dir":
        add_dir(fullpath)

def list_sessions():
    client.client(HOST, PORT).list_sessions()

def attach_session(target):
    cl = client.client(HOST, PORT)
    cl._list_sessions()
    cl.attach(target)

def main():
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Start a notebook");

    parser.add_argument('action', nargs="?", action="store", default=None)
    parser.add_argument('target', nargs="?", action="store")

    args = parser.parse_args()

    target = args.target
    action = args.action
    cwd = os.getcwd()

    if not action and not target:
        action = 'list'

    if action in ['list']:
        list_sessions()

    if action in ['attach']:
        attach_session(target)

if __name__ == '__main__':
    main()
