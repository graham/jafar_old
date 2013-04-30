try:
    import json
except:
    import simplejson as json

import httplib
import urllib
import urlparse
import functools
import types

from bottle import request, response, error, run, route, static_file
config = {'debug':2}

from errors import JafarException, JafarRaw

class JafarAPI(object):
    def __init__(self):
        self.f_template_cache = {}
        self.live_version = '0'
        self.api_calls = []
        self.broute = route
        self.defaults = {}

        self.pre_call = []
        self.post_call = []

        self.api = self.build_wrapper(version=None)
        self.raw = self.build_wrapper(raw=True)

    def build_client(self):
        from clients.inline import JafarLocalClient
        return JafarLocalClient(self)

    def nice_api(self):
        try:
            version = request.GET.get('version', None)
        except:
            version = None

        try:
            packages = request.GET.get('packages', None)
        except:
            packages = None

        if packages:
            packages = packages.split(',')
            packages = map(lambda i: i.strip('/').replace('/', '.'), packages)

        d = []
        for j in self.api_calls:
            method, path, data = j

            v = {}
            for i in data['validators']:
                v[i] = (data['validators'][i].func_name, data['validators'][i].func_doc)

            if version == None or data['api_version'] == version:
                package_name = data['path'].strip('/').replace('/', '.')

                hit = 0
                if packages:
                    for i in packages:
                        if package_name.startswith(i):
                            hit = 1
                else:
                    hit = 1

                if hit:
                    d.append( dict(
                            method=method,
                            fullpath=path,
                            path=data['path'],
                            func_name=data['func_name'],
                            func_doc=data['func_doc'],
                            required_args=data['required_args'],
                            optional_args=data['optional_args'],
                            validators=v,
                            api_version=data['api_version'],
                            ))

        newd = []
        keys = d[0].keys()
        keys.sort()

        newd.append(keys)
        for i in d:
            newd.append([i[k] for k in keys])
        
        return newd

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

    def build_wrapper(self, **default_kwargs):
        def wrapped_api(**outkw):
            d = dict(path='/', auth=None, required=[], optional={}, 
                     validate={}, version=None, method='GET', 
                     errors={}, returns=None, explicit_pass_in=False)
            d.update(default_kwargs)
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
        return wrapped_api

    def wrap(self, wrapped_function, path='/', auth=None, required=[], optional={}, 
             validate={}, version=None, method='GET', errors={}, returns=None, 
             explicit_pass_in=False, pre_call=None, post_call=None, raw=None, **outer_kwargs):

        if pre_call == None:
            pre_call = []
        if post_call == None:
            post_call = []

        dropin_pre_call = pre_call
        dropin_post_call = post_call

        def inner(*args, **kwargs):
            missing = {}
            malformed = {}
            docs = []
            session = None

            d = {}
            d.update(optional)
            for i in (request.forms, request.POST, request.GET):
                d.update(i)
            
            body = request.body.read()

            q = {}
            if body:
                try:
                    q = dict(urlparse.parse_qsl(body))
                except:
                    q = dict(body=body)

            d.update(q)

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
                for i in self.pre_call + dropin_pre_call:
                    i(path, a, d, wrapped_function)

                temp_result = wrapped_function(*a, **d)

                if raw is None:
                    result = json.dumps(temp_result)
                else:
                    result = temp_result

                for i in dropin_post_call + self.post_call:
                    i(path, result, wrapped_function)
                return result
            except JafarException, e:
                return json.dumps({'error':e.args[0], 'type':'exception'})
            except JafarRaw, nr:
                return nr.args[0]
            except AssertionError, e:
                return json.dumps({'error':e.message, 'type':'failed-assert'})
        return inner
        
    def page(self, template='', **outkw):
        d = dict(path='/', auth=None, required=[], optional={}, validate={}, version=None, method='GET', errors={}, returns=None, explicit_pass_in=False, raw=True)
        d.update(outkw)
        d.update(self.defaults)
        renderer = d.get('renderer', None)
        base = d.get('base', None)

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
                import jafar

                d = inner(*args, **kwargs)

                if renderer is not None:
                    return renderer(template, d, outkw)
                else:
                    temp = self.get_file(template)
                    if base:
                        outkw['content'] = temp % d
                        outkw.update(jafar.cached_data)
                        base_render = self.get_file(base) % outkw
                        return base_render
                    else:
                        return temp % d

            f = route('/%s' % (d['path'].lstrip('/')), method=d['method'])(wrap_template)
            return f
        return wrapper
