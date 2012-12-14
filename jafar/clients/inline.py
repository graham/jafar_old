try:
    import json
except:
    import simplejson as json

import httplib
import urllib
import functools
import types

class JafarLocalClient(object):
    def __init__(self, api_obj):
        self._calls = set()
        self._proxies = set()
        self._data = ''
        self._api_obj = api_obj
        self._reflect()
        self._version = '0'
    
    def _help(self, key, version=None):
        if version == None:
            version = self._version
        new_key = '%i/%s' % (version, key.lstrip('/'))
        if new_key in self._data:
            print self._data[new_key]
        
    def __repr__(self):
        return "<JafarClient available_api_calls=%r proxies=%r>" % (list(self._calls), list(self._proxies))

    def _get(self, url, data={}):
        for method, path, details in self._api_obj.api_calls:
            path = '/' + path.strip()
            url = url.strip()
            if path == url:
                return details['func'](**data)
        return None

    def _reflect(self, inner_data=None):
        for i in self._calls:
            delattr(self, i)
        for i in self._proxies:
            delattr(self, i)

        if inner_data:
            code, data = 200, inner_data
        else:
            code, data = 200, self._api_obj.nice_api()

        if code == 200:
            self._data = data
            for method, key, value in data:
                p = key.split('/', 1)[1].strip('/')
                if not p:
                    p = '_'

                url = '/%s/%s' % ('0', value['path'].lstrip('/'))
                def w(url2=url):
                    def inner_call(**kwargs):
                        return self._get(url2, kwargs)
                    return inner_call

                c = w()
                c.func_doc = str(value['func_doc']) + "\nRequired Args: " + str(value['required_args']) + "\nOptional Args:" + str(value['optional_args'])

                l = p.split('/')
                c.func_name = str(l[-1])
                
                parent = self
                cur = self
                for i in l[:-1]:
                    test = getattr(cur, i, None)
                    if test == None:
                        np = JafarProxy(self)
                        test = np
                        cur._proxies.add(i)
                        setattr(cur, i, np)
                    parent = cur
                    cur = test

                if type(cur) == types.FunctionType:
                    name = cur.func_name
                    np = JafarProxy(self)
                    np._api_call = cur
                    cur = np
                    setattr(parent, name, np)
                    parent._calls.add(name)
                    
                setattr(cur, l[-1], c)
                cur._calls.add(l[-1])

                
class JafarProxy(object):
    def __init__(self, client):
        self.client = client
        self._api_call = None
        self._calls = set()
        self._proxies = set()
        
    def __repr__(self):
        if self._api_call:
            return "<JafarProxy call=%s available_api_calls=%r proxies=%r>" % (str(self._api_call.func_name), list(self._calls), list(self._proxies))
        else:
            return "<JafarProxy available_api_calls=%r proxies=%r>" % (list(self._calls), list(self._proxies))
            
    def _get(*args, **kwargs):
        return self.client._get(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        return self._api_call(*args, **kwargs)

if __name__ == '__main__':
    x = JafarLocalClient()

