import socketserver
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qsl


class Handler(BaseHTTPRequestHandler):
    stop = False
    result = dict

    def do_GET(self):
        q = dict(parse_qsl(self.path[2:]))
        Handler.result = q.get('state', ''), q.get('code', '')

        # body = result.get('code').encode('utf-8')
        body = b''

        self.send_response(200)
        self.send_header("Content-type", 'text/plain')
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

        if Handler.result[0]:
            Handler.stop = True


def serve(port=9004):
    httpd = None
    try:
        httpd = socketserver.TCPServer(("", port), Handler)
        while not Handler.stop:
            httpd.handle_request()
        # r = httpd.serve_forever()
        return Handler.result
    finally:
        if not httpd is None:
            httpd.server_close()


if __name__ == '__main__':
    serve()
