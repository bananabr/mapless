import os
import json
import functools

from lib.http.jsonResponse import invalid_request
from lib.http.params import getParams


def log_context(func):
    def _logger(event, context):
        print('## ENVIRONMENT VARIABLES')
        print(os.environ)
        print('## EVENT')
        print(event)
        print('## CONTEXT')
        print(context)
        return func(event, context)
    return _logger


def requires(*required_params):
    '''
    A decorator to check for required parameters
    '''

    def decorator(validated_function):
        @functools.wraps(validated_function)
        def decorator_wrapper(event, context):
            params = getParams(event).keys()
            for param in required_params:
                if param in params:
                    continue
                print({"message": "{} is required".format(param)})
                return invalid_request({"message": "{} is required".format(param)})
            return validated_function(event, context)
        return decorator_wrapper
    return decorator

def allows(*allowed_params):
    '''
    A decorator to check for allowed parameters
    '''

    def decorator(validated_function):
        @functools.wraps(validated_function)
        def decorator_wrapper(event, context):
            params = getParams(event).keys()
            for param in params:
                if param not in allowed_params:
                    print({"message": "{} is not an allowed parameter".format(param)})
                    return invalid_request({"message": "{} is not an allowed parameter".format(param)})
            return validated_function(event, context)
        return decorator_wrapper
    return decorator

def allowed_values(param, allowed_values):
    '''
    A decorator to check for allowed parameter values
    '''

    def decorator(validated_function):
        @functools.wraps(validated_function)
        def decorator_wrapper(event, context):
            params = getParams(event)
            if params[param] not in allowed_values:
                print({"message": "{} is not an a valid value for parameter {}".format(params[param], param)})
                return invalid_request({"message": "{} is not an a valid value for parameter {}".format(params[param], param)})
            return validated_function(event, context)
        return decorator_wrapper
    return decorator
