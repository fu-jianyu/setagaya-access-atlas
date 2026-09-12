"""Check chunk integrity, route dimensions, local references and portable startup."""
import gzip
import hashlib
import io
import json
import socket
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'

def main():
    manifest = json.loads((DIST / 'data/route-manifest.json').read_text(encoding='utf-8'))
    records = []
    for category, entry in manifest['categories'].items():
        parts = []
        for part in entry['parts']:
            data = (DIST / part['url']).read_bytes()
            assert len(data) == part['bytes'] <= 20 * 1024 * 1024
            assert hashlib.sha256(data).hexdigest() == part['sha256']
            parts.append(data)
        compressed = b''.join(parts)
        assert hashlib.sha256(compressed).hexdigest() == entry['sha256']
        size = 0
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
            while block := stream.read(1024 * 1024):
                size += len(block)
        assert size == entry['uncompressedBytes']
        records.append({'category': category, 'parts': len(parts), 'uncompressedBytes': size})
    files = [p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.git' not in p.parts]
    assert all(p.stat().st_size <= 25 * 1024 * 1024 for p in files), 'A file exceeds GitHub browser upload size.'
    # The server must resolve dist relative to its script, never to cwd.
    with tempfile.TemporaryDirectory(prefix='atlas unrelated cwd ') as other:
        process = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), '--port', '0', '--no-browser'],
                                   cwd=other, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            line = process.stdout.readline().strip()
            assert line.startswith('Access Atlas ready: '), line
            url = line.removeprefix('Access Atlas ready: ')
            with urllib.request.urlopen(url, timeout=10) as response:
                assert b'Setagaya / Access Atlas' in response.read()
            with urllib.request.urlopen(url + 'route-loader.mjs', timeout=10) as response:
                assert 'javascript' in response.headers['Content-Type']
            with urllib.request.urlopen(url + 'data/route-manifest.json', timeout=10) as response:
                assert json.load(response) == manifest
        finally:
            process.terminate()
            process.communicate(timeout=10)
        # A different app already on the preferred port must never be opened instead.
        with socket.socket() as occupied:
            occupied.bind(('127.0.0.1', 0))
            occupied.listen()
            port = occupied.getsockname()[1]
            process = subprocess.Popen([sys.executable, str(ROOT / 'server.py'), '--port', str(port), '--no-browser'],
                                       cwd=other, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                assert 'unavailable' in process.stdout.readline()
                line = process.stdout.readline().strip()
                url = line.removeprefix('Access Atlas ready: ')
                assert url != f'http://127.0.0.1:{port}/'
                with urllib.request.urlopen(url, timeout=10) as response:
                    assert b'Setagaya / Access Atlas' in response.read()
            finally:
                process.terminate()
                process.communicate(timeout=10)
    report = {'status': 'passed', 'checks': ['All route chunk SHA-256 hashes', 'Combined gzip hashes and dimensions',
        'Every repository file <=25 MiB', 'Server starts from unrelated working directory', 'Module MIME type',
        'HTTP index and manifest', 'Occupied preferred port chooses a different port'], 'routes': records, 'repositoryBytes': sum(p.stat().st_size for p in files)}
    (ROOT / 'audit').mkdir(exist_ok=True)
    (ROOT / 'audit/portable-release.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
