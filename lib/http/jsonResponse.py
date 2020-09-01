import json
import decimal


def _http_return(code, data):
    if data:
        body = json.dumps(data)
    else:
        body = None

    return {
        "statusCode": code,
        "body": body,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Origin": "*"
        }
    }


def success(data={}):
    return _http_return(200, data)


def invalid_request(data={"message": "Invalid request"}):
    return _http_return(400, data)

def unauthorized(data={"message": "Unauthorized"}):
    return _http_return(401, data)

def not_found(data={"message": "resource not found"}):
    return _http_return(404, data)


def internal_server_error(data={"message": "internal server error"}):
    return _http_return(500, data)


def service_unavailable(data={"message": "service unavailable"}):
    return _http_return(503, data)
