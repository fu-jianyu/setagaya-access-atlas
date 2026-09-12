from pathlib import Path
from html.parser import HTMLParser
import json,ast,hashlib
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ['src','href'] and v and not v.startswith(('data:','http:','https:','#')):self.links.append(v)
pages=[]
for filename in ['index.html','guide.html']:
    p=Links();p.feed((DIST/filename).read_text(encoding='utf-8'))
    for v in p.links:assert (DIST/v).exists(),v
    pages.append({'page':filename,'localReferences':len(p.links)})
for name in ['server.py','launch.py']:ast.parse((ROOT/name).read_text(encoding='utf-8'))
meta=json.loads((DIST/'data/metadata.json').read_text());assert meta['poiCount']==sum(x['count'] for x in meta['categories'])
assert len(list((DIST/'tiles').rglob('*.png')))==29
files={str(p.relative_to(DIST)):p.stat().st_size for p in DIST.rglob('*') if p.is_file()}
manifest={'status':'passed','pages':pages,'files':len(files),'publicBytes':sum(files.values()),'metadata':meta,'sourceHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [DIST/'model.mjs',DIST/'worker.js',DIST/'main.mjs',ROOT/'scripts/precompute_presets.py']}}
(ROOT/'audit/site-check.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(json.dumps({'status':'passed','pages':pages,'files':len(files),'publicMB':round(sum(files.values())/1e6,1)}))
