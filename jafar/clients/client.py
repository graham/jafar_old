try:
    import json
except:
    import simplejson as json

import httplib2
import urllib
import functools
import types
from jafar.errors import JafarException

non_json_types = [
    int,
    str,
    unicode,
    float
]

class JafarClient(object):
    def __init__(self, server, version=0, data=None):
        self._host = server
        self._version = version
        self._token = None
        self._server = httplib2.Http()
        self._calls = set()
        self._proxies = set()
        self._data = data or ""
        self._reflect()
    
    def _login(self, uid, password):
        self._token = self.auth.login(uid=uid, password=password)
    
    def _help(self, key, version=None):
        if version == None:
            version = self._version
        new_key = '%i/%s' % (version, key.lstrip('/'))
        if new_key in self._data:
            print self._data[new_key]
        
    def __repr__(self):
        return "<JafarClient available_api_calls=%r proxies=%r>" % (list(self._calls), list(self._proxies))

    def _get(self, method, url, data={}):
        def jsonify_if_needed(value):
            if type(value) in non_json_types:
                return value
            else:
                return json.dumps(value)
        ndata = {}
        for i in data:
            ndata[i] = jsonify_if_needed(data[i])

        if method == 'GET':
            return self._fetch(method, url, gdata=ndata)
        elif method == 'POST':
            return self._fetch(method, url, data=ndata)
        
    def _fetch(self, method, url, gdata={}, data={}):
        #if self._token:
        #    if method == 'GET':
        #        gdata.update({'_auth_token':self._token})
        #    else:
        #        data.update({'_auth_token':self._token})
        
        if gdata:
            url = url + "?" + urllib.urlencode(gdata)

        raw = urllib.urlencode(data)

        resp, content = self._server.request('http://' + self._host + url, method, body=raw, headers={'Host':self._host})

        d = content
        status = int(resp['status'])

        try:
            d = json.loads(d)
        except:
            pass
        return status, d
    
    def _handle(self, result):
        if result[0] == 200:
            return result[1]
        else:
            print '\n' * 2
            print result[1]
            print '\n' * 2
            raise JafarException( 0, str(result) )
    
    def _reflect(self, inner_data=None):
        for i in self._calls:
            delattr(self, i)
        for i in self._proxies:
            delattr(self, i)

        if inner_data:
            code, data = 200, inner_data
        else:
            code, data = self._get('GET', '/_api_list/', {'version':self._version})

        dd = []
        keys = data[0]
        for i in data[1:]:
            kv = {}
            for k, v in zip(keys, i):
                kv[k] = v
            dd.append(kv)

        data = dd

        if code == 200:
            self._data = data
            for values in data:
                method = values['method']
                key = values['fullpath']

                p = key.split('/', 1)[1].strip('/')
                if not p:
                    p = '_'

                url = '/%s/%s' % (self._version, values['path'].lstrip('/'))
                def w(url2, method2):
                    def inner_call(**kwargs):
                        return self._handle(self._get(method2, url2, kwargs))
                    return inner_call

                c = w(url, method)
                c.func_doc = str(values['func_doc']) + "\nRequired Args: " + str(values['required_args']) + "\nOptional Args:" + str(values['optional_args'])

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
    import sys
    if '-gae' in sys.argv:
        x = JafarClient('jitsu.appspot.com')
    else:
        x = JafarClient('localhost:8080')

