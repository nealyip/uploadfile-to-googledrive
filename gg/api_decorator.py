from .oauth2 import delete_token, creds, update_creds
from .service import build, RefreshError


class APIDecorator:
    @staticmethod
    def update_token(fun):
        def onCall(*args):
            try:
                result = fun(*args)
                update_creds(args[0].service._creds)
                return result
            except RefreshError as e:
                if e.args[0] == 'invalid_grant: Token has been expired or revoked.':
                    print('Token has been expired or revoked.')
                    delete_token()
                    args[0].rebuild()
                    return fun(*args)
                else:
                    raise

        return onCall

    @staticmethod
    def service(name: str, ver: str):
        def proxy(cls):
            class Service:
                def __init__(self, name, ver):
                    self._creds = creds()
                    self._service = build(name, ver, credentials=self._creds)

                def __getattr__(self, item):
                    return getattr(self._service, item)

            class Proxy:
                def __init__(self, *args, **kwargs):
                    self.__wrapped = cls(*args, **kwargs)
                    self.buildService()

                def __getattr__(self, item):
                    return getattr(self.__wrapped, item)

                def __setattr__(self, key, value):
                    """
                    this method is called by outside only.
                    ie.
                    drive = Drive() # here's drive is Proxy's instance
                    drive.a = 1
                    however,
                    called inside class won't trigger this function
                    because there's self is the original instance
                    """
                    if key == '_Proxy__wrapped':
                        self.__dict__[key] = value
                    else:
                        setattr(self.__wrapped, key, value)

                def buildService(self):
                    self.__wrapped.service = Service(name, ver)
                    self.__wrapped.rebuild = self.buildService

            return Proxy

        return proxy
