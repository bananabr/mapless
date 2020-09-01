import json
import socket

import requests
from requests.auth import HTTPBasicAuth

from lib.http.jsonResponse import success, not_found, internal_server_error
from lib.http.decorators import log_context, requires, allows, allowed_values
from lib.http.params import getParams
from lib.http.websockets import send_to_connection


def test_path(host, port=80, path='', user=None, secret=None):
    if user or secret:
        r = requests.get(f'http://{host}:{port}/{path}',
                        auth=HTTPBasicAuth(user, secret))
    else:
        r = requests.get(f'http://{host}:{port}/{path}')
    return r.status_code


@log_context
@requires('host')
@allows('host', 'port', 'username', 'password', 'path')
def handler(event, context):
    try:
        params = getParams(event)
        port = int(params.get('port', 80))
        username = params.get('username', None)
        password = params.get('password', None)
        path = params.get('path', '/')

        status = test_path(params['host'], port=port, path=path, user=username, secret=password)
        if  status != 404:
            return success(data={'status': status})
        else:
            return not_found(data=None)

        
    except Exception as ex:
        return internal_server_error({
            "statusCode": 500,
            'error': str(ex)
        })
