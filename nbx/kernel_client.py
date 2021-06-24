from jupyter_client import find_connection_file
from jupyter_client.manager import KernelManager

import time

def run_cell(client, cell, store_history=True):
    """
    Taken from ipython.frontend.terminal.console.ZMQInteractiveShell
    """
    if (not cell) or cell.isspace():
        return

    # flush stale replies, which could have been ignored, due to missed heartbeats
    while client.shell_channel.msg_ready():
        client.shell_channel.get_msg()


    # shell_channel.execute takes 'hidden', which is the inverse of store_hist
    msg_id = client.shell_channel.execute(cell, not store_history)
    while not client.shell_channel.msg_ready(): # wait for completion
        pass

    if client.shell_channel.msg_ready():
        handle_execute_reply(client, msg_id)

    # meh. sometimes iopub doesn't have the pyout.
    # sleep for 100ms to make sure it's in there
    # probably shouldn't be here
    data = get_pyout(client)
    return data

def handle_execute_reply(client, msg_id):
    msg = client.shell_channel.get_msg()

    if msg["parent_header"].get("msg_id", None) == msg_id:
        content = msg["content"]
        status = content['status']
        if status == 'aborted':
            #self.write('Aborted\n')
            return
        elif status == 'ok':
            # print execution payloads as well:
            for item in content["payload"]:
                text = item.get('text', None)
                if text:
                    pass
        elif status == 'error':
            for frame in content["traceback"]:
                print(frame)

def get_pyout(client):
    """
    Listen to iopub messages until we get notified that the kernel is idle
    """
    data = None
    while True:
        time.sleep(.1)
        sub_msg = client.iopub_channel.get_msg()
        msg_type = sub_msg['header']['msg_type']
        parent = sub_msg["parent_header"]

        if parent and client.session.session != parent['session']:
            continue

        # only treat the execute_result as data. ignore stream message types
        # aka print results
        if msg_type in ['execute_result']:
            assert data is None
            data = sub_msg['content']['data']
            continue

        # we are done now.
        if msg_type == 'status' and sub_msg['content']['execution_state'] == 'idle':
            return data

class KernelClient(object):
    def __init__(self, client):
        self.client = client
        self.client.start_channels()

    def execute(self, code):
        data = run_cell(self.client, code)
        return data

    def exit(self):
        self.client.stop_channels()

def get_client(cf, profile=None):
    """
    Usage:
        >>> kc = get_client('kernel-143a2687-f294-42b1-bdcb-6f1cc2f4cc87.json', 'dale')
        >>> data = kc.execute("'123'")
        >>> data
        {u'text/plain': u'123'}
    """
    connection_file = find_connection_file(cf, profile=profile)
    km = KernelManager(connection_file=connection_file)
    km.load_connection_file()

    client = km.client()
    return KernelClient(client)
