from . import client
try:
    import urllib.request as urllib2
except:
    import urllib2

import urllib

def list_sessions(cl):
    cl.list_sessions()

def attach_session(cl, target):
    cl._list_sessions()
    cl.attach(target)

def kernel_pwd(cl, target):
    cl._list_sessions()
    return cl.kernel_path(target)

def main():
    import argparse
    import os
    parser = argparse.ArgumentParser(description="");

    parser.add_argument('action', nargs="?", action="store", default=None)
    parser.add_argument('target', nargs="?", action="store")
    parser.add_argument('--host', default="127.0.0.1")
    parser.add_argument('--port', default="8888")

    args = parser.parse_args()

    host = args.host
    port = args.port
    target = args.target
    action = args.action
    cwd = os.getcwd()

    cl = client.client(host, port)

    if not action and not target:
        action = 'list'

    if action in ['list']:
        list_sessions(cl)

    if action in ['attach']:
        attach_session(cl, target)

    if action in ['pwd']:
        import pipes
        print(kernel_pwd(cl, target))

if __name__ == '__main__':
    main()
