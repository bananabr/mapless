import json
import socket

import requests
from requests.auth import HTTPBasicAuth

from lib.http.jsonResponse import success, not_found, internal_server_error
from lib.http.decorators import log_context, requires, allows, allowed_values
from lib.http.params import getParams
from lib.http.websockets import send_to_connection


def test_path(host, port=80, path='', badstring=None, user=None, secret=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'
    }
    if user or secret:
        r = requests.get(f'http://{host}:{port}/{path}',
                         auth=HTTPBasicAuth(user, secret), headers=headers, allow_redirects=False)
    else:
        r = requests.get(f'http://{host}:{port}/{path}', headers=headers, allow_redirects=False)

    if r.status_code == 200 and r.text and badstring and badstring in r.text:
        return 404
    return r.status_code


@log_context
@requires('host')
@allows('host', 'port', 'username', 'password', 'path', 'badstring')
def handler(event, context):
    try:
        params = getParams(event)
        port = int(params.get('port', 80))
        username = params.get('username', None)
        password = params.get('password', None)
        path = params.get('path', '/')
        badstring = params.get('badstring', None)

        status = test_path(params['host'], port=port, path=path,
                           user=username, secret=password, badstring=badstring)
        if status != 404:
            return success(data={'path': path, 'status': status})
        else:
            return not_found(data=None)

    except Exception as ex:
        return internal_server_error({
            "statusCode": 500,
            'error': str(ex)
        })
