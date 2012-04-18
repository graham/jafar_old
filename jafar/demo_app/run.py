try:
    import json
except:
    import simplejson as json

import jafar
import jafar.config
import jafar.validators
import jafar.auth
import sys
import base64
import sys
import os

from jafar.pregame import init_base, route_to_app, route_to_templates

default_api = init_base()

route_to_app('/a/', 'demo_app/html/')
route_to_app('/css/', 'demo_app/css/')
route_to_app('/img/', 'demo_app/img/')
route_to_app('/genie/', '/Users/graham/DropboxLocal/garden/genie/')
route_to_app('/clients/', 'clients/')
route_to_templates('/templates/', 'demo_app/templates/')

def jafar_run(host='127.0.0.1', port=8080, reloader=True, config_d={}):
    import bottle
    bottle.debug(True)
    try:
        while True:
            jafar.run(host=host, port=port, reloader=reloader)
    except KeyboardInterrupt, ki:
        return
        
data = {'value': 0}
api1 = default_api.build_wrapper(version=1)
api2 = default_api.build_wrapper(version=2)

if __name__ == '__main__':
    api = default_api.api
    @api2(path='/hello')
    def hello():
        return 'hello'
    
    @api(path='/contacts/')
    def contacts():
        return 'hi from contacts'
    @api(path='/events/')
    def events():
        return 'hi from events'
    @api(path='/events/create/')
    def event_create():
        return 'you just created an event'

    if 'serve' in sys.argv:
        from jafar.daemon import Daemon
        class JafarDaemon(Daemon):
            def run(self):
                jafar_run()
        x = JafarDaemon('jafar_root', proctitle='jafar_demo_app')
        x.start()
    
    if 'client' in sys.argv:
        from clients.client import JafarClient
        c = JafarClient('127.0.0.1:8080')
        print c.ticket.view(id=1)
