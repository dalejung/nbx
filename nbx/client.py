import requests

class IPythonService(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def _get(self, path, **kwargs):
        url = 'http://{host}:{port}/{path}'.format(path=path, **self.__dict__)
        r = requests.get(url, **kwargs)
        return r.json()

    def _post(self, path, **kwargs):
        url = 'http://{host}:{port}/{path}'.format(path=path, **self.__dict__)
        r = requests.post(url, **kwargs)
        return r.json()

    def sessions(self):
        return self._get('api/sessions')

    def server_info(self):
        return self._get('server-info')

class IPythonClient(object):
    def __init__(self, service):
        self.service = service
        self.sessions_cache = None

    def _list_sessions(self):
        sessions = self.service.sessions()
        self.sessions_cache = sessions
        lines = [self._format_session(i, session) for i, session in enumerate(sessions)]
        return lines

    def list_sessions(self):
        lines = []
        lines.append("Active Kernels:")
        lines.append("====================")
        lines.extend(self._list_sessions())
        print '\n'.join(lines)

    def _format_session(self, i, session):
        return "[{i}] {name}".format(i=i, name=session['notebook']['name'])

    def _get_session(self, pos):
        session = self.sessions_cache[pos]
        return session

    def attach(self, pos):
        info = self.service.server_info()
        profile = info['profile']
        pos = int(pos)
        session = self._get_session(pos)
        print "=" * 80
        print "Attaching to {name}".format(name=session['notebook']['name'])
        print "=" * 80
        return attach_session(session, profile=profile)

def attach_session(session, profile='default'):
    """
        Start a terminal app attached to a notebook
    """
    from IPython.terminal.ipapp import launch_new_instance
    kernel = 'kernel-{0}.json'.format(session['kernel']['id'])
    # TODO support other submodules like qtconsole
    argv = ['console', '--existing', kernel, '--profile={0}'.format(profile)]
    return launch_new_instance(argv=argv)

def client(host="127.0.0.1", port="8888"):
    service = IPythonService(host, port)
    client = IPythonClient(service)
    return client
