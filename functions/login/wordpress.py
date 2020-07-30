import json
import socket

from lib.http.jsonResponse import success, unauthorized, internal_server_error
from lib.http.decorators import log_context, requires, allows, allowed_values
from lib.http.params import getParams
from lib.http.websockets import send_to_connection

import wordpress_xmlrpc
from wordpress_xmlrpc import Client, WordPressPost, InvalidCredentialsError

def test_auth(host, port=80, path='', user='admin', secret='admin'):

	try:
		client = Client(f'http://{host}:{port}/{path}/xmlrpc.php', user, secret)
		client.call(wordpress_xmlrpc.methods.users.GetUsers())
		return True
	except InvalidCredentialsError:
		return False

@log_context
@requires('host')
@allows('host', 'port', 'username', 'password', 'path')
def handler(event, context):
	try:
		params = getParams(event)
		port = int(params.get('port', 80))
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
