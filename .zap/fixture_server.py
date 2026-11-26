"""Owned HTTP fixture for proving the passive gate; never deployed as Juice Shop."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'<!doctype html><html><head><title>Gate fixture</title></head><body>Owned fixture</body></html>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        if '--safe-headers' in sys.argv:
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.end_headers()
        self.wfile.write(body)


HTTPServer(('0.0.0.0', 3000), Handler).serve_forever()
