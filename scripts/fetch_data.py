"""Download public OSM source data and pinned Leaflet assets, once."""
from pathlib import Path
import urllib.request, urllib.parse, json, time

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'raw'; RAW.mkdir(exist_ok=True)
DIST = ROOT / 'dist'; DIST.mkdir(exist_ok=True)
ENDPOINTS = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter', 'https://overpass.private.coffee/api/interpreter']

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'SetagayaAccessResearch/1.0 (local educational map)', 'Accept': '*/*'}), timeout=180).read()

def query(name, q):
    p = RAW / (name + '.json')
    if p.exists():
        try:
            obj=json.loads(p.read_text(encoding='utf-8'))
            if obj.get('elements'): return obj
        except Exception: pass
    for endpoint in ENDPOINTS:
        try:
            data = get(endpoint+'?'+urllib.parse.urlencode({'data': q}))
            obj = json.loads(data)
            if not obj.get('elements'): raise ValueError('Empty data '+str(obj)[:200])
            p.write_bytes(data)
            print(name, len(obj['elements']), 'elements', len(data), 'bytes', flush=True)
            return obj
        except Exception as e: print(endpoint, name, str(e), flush=True)
    raise RuntimeError('All public endpoints failed for '+name)

if __name__ == '__main__':
    b = query('boundary', '[out:json][timeout:90];rel["boundary"="administrative"]["name:en"="Setagaya"](35.5,139.5,35.8,139.8);out geom;')
    bounds=b['elements'][0]['bounds']
    bbox=','.join(str(bounds[k]+off) for k,off in [('minlat',-.012),('minlon',-.014),('maxlat',.012),('maxlon',.014)])
    query('roads', '[out:json][timeout:180];way["highway"~"^(primary|secondary|tertiary|unclassified|residential|living_street|pedestrian|primary_link|secondary_link|tertiary_link)$"]["access"!~"^(private|no)$"]["foot"!="no"]('+bbox+');out body;>;out skel qt;')
    query('pois', '[out:json][timeout:180];(nwr["amenity"~"^(hospital|clinic|doctors|pharmacy|school|kindergarten|college|university|library|community_centre|townhall|post_office)$"]('+bbox+');nwr["shop"~"^(supermarket|convenience|greengrocer|bakery)$"]('+bbox+');nwr["leisure"~"^(park|playground|sports_centre)$"]('+bbox+'););out center tags;')
    # The required basemap is the separately bundled GSI tile layer.
    # Extra OSM context geometry is optional and must not block the site build.
    try:
        query('background', '[out:json][timeout:90];(way["waterway"~"^(river|stream)$"]('+bbox+');way["railway"="rail"]('+bbox+');way["natural"="water"]('+bbox+');way["leisure"="park"]('+bbox+'););out geom;')
    except RuntimeError:
        print('Optional OSM context unavailable; the GSI basemap is used.',flush=True)
    vendor=DIST/'vendor'; vendor.mkdir(exist_ok=True)
    for filename in ['leaflet.js','leaflet.css']:
        p=vendor/filename
        if not p.exists(): p.write_bytes(get('https://unpkg.com/leaflet@1.9.4/dist/'+filename))
    p=vendor/'Leaflet-LICENSE.txt'
    if not p.exists(): p.write_bytes(get('https://unpkg.com/leaflet@1.9.4/LICENSE'))
    print('Public sources and local map library ready.', flush=True)
