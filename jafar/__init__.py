from gevent import monkey; monkey.patch_all()

from bottle import run
default_api = None

from jafar.pregame import init_base

def start(host='127.0.0.1', port=8080, reloader=True, config_d={}):
    run(host=host, port=port, reloader=reloader)


