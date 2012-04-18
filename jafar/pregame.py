try:
    import json
except:
    import simplejson as json

import config
import validators
import auth
import sys

import base64
import sys
import os

from bottle import request, response, error, run, route, static_file

def wrap_object(root, obj, methods, **topkwargs):
    for i in methods:
        @api(path='%s%s' % (root, i), **topkwargs)
        def test(__method=i, **kwargs):
            return getattr(obj, __method)(**kwargs)

def route_to_app(url, loc):
    @route('%s' % url)
    @route('%s:path#.+#' % url)
    def server_static(path='/'):
        if path.endswith('/'):
            path += 'index.html'
        return static_file(path, root=loc)

def route_to_templates(url, loc):
    @route('%s' % url)
    @route('%s:path#.+#' % url)
    def server_static(path='/'):
        if path.endswith('/'):
            files = os.listdir(loc+'/'+path)
            files = filter(lambda x: os.path.isfile(loc+'/'+path+x), files)
            files = filter(lambda x: not x.endswith('~'), files)
            return json.dumps(files)
        else:
            return static_file(path, root=loc)

def init_base():
    import jafar
    if jafar.default_api:
        return jafar.default_api
    
    @error(404)
    def error404(error):
        return json.dumps(['error', 'There is no API call at this URL.'])

    @route('/_api_list/')
    def l():
        return jafar.default_api.nice_api()

    def get_data_page(name):
        for i in os.listdir('html'):
            check = i.split('.')[0]
            if check == name:
                return open('html/' + i).read()
        return ''

    @route('/favicon.ico')
    def favicon():
        return get_data_page('favicon')
    
    @route('/_api')
    def api_view():
        return get_data_page('index')

    @route('/_data/:path')
    def server_static_data(path):
        return get_data_page(path)

    jafar.default_api = config.JafarAPI()
    return jafar.default_api
    
def jafar_run(host='127.0.0.1', port=8080, reloader=True, config_d={}):
    import bottle
    bottle.debug(True)
    run(host=host, port=port, reloader=reloader)

