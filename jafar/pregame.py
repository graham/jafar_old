try:
    import json
except:
    import simplejson as json

import layer
import validators
import sys

import base64
import sys
import os

from bottle import request, response, error, run, route, static_file
import bottle

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

def init_base(easy_mode=False):
    import jafar
    if jafar.default_api:
        return jafar.default_api
    jafar.default_api = layer.JafarAPI()
    
    @error(404)
    def error404(error):
        return json.dumps(['error', 'There is no API call at this URL.'])

    @jafar.default_api.raw(path='/_api_list/')
    def l(nice=None, *args, **kwargs):
        i = jafar.default_api.nice_api()
        response.content_type = 'text/plain'
        if nice:
            return '\n'.join([str(ii) for ii in i])
        else:
            return json.dumps(i)

    @route('/favicon.ico')
    def favicon():
        return ''
    
    @route('/_api')
    def api_view():
        return 'bye'

    @jafar.default_api.api(path='/_report_error')
    def report_error(message=None, url=None, linenumber=None):
        jafar.report_error(message=message, url=url, linenumber=linenumber)

    ## if easy mode lets make it ... easy.
    if easy_mode:
        for i in ('templates', 'pages', 'static'):
            try:
                os.mkdir(i)
            except:
                pass
        route_to_app('/static/', 'static/')
        route_to_app('/templates/', 'templates/')

    return jafar.default_api
    
def jafar_run(host='127.0.0.1', port=8080, config_d={}):
    import bottle
    run(host=host, port=port, reloader=False)

def jafar_dev(host='127.0.0.1', port=8080, reloader=True, config_d={}):
    import bottle
    run(host=host, port=port, reloader=reloader)

def jafar_paste(host='127.0.0.1', port=8080, reloader=True):
    import bottle
    bottle.run(host=host, port=port, reloader=reloader, server='paste')
