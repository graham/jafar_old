import os
import json
import time
import uuid

import jafar

class JafarSessionSimpleFS(object):
    path = '/Users/graham/storage/simple/%s.json'

    def __init__(self, key, data=None):
        self.key = key
        self.data = data or {}
        if data:
            self.dirty = True
        else:
            self.dirty = False

    def __repr__(self):
        return "<%s object %s %s>" % (
            self.__class__.__name__,
            self.key,
            self.__class__.test(self.key)
            )

    def get(self, key):
        return self.data[key]

    def set(self, key, value):
        self.data[key] = value
        self.dirty = True

    def save(self):
        if self.dirty:
            self.save_data()
            self.dirty = False

    def save_data(self):
        f = open(self.path % self.key, 'w')
        f.write(json.dumps(self.data))
        f.close()
        
    def load_data(self):
        if os.path.exists(self.path % self.key):
            f = open(self.path % self.key).read()
            self.data = json.loads(f)
            return True
        else:
            return False

    @classmethod
    def test(cls, key):
        return os.path.exists(cls.path % key)

    @classmethod
    def load(cls, key):
        ses = cls(key)
        ses.load_data()
        return ses

    @classmethod
    def drop(cls, key):
        os.unlink(cls.path % key)

def init_basic_auth(options):
    import jafar
    api = jafar.init_base()

    SESSION_KEY = options.get("SESSION_KEY", False) or "jafar_session_id"
    SESSION_CLASS = options.get("SESSION_CLASS", False) or JafarSessionSimpleFS

    DB_APP_KEY = options.get("DB_APP_KEY")
    DB_APP_SECRET = options.get("DB_APP_SECRET")
    DB_APP_TYPE = options.get("DB_APP_TYPE") or "app_folder"

    ###### this should be generalized in some way ######
    import dropbox
    import dropbox.client, dropbox.rest, dropbox.session
    
    def build_client(key, secret):
        sess = dropbox.session.DropboxSession(DB_APP_KEY, DB_APP_SECRET, DB_APP_TYPE)
        sess.set_token(key, secret)
        return dropbox.client.DropboxClient(sess)

    def request_client():
        sess = dropbox.session.DropboxSession(DB_APP_KEY, DB_APP_SECRET, DB_APP_TYPE)
        request_token = sess.obtain_request_token()
        url = sess.build_authorize_url(request_token, oauth_callback='http://%s/auth/complete' % (jafar.get_host()))
        return url, request_token.key, request_token.secret
    ###### end generalized shit ######

    def default_on_no_auth():
        jafar.redirect('/auth/start')

    def default_validate_session(ses):
        client = build_client(ses.get('auth_key'), ses.get('auth_secret'))
        try:
            ac = client.account_info()
            return True
        except:
            return False

    on_no_auth = options.get('on_no_auth', False) or default_on_no_auth
    validate_session = options.get('validate_session', False) or default_validate_session

    def simple_session(do_auth_on_fail=True):
        if SESSION_CLASS.test(jafar.get_cookie(SESSION_KEY)):
            session = SESSION_CLASS.load(jafar.get_cookie(SESSION_KEY))
            if session.data.get('valid', False):
                return session
            else:
                if do_auth_on_fail:
                    on_no_auth()
                else:
                    return None
        else:
            if do_auth_on_fail:
                on_no_auth()
            else:
                return None
    
    jafar.get_session = simple_session

    ## routes that actually do the auth.

    @api.raw(path='/auth/')
    def auth_pretest(target=None, force=None):
        sid = jafar.get_cookie(SESSION_KEY)
        if not sid or force:
            on_no_auth()

        if SESSION_CLASS.test(sid) is False:
            jafar.set_cookie(SESSION_KEY, '', path='/')
            on_no_auth()

        session = SESSION_CLASS.load(sid)

        if validate_session(session):
            jafar.redirect('/')
        else:
            jafar.set_cookie(SESSION_KEY, '', path='/')
            on_no_auth()

    @api.raw(path='/auth/start')
    def auth_start():
        new_session_key = str(uuid.uuid4())
        url, key, secret = request_client()
        session = SESSION_CLASS(new_session_key, {'session_key':new_session_key,
                                               'auth_key':key,
                                               'auth_secret':secret,
                                               'valid':False})
        session.save()
        jafar.set_cookie(SESSION_KEY, new_session_key, path='/')
        return '''<html><head></head><body>Authorizing...</body><script language="javascript">setTimeout( function() {window.location='%s';}, 200);</script></html>''' % url

    @api.raw(path='/auth/complete')
    def auth_complete(uid=None, oauth_token=None):
        session = SESSION_CLASS.load(jafar.get_cookie(SESSION_KEY))
        print session, session.data, jafar.get_cookie(SESSION_KEY)
        
        assert session.get('auth_key') == oauth_token

        request_token = dropbox.session.OAuthToken(session.get('auth_key'), session.get('auth_secret'))
        db_sess = dropbox.session.DropboxSession(DB_APP_KEY, DB_APP_SECRET, DB_APP_TYPE)
        db_sess.request_token = request_token

        access_token = db_sess.obtain_access_token(request_token)
        client = dropbox.client.DropboxClient(db_sess)
        ac = client.account_info()

        session.set('auth_key', access_token.key)
        session.set('auth_secret', access_token.secret)
        session.set('uid', uid)
        session.set('valid', True)
        session.set('username', ac['email'])
        session.set('fullname', ac['display_name'])
        session.save()

        jafar.redirect('/')

    @api.api(path='/auth/test')
    def auth_test():
        session = jafar.get_session()
        client = build_client(session.get('auth_key'), session.get('auth_secret'))
        try:
            str(client.account_info())
            return True
        except Exception, er:
            return False
