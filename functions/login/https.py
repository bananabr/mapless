import json
import socket

import requests
from requests.auth import HTTPBasicAuth

from lib.http.jsonResponse import success, unauthorized, internal_server_error
from lib.http.decorators import log_context, requires, allows, allowed_values
from lib.http.params import getParams
from lib.http.websockets import send_to_connection


def test_auth(host, port=443, path='', user='admin', secret='admin'):
    r = requests.get(f'https://{host}:{port}/{path}',
                     auth=HTTPBasicAuth(user, secret))
    if r.status_code == 200:
        return True
    else:
        return False


@log_context
@requires('host')
@allows('host', 'port', 'username', 'password', 'path')
def handler(event, context):
    try:
        params = getParams(event)
        port = int(params.get('port', 443))
        username = params.get('username', 'admin')
        password = params.get('password', 'admin')
        path = params.get('path', '')

        if test_auth(params['host'], port=port, path=path, user=username, secret=password):
            return success(data=None)
        else:
            return unauthorized(data=None)

        
    except Exception as ex:
        return internal_server_error({
            "statusCode": 500,
            'error': str(ex)
        })


@log_context
@requires('host')
@allows('action', 'host', 'port', 'username', 'password', 'path')
@allowed_values('action', ['login_http'])
def ws_handler(event, context):
    try:
        params = getParams(event)
        result = {}
        port = int(params.get('port', 443))
        username = params.get('username', 'admin')
        password = params.get('password', 'admin')
        path = params.get('path', '')

        if test_auth(params['host'], port=port, path=path, user=username, secret=password):
            result[port] = True
            status = 200
        else:
            status = 401
            result[port] = False

        response = {
            "statusCode": status,
            "body": {
                'host': params['host'],
                'username': username,
                'password': password,
                'result': result
            }
        }

        send_to_connection(event['requestContext']['connectionId'], response)
    except Exception as ex:
        send_to_connection(event['requestContext']['connectionId'], {
            "statusCode": 500,
            'error': str(ex)
        })
