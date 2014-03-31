

import os.path

from tornado import web

import IPython
from zmq.utils import jsonapi
from nbx.handlers import NBXHandler
import nbx.kernel_client as kernel_client

PWD_CODE = """
from IPython.utils import py3compat
py3compat.getcwd()
"""

class KernelInfo(NBXHandler):

    @web.authenticated
    def get(self, kernel_id):
        km = self.kernel_manager
        client = km.get_kernel(kernel_id).client()
        client = kernel_client.KernelClient(client)

        data = client.execute(PWD_CODE)
        client.exit()

        model = km.kernel_model(kernel_id)
        kernel_path = '';
        if 'text/plain' in data:
            kernel_path = eval(data['text/plain'])
        model['kernel_path'] = kernel_path

        self.finish(jsonapi.dumps(model))

_kernel_id_regex = r"(?P<kernel_id>\w+-\w+-\w+-\w+-\w+)"

default_handlers = [
    (r"/api/kernel-info/%s" % (_kernel_id_regex), KernelInfo),
]
