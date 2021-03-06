import requests

class IPythonService(object):
    def __init__(self, host, port, token=None):
        self.host = host
        self.port = port
        self.token = token

    def _get(self, path, **kwargs):
        token = self.token
        if token:
            kwargs['headers'] = {'Authorization': f'token {token}'}
        url = 'http://{host}:{port}/{path}'.format(path=path, **self.__dict__)
        r = requests.get(url, **kwargs)
        return r.json()

    def sessions(self):
        return self._get('api/sessions')

    def server_info(self):
        return self._get('server-info')

    def kernel_info(self, kernel_id):
        return self._get('api/kernel-info/{kernel_id}'.format(kernel_id=kernel_id))

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
        print('\n'.join(lines))

    def _format_session(self, i, session):
        name = session['notebook']['path'].rsplit('/')[-1]
        return "[{i}] {name}".format(i=i, name=name)

    def _get_session(self, pos):
        session = self.sessions_cache[pos]
        return session

    def attach(self, pos):
        info = self.service.server_info()
        profile = info['profile']
        pos = int(pos)
        session = self._get_session(pos)
        print("=" * 80)
        name = session['notebook']['path'].rsplit('/')[-1]
        print("Attaching to {name}".format(name=name))
        print("=" * 80)
        return attach_session(session, profile=profile)

    def kernel_path(self, pos):
        info = self.service.server_info()
        profile = info['profile']
        pos = int(pos)
        session = self._get_session(pos)
        kernel_id = session['kernel']['id']
        kernel_info = self.service.kernel_info(kernel_id)
        kernel_path = kernel_info['kernel_path']
        return kernel_path

def attach_session(session, profile='default'):
    """
        Start a terminal app attached to a notebook
    """
    from jupyter_console import app
    kernel = 'kernel-{0}.json'.format(session['kernel']['id'])
    # TODO support other submodules like qtconsole
    argv = ['console', '--existing', kernel, '--profile={0}'.format(profile)]
    return app.launch_new_instance(argv=argv)

def client(host="127.0.0.1", port="8888", token=None):
    service = IPythonService(host, port, token)
    client = IPythonClient(service)
    return client
