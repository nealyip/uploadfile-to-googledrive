# from google.auth.transport.urllib3 import AuthorizedHttp
import pickle
from os import environ, path, remove, makedirs

from .google_oauth2_lib import flow


def home():
    try:
        from pathlib import Path
        return Path.home()
    except (ImportError, AttributeError):
        from os.path import expanduser
        return expanduser("~")


# p = path.dirname(path.abspath(__file__))
p = path.sep.join((str(home()), r'.google-credentials', r'uploadfile'))
pkl = p + path.sep + r'credentials.pkl'

SCOPES = (
    'https://www.googleapis.com/auth/drive.file',  # created by this app's files only
    # 'https://www.googleapis.com/auth/drive' # all files
    'openid'
)


def create_creds_folder():
    if not path.exists(p):
        makedirs(p, 0o700)


def delete_token():
    remove(pkl)


def access_token():
    return creds().token


def update_creds(c):
    pickle.dump(c, open(pkl, 'wb'))


def creds():
    try:
        _creds = pickle.load(open(pkl, 'rb'))
    except Exception as e:
        _flow = flow.from_client_secrets_file(p + path.sep + 'client_secret.json', scopes=SCOPES)

        # print(flow.authorization_url(access_type='offline'))
        if environ.get('UPLOAD_AUTH_USING') == 'manual':
            _creds = _flow.run_console()
        else:
            _creds = _flow.run_local_server()
        update_creds(_creds)

    return _creds


if __name__ == '__main__':
    print(access_token())
