#!/usr/bin/env python

import sys
import shutil
import urllib
import os

commands = [
    ['init', 'create a new simple project'],
    ['install', 'install this file in /usr/local/bin/'],
]

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        rest = sys.argv[2:]
        handle(command, rest)
    else:
        handle(None, None)

def handle(command, rest):
    if command is None:
        print 'commands'
        for key, value in commands:
            print key.rjust(10), ' - ', value
    elif command == 'install':
        path = '/usr/local/bin/jafar_helper.py'
        shutil.copyfile('jafar_helper.py', path)
        print 'installed in %s' % path
        print 'setting permissions.'
        shutil.copymode('jafar_helper.py', path)
    elif command == 'init':
        for i in ('templates', 'pages', 'static'):
            print 'creating', i
            os.mkdir(i)
                
        f = open('serve.py', 'w')
        f.write('''
import jafar
import jafar.session
import time

api = jafar.init_base()
jafar.set('version', int(time.time()))

@api.raw(path='/')
def index():
        return open('pages/index.html').read()

@api.api(path='/hello')
def hello():
        return "hello world."

jafar.route_to_app('/static/', 'static/')
jafar.route_to_app('/templates/', 'templates/')

def all_done_callback():
    print 'all done'

jafar.pregame.jafar_paste(host='0.0.0.0', cb=all_done_callback)
''')
        f.close()
        print 'wrote out initial simple config to "serve.py"'

        shutil.copyfile('/Users/graham/grambox/Dropbox/garden/jafar/jafar/clients/jafar.js', 'static/jafar.js')
        urllib.urlretrieve('http://code.jquery.com/jquery-1.9.1.min.js', 'static/jquery.js')
        urllib.urlretrieve('http://dl.dropbox.com/u/28233387/glib.js', 'static/glib.js')

        f = open('static/page.js', 'w')
        f.write('''/* Starting Doc, have fun! */
var jafar_client = null;
$(document).ready( function() {
    console.log("loaded.");
    _GLIB.build_jafar_client(function(client) { 
        jafar_client = client; 
        $('#api_info').html( "" + jafar_client );
    });
});
''')
        f.close()

        f = open('pages/index.html', 'w')
        f.write('''
<html>
  <head>
    <script src="/static/glib.js" type="text/javascript"></script>
    <script src="/static/jquery.js" type="text/javascript"></script>
    <script src="/static/page.js" type="text/javascript"></script>
    <link href="/static/page.css" media="all" rel="stylesheet" type="text/css" />
  </head>

  <body>
        Hello World
        <div id="api_info"></div>
  </body>
</html>
''')
        f.close()

        f = open('static/page.css', 'w')
        f.write("body { font-family: fixed; }")
        f.close()

if __name__ == '__main__':
    main()
