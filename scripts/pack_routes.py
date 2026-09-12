"""Split gzip route streams into <=20 MiB files; original bytes are unchanged."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'dist' / 'data'

def pack(source):
    manifest = {'version': 1, 'encoding': 'gzip-float32-le', 'categories': {}}
    metadata = json.loads((DATA / 'metadata.json').read_text(encoding='utf-8'))
    for category in metadata['categories']:
        name = category['id']
        output = DATA / 'routes' / name
        output.mkdir(parents=True, exist_ok=True)
        parts, total = [], hashlib.sha256()
        with (source / (name + '.f32.gz')).open('rb') as stream:
            while chunk := stream.read(20 * 1024 * 1024):
                filename = f'part-{len(parts):03d}.bin'
                (output / filename).write_bytes(chunk)
                total.update(chunk)
                parts.append({'url': f'data/routes/{name}/{filename}', 'bytes': len(chunk),
                              'sha256': hashlib.sha256(chunk).hexdigest()})
        manifest['categories'][name] = {
            'parts': parts, 'sha256': total.hexdigest(),
            'uncompressedBytes': metadata['nodes'] * category['count'] * 4}
    (DATA / 'route-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('Packed', len(manifest['categories']), 'route tables without changing their contents.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DATA)
    pack(parser.parse_args().source.resolve())
