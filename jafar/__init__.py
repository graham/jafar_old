from bottle import run, static_file, redirect, response, request
default_api = None

from jafar.pregame import init_base, route_to_app, route_to_templates, jafar_run

## Helpful commands for starting jafar.
def start(host='127.0.0.1', port=8080, reloader=True, config_d={}):
    run(host=host, port=port, reloader=reloader)

def set_cookie(*args, **kwargs):
    return response.set_cookie(*args, **kwargs)

def get_cookie(*args, **kwargs):
    return request.get_cookie(*args, **kwargs)

## simple caching of data.
cached_data = {}
def get(key):
    return cached_data[key]
def set(key, value):
    cached_data[key] = value

import urlparse
## helpful things for your app.
def get_host():
    return urlparse.urlparse(request.url).netloc
