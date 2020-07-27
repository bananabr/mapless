import json
import socket

from lib.http.jsonResponse import success, internal_server_error
from lib.http.decorators import log_context, requires, allows, allowed_values
from lib.http.params import getParams


def isOpen(ip, port, timeout=5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False


@log_context
@requires('host', 'port')
@allows('host', 'port', 'scan', 'timeout')
def handler(event, context):
    try:
        params = getParams(event)
        port = int(params['port'])
        timeout = int(params.get('timeout', 5))
        if isOpen(params['host'], port, timeout=timeout):
            result = True
        else:
            result = False

        response = {
                'host': params['host'],
                'port': port,
                'open': result
        }

        return success(response)
    except Exception as ex:
        return internal_server_error({
            'error': str(ex),
            'context': event
        })
