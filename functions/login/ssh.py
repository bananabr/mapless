import json
import socket

from lib.http.jsonResponse import success, unauthorized, internal_server_error
from lib.http.decorators import log_context, requires, allows, allowed_values
from lib.http.params import getParams
from lib.http.websockets import send_to_connection

import paramiko
from paramiko import SSHClient
from paramiko import AuthenticationException


def test_auth(host, port=22, user='root', secret='password'):
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, port=port, username=user, password=secret)
        client.close()
        return True
    except AuthenticationException:
        return False


@log_context
@requires('host')
@allows('host', 'port', 'username', 'password')
def handler(event, context):
    try:
        params = getParams(event)
        port = int(params.get('port', 22))
        username = params.get('username', 'root')
        password = params.get('password', 'password')

        if test_auth(params['host'], port=port, user=username, secret=password):
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
@allows('action', 'host', 'port', 'username', 'password')
@allowed_values('action', ['login_ssh'])
def ws_handler(event, context):
    try:
        params = getParams(event)

        result = {}
        port = int(params.get('port', 22))
        username = params.get('username', '')
        password = params.get('password', 'password')

        if test_auth(params['host'], port=port, user=username, secret=password):
            result[port] = True
        else:
            result[port] = False

        response = {
            "statusCode": 200,
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
