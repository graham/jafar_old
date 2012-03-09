try:
    import json
except:
    import simplejson as json

import config
import validators
import auth
import sys

from bottle import request, response, error, run, route, static_file

default_api = config.JafarAPI()
    
@error(404)
def error404(error):
    return json.dumps(['error', 'There is no API call at this URL.'])

@route('/_api_list/')
def l():
    return default_api.nice_api()

import base64
import sys
import os

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

route_to_app('/app/', 'html/')
route_to_app('/genie/', '/Users/graham/DropboxLocal/garden/genie/')
route_to_app('/clients/', 'clients/')
route_to_templates('/template/', 'template/')

def jafar_run(host='127.0.0.1', port=8080, reloader=True, config_d={}):
    import bottle
    bottle.debug(True)
    run(host=host, port=port, reloader=reloader)

data = {'value': 0}

if __name__ == '__main__':
    api = default_api.api
    @api(path='/incr', required=['name'])
    def incr(name):
        "this function does cool shit. you should pass in name"
        data['value'] += 2
        return data['value']

    @api(path='/decr')
    def decr():
        data['value'] -= 1
        return data['value']

    @api(path='/asdf')
    def asdf(name, age):
        return "Hello %s, %s" % (name, age)

    @api(path='/view')
    def view():
        return data['value']

    @api(path='/incr1')
    def incr1():
        c = default_api.build_client()
        old_value = c.view()
        c.incr()
        return old_value

    @api(path='/hello')
    def hello(name):
        "this function will say hello to you"
        return "hello %s" % name

    @api(path='/test/greg')
    def greg():
        return "hi greg"

    if 'serve' in sys.argv:
        jafar_run()
    
    if 'client' in sys.argv:
        from clients.client import JafarClient
        c = JafarClient('127.0.0.1:8080')
        print c.ticket.view(id=1)
