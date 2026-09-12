"""Run Access Atlas from any working directory using Python's standard library."""
import argparse
import functools
import mimetypes
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
mimetypes.add_type('text/javascript', '.mjs')
mimetypes.add_type('application/octet-stream', '.bin')

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def log_message(self, fmt, *args):
        if len(args) > 1 and str(args[1]) not in ('200', '304'):
            super().log_message(fmt, *args)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765, help='Preferred port; 0 selects any available port.')
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    handler = functools.partial(Handler, directory=str(ROOT / 'dist'))
    if not (ROOT / 'dist' / 'data' / 'route-manifest.json').is_file():
        parser.error('Missing bundled data. Extract the complete repository before starting.')
    if not 0 <= args.port <= 65535:
        parser.error('Port must be between 0 and 65535.')
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    except OSError:
        if args.port == 0:
            raise
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        print(f'Port {args.port} is unavailable; selected a free port.', flush=True)
    with server:
        url = f'http://127.0.0.1:{server.server_port}/'
        print(f'Access Atlas ready: {url}\nKeep this window open. Press Ctrl+C to stop.', flush=True)
        if not args.no_browser:
            threading.Timer(0.4, webbrowser.open, args=(url,)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nAccess Atlas stopped.')

if __name__ == '__main__':
    main()
