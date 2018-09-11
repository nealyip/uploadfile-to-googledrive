import hashlib
import json
import os
import urllib.request as request
from datetime import datetime, timedelta, timezone
from os import getenv
from urllib.parse import urlencode

from .local_server import serve

PORT = int(getenv('UPLOAD_LOCAL_SERVER_PORT', 9004))


class OAuth2:

    def __init__(self, file, scopes=(), *, mode='loopback_ip', ip='127.0.0.1', port=9004):
        self.client(file)
        self.port = port
        self.mode = mode or 'loopback_ip'
        self.ip = ip
        self.scopes = scopes

    def client(self, file):
        r = json.load(open(file, 'r', encoding='utf-8'))
        installed = r.get('installed')
        self.clientId, self.clientSecret = installed.get('client_id'), installed.get('client_secret')
        assert self.clientId, 'Missing client id'
        assert self.clientSecret, 'Missing client secret'

    @staticmethod
    def stateToken():
        state = hashlib.sha256(os.urandom(1024)).hexdigest()
        return state

    @property
    def redirectUri(self):
        uri = {
            'custom_uri': '',
            'loopback_ip': 'http://%s:%d' % (self.ip, self.port),
            'manual': 'urn:ietf:wg:oauth:2.0:oob',
            'programmatic': 'urn:ietf:wg:oauth:2.0:oob:auto'
        }
        return uri.get(self.mode, uri.get('manual'))

    def authorizationCode(self):
        """
        4 modes
        custom_uri : Android apps, iOS apps, Universal Windows Platform (UWP) apps
        loopback_ip : macOS, Linux, and Windows desktop (but not Universal Windows Platform) apps
        manual : Copy and paste
        programmatic:

        :param mode:
        :param port:
        :return:
        """
        query = {
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'state': OAuth2.stateToken(),
            'redirect_uri': self.redirectUri,
            'client_id': self.clientId
        }
        assert query.get('client_id'), 'Client ID not found'
        base = 'https://accounts.google.com/o/oauth2/v2/auth'
        print('Please goto this url by your favourite browser.')
        print('%s?%s' % (base, urlencode(query)))
        code = ''
        if self.mode == 'manual':
            code = input('Please paste the authorization code here: ')
        elif self.mode == 'loopback_ip':
            state, code = serve(self.port)
        else:
            raise Exception('%s mode is not support' % self.mode)
        return code

    def accessToken(self, *, auth='', refresh=''):
        assert auth != '' or refresh != '', 'Require either auth or refresh token'
        base = 'https://www.googleapis.com/oauth2/v4/token'
        query = {
            'client_id': self.clientId,
            'client_secret': self.clientSecret,
        }
        query.update(
            {
                'code': auth,
                'redirect_uri': self.redirectUri,
                'grant_type': 'authorization_code'
            } if auth != '' else {
                'refresh_token': refresh,
                'grant_type': 'refresh_token'
            })
        req = request.Request(base, method='POST', headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        result = request.urlopen(req, data=urlencode(query).encode('utf-8'))
        token = json.loads(result.read().decode('utf-8'))
        # self.user_info(token)
        return token

    def user_info(self, token):
        # import base64
        # base64.b64decode(token.get('id_token').split('.')[1])
        # can be found on https://accounts.google.com/.well-known/openid-configuration
        url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        req = request.Request(url, method='GET', headers={
            'Authorization': 'Bearer {}'.format(token.get('access_token'))
        })
        result = request.urlopen(req).read()
        return result


class Credentials:
    def __init__(self, result, file, time):
        self._result = result.copy()
        self._result['start_time'] = time
        self._result['client_secret_file'] = file

    def refresh(self):
        expires = self.start_time + timedelta(seconds=self.expires_in)
        expired = datetime.now(tz=self.start_time.tzinfo) > expires
        if expired:
            oauth = OAuth2(self.client_secret_file)
            result = oauth.accessToken(refresh=self.refresh_token)
            self._result.update(result)
            self._result['start_time'] = datetime.now(tz=timezone(timedelta(hours=8)))

    def __getattr__(self, item):
        if item == 'access_token':  # Deny get token by access_token, use token instead.
            raise AttributeError
        elif item[0:2] != '__':
            return self._result.get(item, None)
        raise AttributeError

    @property
    def token(self):  # Follow google apiclient library, use token as key
        self.refresh()
        return self._result['access_token']


class flow:
    @classmethod
    def from_client_secrets_file(cls, client_secrets_file, scopes, **kwargs):
        def run(mode):
            oauth = OAuth2(client_secrets_file, scopes=scopes, mode=mode, port=PORT)
            auth = oauth.authorizationCode()
            return Credentials(oauth.accessToken(auth=auth), client_secrets_file,
                               datetime.now(tz=timezone(timedelta(hours=8))))

        class Flow:
            def run_console(self):
                return run('manual')

            def run_local_server(self):
                return run('loopback_ip')

        return Flow()


if __name__ == '__main__':
    from .oauth2 import home, SCOPES

    oauth = OAuth2(os.path.sep.join((str(home()), r'.google-credentials', r'uploadfile', r'client_secret.json')),
                   scopes=SCOPES, port=9104)
    auth = oauth.authorizationCode()
    x = oauth.accessToken(auth=auth)
    print(x)
