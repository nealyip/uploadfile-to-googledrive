import mimetypes
import os
import sys
import time
import urllib.request as request
from json import loads, dumps
from urllib.error import HTTPError
from urllib.parse import urlencode


class RefreshError(Exception):
    pass


try:
    timer = time.perf_counter  # or process_time
    # timer = time.process_time
except AttributeError:
    timer = time.clock if sys.platform[:3] == 'win' else time.time

FOLDERMIMETYPE = 'application/vnd.google-apps.folder'
CHUNKSIZE = os.getenv('UPLOAD_CHUNKSIZE', 4096)  # kb


def execute(instance):
    url = instance.url
    method = instance.method or 'GET'
    data = {key: instance.data[key] for key in instance.data if not instance.data[key] is None}
    headers = {
        'Authorization': 'Bearer %s' % instance.credentials.token
    }
    if method == 'GET' and len(data.keys()) > 0:
        url = '%s%s%s' % (instance.url, '?' if instance.url.find('?') == -1 else '&', urlencode(data))
        data = ''
    else:
        headers.update({
            'Content-Type': instance.mime or 'x-www-form-urlencoded'
        })
        if instance.mime[:16].lower() == 'application/json':
            data = dumps(data)
        else:
            data = urlencode(data)
    req = request.Request(url, method=method, headers=headers)
    try:
        response = request.urlopen(req, data=data.encode('utf-8'))
        return loads(response.read().decode('utf-8')) if not hasattr(instance, 'returnResponse') else response
    except HTTPError as e:
        if e.code == 401:
            raise RefreshError('invalid_grant: Token has been expired or revoked.')
        raise


def stat(file):
    size = os.stat(file).st_size
    mime = mimetypes.guess_type(file)[0] or 'application/octet-stream'
    return size, mime


def executeUpload(instance):
    data, chunk_size, response, begin = instance.data, CHUNKSIZE * 1024, {}, timer()
    with open(data.file, 'rb') as f:
        start, content = 0, f.read(chunk_size)
        while content != b'':
            l = len(content)
            args = {
                'url': instance.url,
                'method': 'PUT',
                'headers': {
                    'Content-Type': instance.mime,
                    'Content-Length': l,
                    'Content-Range': 'bytes %d-%d/%d' % (start, start + l - 1, instance.size)
                }
            }

            req = request.Request(**args)
            try:
                response = request.urlopen(req, data=content)
                assert response.status == 200 or response.status == 201, 'Server response %d %s' % (
                    response.status, response.read())

                body = loads(response.read().decode())
                response = body
                break
            except HTTPError as e:
                assert e.code == 308, e
                total_received = e.fp.getheader('Range')  # 'bytes=0-262143'
                if total_received[6:] == '0-%d' % (start + l - 1):
                    start += l
                    elapsed = timer() - begin
                    speed = int(start / elapsed / 1024)
                    print('[%-40s] %dkbps' % ('|' * int(start / instance.size * 40), speed), end='\r')
                    content = f.read(chunk_size)

    print(' ' * 55, end='\r')
    return response


def executable(cls):
    def onCall(*args, **kwargs):
        instance = cls(*args, **kwargs)
        instance.execute = lambda: execute(instance)
        return instance

    return onCall


class DriveAPI:
    credentials = None

    @staticmethod
    def files():
        @executable
        class Files:
            def list(self, *args, **kwargs):
                self.url = 'https://www.googleapis.com/drive/v3/files'
                self.method = 'GET'
                self.data = kwargs
                self.credentials = DriveAPI.credentials
                return self

            def create(self, *args, **kwargs):
                self.method = 'POST'
                self.data = kwargs.get('body')
                self.credentials = DriveAPI.credentials
                self.mime = 'application/json; charset=UTF-8'
                if kwargs.get('body', {}).get('mimeType') == FOLDERMIMETYPE:
                    self.url = 'https://www.googleapis.com/drive/v3/files'
                else:
                    self.url = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable'
                    self.returnResponse = True
                    size, mime = stat(kwargs.get('media_body').file)
                    assert size > 0, 'Cannot upload empty file'
                    self.headers = {
                        'X-Upload-Content-Type': mime,
                        'X-Upload-Content-Length': size
                    }
                    response = self.execute()
                    assert response.status == 200, response.read().decode('utf-8')
                    self.url = response.getheader('Location')
                    self.data = kwargs.get('media_body')
                    self.method = 'PUT'
                    self.size, self.mime = size, mime
                    self.execute = lambda: executeUpload(self)
                return self

        return Files()


class MediaFileUpload():
    def __init__(self, file, *, resumable=False):
        self.file = file
        self.resumable = resumable


def build(name, ver, *, credentials):
    if name == 'drive':
        DriveAPI.credentials = credentials
        return DriveAPI

    raise Exception('%s is not supported' % name)
