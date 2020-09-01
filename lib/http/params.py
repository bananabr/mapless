import json

def getParams(event):
    result = {}
    if(event.get('pathParameters', None)):
        result.update(event.get('pathParameters',{}))
    if(event.get('queryStringParameters', None)):
        result.update(event.get('queryStringParameters',{}))
    if(event.get('body', None)):
        if event['headers']['Content-Type'] == 'application/json':
            result.update(json.loads(event.get('body','{}')))
        elif event['headers']['Content-Type'] == 'application/x-www-form-urlencoded':
            result.update({ k: v for k,v in [ v.split('=') for v in event.get('body','').split('&') ] })
    return result
