try:
    import json
except:
    import simplejson as json

import httplib
import urllib
import functools
import types

from bottle import request, response, error, run, route, static_file
config = {'debug':2}

from auth import JafarSessionFile, JafarUserFile
from errors import JafarException, JafarRaw

class JafarAPI(object):
    def __init__(self):
        self.f_template_cache = {}
        self.live_version = '0'
        self.user_class = JafarUserFile
        self.session_class = JafarSessionFile
        self.api_calls = []
        self.broute = route

        self.pre_call = []
        self.post_call = []

    def build_client(self):
        from clients.inline import JafarLocalClient
        return JafarLocalClient(self)

    def nice_api(self):
        try:
            version = request.GET.get('version', None)
        except:
            version = None

        d = []
        for j in self.api_calls:
            method, path, data = j

            v = {}
            for i in data['validators']:
                v[i] = (data['validators'][i].func_name, data['validators'][i].func_doc)

            if version != None:
                if data['api_version'] == version:
                    d.append( (method, path, {
                        'path':data['path'],
                        'func_name':data['func_name'],
                        'func_doc':data['func_doc'],
                        'required_args':data['required_args'],
                        'optional_args':data['optional_args'],
                        'validators':v,
                        'api_version':data['api_version'],
                        'method':method
                    }) )
            else:
                d.append( (method, path, {
                    'path':data['path'],
                    'func_name':data['func_name'],
                    'func_doc':data['func_doc'],
                    'required_args':data['required_args'],
                    'optional_args':data['optional_args'],
                    'validators':v,
                    'api_version':data['api_version'],
                    'method':method
                }) )

        return json.dumps(d)

    def get_file(self, fname):
        if fname in self.f_template_cache:
            self.f_template_cache[fname] = open(fname).read()
        else:
            self.f_template_cache[fname] = open(fname).read()

        return self.f_template_cache[fname]

    def error400(self, docs=[], missing={}, malformed={}, func_doc=''):
        response.status = 400
        response.content_type = 'text/plain'

        if config['debug'] == 2 or 'debug_loud' in request.GET:
            d = [ json.dumps([]) ]
            d.append('')
            d.append('/* debug splitter */')

            d.append('/* Function Documentation: %s */' % func_doc)

            for i in missing:
                d.append('// %r is required for this API call.' % i)
                d.append('')
            if malformed:
                d.append('')
                d.append('// Malformed:')

                for key, string in docs:
                    d.append('//   %s: %s' % (key, ', '.join(string)))

        elif 'debug' in request.POST:
            d = [json.dumps( {'missing':missing, 'malformed':malformed, 'docs':docs} )]
        else:
            d = [json.dumps( {'missing':missing, 'malformed':malformed} )]
        return '\n'.join(d)

    def api(self, **outkw):
        d = dict(path='/', auth=None, required=[], optional={}, validate={}, version=None, method='GET', errors={}, returns=None, explicit_pass_in=False)
        d.update(outkw)
        if d['version'] == None:
            d['version'] = self.live_version
            
        def wrapper(wrapped_function):
            self.api_calls.append( (d['method'], '%s%s' % (d['version'], d['path']),
                {
                'path':d['path'], 
                'func_name':wrapped_function.func_name,
                'func_doc':wrapped_function.func_doc,
                'func':wrapped_function,
                'required_args':d['required'],
                'optional_args':d['optional'],
                'validators':d['validate'],
                'api_version':d['version'],
                'errors':d['errors'],
                'returns':d['returns']
                }) )

            inner = self.wrap(wrapped_function, **d)
            f = route('/%s/%s' % (d['version'], d['path'].lstrip('/')), method=d['method'])(inner)

            if d['version'] == self.live_version:
                route(d['path'], method=d['method'])(inner)
            return f
        return wrapper

    def wrap(self, wrapped_function, path='/', auth=None, required=[], optional={}, validate={}, version=None, method='GET', errors={}, returns=None, explicit_pass_in=False):
        def inner(*args, **kwargs):
            missing = {}
            malformed = {}
            docs = []
            session = None

            d = {}
            d.update(optional)
            d.update(request.POST)
            d.update(request.GET)

            for i in required:
                if i not in d:
                    missing[i] = ( i, i )

            for key in validate:
                value = validate[key]

                try:
                    d[key] = value(d[key])
                except JafarException, e:
                    malformed[key] = value.func_name
                    docs.append( (key, e.args) )

            if missing or malformed:
                return self.error400(docs=docs, missing=missing, malformed=malformed, func_doc=wrapped_function.func_doc)

            if '__args__' in d:
                a = d.popitem('__args__')
            else:
                a = []

            if explicit_pass_in:
                d['_api_object'] = self

            #return wrapped_function(instance, user=None, **d)
            try:
                for i in self.pre_call:
                    i(a, d, wrapped_function)
                result = json.dumps(wrapped_function(*a, **d))
                for i in self.post_call:
                    i(result, wrapped_function)
                return result
            except JafarException, e:
                return json.dumps({'error':e.args})
            except JafarRaw, nr:
                return nr.args[0]
        return inner
        
    def page(self, template, dump=None, **outkw):
        if dump == None:
            dump = 'templates/dump.html'
        d = dict(path='/', auth=None, required=[], optional={}, validate={}, version=None, method='GET', errors={}, returns=None, explicit_pass_in=False)
        d.update(outkw)
        if d['version'] == None:
            d['version'] = self.live_version

        def wrapper(wrapped_function):
            self.api_calls.append( (d['method'], '%s%s' % (d['version'], d['path']),
                {
                'path':d['path'], 
                'func_name':wrapped_function.func_name,
                'func_doc':wrapped_function.func_doc,
                'func':wrapped_function,
                'required_args':d['required'],
                'optional_args':d['optional'],
                'validators':d['validate'],
                'api_version':d['version'],
                'errors':d['errors'],
                'returns':d['returns']
                }) )

            inner = self.wrap(wrapped_function, **d)

            def wrap_template(*args, **kwargs):
                d = inner(*args, **kwargs)
                t = self.get_file(template)
                try:
                    tt = (self.get_file(dump) % json.dumps(d))
                except:
                    tt = ''
                return t + tt

            f = route('/%s' % (d['path'].lstrip('/')), method=d['method'])(wrap_template)
            return f
        return wrapper
