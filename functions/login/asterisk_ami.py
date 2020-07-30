import json
import socket

from lib.http.jsonResponse import success, unauthorized, internal_server_error
from lib.http.decorators import log_context, requires, allows, allowed_values
from lib.http.params import getParams


from asterisk.ami import AMIClient

def test_auth(host, port=7777, user='admin', secret='admin'):
    client = AMIClient(address=host,port=port)
    future = client.login(username=user,secret=secret)
    response = future.response
    if response:
        if response.is_error():
            return False
        else:
            client.logoff()
            return True
    else:
        return False


@log_context
@requires('host')
@allows('host', 'port', 'username', 'password')
def handler(event, context):
    try:
        params = getParams(event)
        port = int(params.get('port', 7777))
        username = params.get('username', 'admin')
        password = params.get('password', 'admin')

        if test_auth(params['host'], port=port, user=username, secret=password):
            return success(data=None)
        else:
            return unauthorized(data=None)
    except Exception as ex:
        return internal_server_error({
            'error': str(ex)
        })
