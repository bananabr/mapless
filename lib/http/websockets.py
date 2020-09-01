import os
import json

import boto3


def send_to_connection(connection_id, data):
    endpoint = os.environ['WEBSOCKET_API_ENDPOINT']
    gatewayapi = boto3.client("apigatewaymanagementapi",
                              endpoint_url=endpoint)
    return gatewayapi.post_to_connection(ConnectionId=connection_id,
                                         Data=json.dumps(data).encode('utf-8'))
