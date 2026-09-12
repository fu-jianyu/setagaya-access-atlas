from pathlib import Path
import urllib.request, json, math, concurrent.futures
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
def fetch(url,p):
    if p.exists(): return
    p.parent.mkdir(exist_ok=True,parents=True)
    data=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SetagayaAccessResearch/1.0'}),timeout=45).read()
    p.write_bytes(data)
for name in ['leaflet.js','leaflet.css']:
    fetch('https://unpkg.com/leaflet@1.9.4/dist/'+name,DIST/'vendor'/name)
fetch('https://unpkg.com/leaflet@1.9.4/LICENSE',DIST/'vendor'/'Leaflet-LICENSE.txt')
def tile(lon,lat,z):
    return int((lon+180)/360*2**z),int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z)
jobs=[]
for z in [12,13]:
    xmin,ymax=tile(139.565,35.579,z);xmax,ymin=tile(139.705,35.695,z)
    for x in range(xmin,xmax+1):
        for y in range(ymin,ymax+1):
            jobs.append((f'https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',DIST/'tiles'/str(z)/str(x)/(str(y)+'.png')))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    for done in ex.map(lambda j:fetch(*j),jobs): pass
print('Local Leaflet and',len(jobs),'GSI background tiles ready',flush=True)
