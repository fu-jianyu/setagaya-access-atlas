"""Reproducible real OSM graph, shortest paths and exact centralities.

The walkable street skeleton omits service alleys and paths. Facilities are
connected to the nearest retained graph junction, with explicit access distance.
"""
import sys, json, math, gzip, time, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import numpy as np
import networkx as nx
import igraph as ig
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point, mapping
from shapely.ops import polygonize, unary_union

RAW=ROOT/'raw'; OUT=ROOT/'dist'/'data'; OUT.mkdir(parents=True,exist_ok=True)
def read(n): return json.loads((RAW/(n+'.json')).read_text(encoding='utf-8'))
def save(n,x): (OUT/n).write_text(json.dumps(x,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
def log(*a): print(*a,flush=True)
def xy(lon,lat): return ((lon-139.63)*111320*math.cos(math.radians(35.64)),(lat-35.64)*111320)
def length(a,b): return math.dist(xy(*a),xy(*b))

boundary=next(x for x in read('boundary')['elements'] if x.get('tags',{}).get('admin_level')=='7')
lines=[LineString([(p['lon'],p['lat']) for p in x['geometry']]) for x in boundary['members'] if x.get('role')=='outer' and x.get('geometry')]
poly=unary_union(list(polygonize(unary_union(lines))))
assert poly.area>0.004, 'Invalid ward boundary'
save('boundary.geojson',mapping(poly))
elements=read('roads')['elements']
coords={x['id']:(x['lon'],x['lat']) for x in elements if x['type']=='node'}
g=nx.Graph()
for w in elements:
    if w['type']!='way': continue
    tags=w.get('tags',{})
    for a,b in zip(w['nodes'],w['nodes'][1:]):
        if a==b or a not in coords or b not in coords: continue
        d=length(coords[a],coords[b])
        if d<=0: continue
        g.add_edge(a,b,length=d,highway=tags['highway'],name=tags.get('name:en',tags.get('name','')),osm=w['id'])
component=max(nx.connected_components(g),key=len)
dropped=len(g)-len(component); g=g.subgraph(component).copy()
log('Raw largest component',len(g),g.number_of_edges(),'discarded nodes',dropped)
# Suppress degree-two shape points, preserving their full geometry and length.
anchors={n for n,d in g.degree() if d!=2}
edges=[]; seen=set()
for a in sorted(anchors):
    for b in g[a]:
        if frozenset((a,b)) in seen: continue
        route=[a,b]; seen.add(frozenset((a,b))); prev,cur=a,b
        while cur not in anchors:
            nxt=next(k for k in g[cur] if k!=prev)
            seen.add(frozenset((cur,nxt))); route.append(nxt); prev,cur=cur,nxt
        if cur==a: continue  # closed degree-two lollipop does not change junction distances
        parts=[g[u][v] for u,v in zip(route,route[1:])]
        edges.append({'u':a,'v':cur,'length':sum(x['length'] for x in parts),'coords':[coords[n] for n in route],
                      'name':next((x['name'] for x in parts if x['name']),''),'highway':parts[0]['highway'],'osm':parts[0]['osm']})
nodes=sorted(set(e['u'] for e in edges)|set(e['v'] for e in edges)); index={n:i for i,n in enumerate(nodes)}
loc=np.array([coords[n] for n in nodes]); N=len(nodes)
for e in edges: e['u']=index[e['u']];e['v']=index[e['v']]
log('Simplified graph',N,'junctions',len(edges),'streets')
# Sparse graph uses minimum parallel-link length; igraph retains physical edges.
minimum={}
for e in edges:
    key=tuple(sorted((e['u'],e['v'])));minimum[key]=min(minimum.get(key,math.inf),e['length'])
rr=[];cc=[];ww=[]
for (u,v),w in minimum.items(): rr.extend([u,v]);cc.extend([v,u]);ww.extend([w,w])
matrix=csr_matrix((ww,(rr,cc)),shape=(N,N))
inside=np.array([poly.covers(Point(*c)) for c in loc])
shown=[i for i,e in enumerate(edges) if poly.covers(LineString(e['coords']).interpolate(.5,normalized=True))]
# Each facility is a mapped entity; remove same-name near-duplicate node/polygon records.
categories=[('health','Healthcare'),('education','Education'),('shopping','Daily shopping'),('recreation','Parks & recreation'),('civic','Civic services')]
def category(t):
    a=t.get('amenity');s=t.get('shop');l=t.get('leisure')
    if a in ['hospital','clinic','doctors','pharmacy']: return 'health'
    if a in ['school','kindergarten','college','university']: return 'education'
    if s in ['supermarket','convenience','greengrocer','bakery']: return 'shopping'
    if l in ['park','playground','sports_centre']: return 'recreation'
    if a in ['library','community_centre','townhall','post_office']: return 'civic'
tree=cKDTree([xy(*c) for c in loc]); pois=[]; duplicates=0; far=0
for e in sorted(read('pois')['elements'],key=lambda x: {'relation':0,'way':1,'node':2}[x['type']]):
    t=e.get('tags',{}); cat=category(t)
    if not cat: continue
    c=e.get('center',e)
    if 'lon' not in c: continue
    lon,lat=c['lon'],c['lat']; name=t.get('name:en',t.get('name',''))
    kind=t.get('amenity',t.get('shop',t.get('leisure','')))
    if any(p['category']==cat and p['kind']==kind and p['name']==name and name and length((lon,lat),(p['lon'],p['lat']))<90 for p in pois): duplicates+=1;continue
    dist,idx=tree.query(xy(lon,lat))
    if dist>350: far+=1;continue
    # Weights are explicitly scenario assumptions, never reported capacity.
    weight={'hospital':4,'university':4,'college':2,'school':2,'supermarket':3,'park':2,'sports_centre':2,'library':2,'community_centre':2}.get(kind,1)
    pois.append({'id':e['type']+'/'+str(e['id']),'name':name or kind.replace('_',' ').title(),'kind':kind,'category':cat,'lon':lon,'lat':lat,'node':int(idx),'connector':round(float(dist),2),'weight':weight,'inside':bool(poly.covers(Point(lon,lat)))})
log('Facilities',len(pois),'duplicates excluded',duplicates,'connectors >350 m excluded',far)
streetdata=[]
for eid in shown:
    e=edges[eid]
    streetdata.append({'id':eid,'u':e['u'],'v':e['v'],'m':round(e['length'],2),'name':e['name'] or e['highway'].replace('_',' ').title(),'kind':e['highway'],'osm':e['osm'],'c':[[round(c[1],6),round(c[0],6)] for c in e['coords']]})
save('network.json',{'nodes':[[round(c[1],6),round(c[0],6)] for c in loc],'inside':inside.astype(int).tolist(),'streets':streetdata})
save('pois.json',pois)
# Unit demand at each inside-ward junction: a spatial-opportunity competition scenario.
# This is not a population dataset. Sum of demand equals number of ward junctions.
for key,title in categories:
    chosen=[p for p in pois if p['category']==key]
    out=OUT/(key+'.f32.gz')
    log('Shortest paths:',key,len(chosen),'destinations')
    with gzip.open(out,'wb',compresslevel=5) as f:
        for start in range(0,len(chosen),96):
            block=chosen[start:start+96]
            distances=dijkstra(matrix,directed=False,indices=[p['node'] for p in block])
            distances+=np.array([p['connector'] for p in block])[:,None]
            distances.astype('<f4').tofile if False else None
            f.write(distances.astype('<f4').tobytes())
    log(key,'distance table MB',round(out.stat().st_size/1e6,1))
# Graph centrality based on retained junctions, excluding self. Weighted by metres.
centralfile=OUT/'centrality.json'
if not centralfile.exists():
    sums=np.zeros(N);harmonic=np.zeros(N)
    for start in range(0,N,192):
        inds=np.arange(start,min(start+192,N));ds=dijkstra(matrix,directed=False,indices=inds)
        sums[inds]=ds.sum(axis=1)
        with np.errstate(divide='ignore'): inv=np.where(ds>0,1/ds,0)
        harmonic[inds]=inv.sum(axis=1)
        if start%1920==0: log('Centrality distance rows',start,'/',N)
    log('Exact edge betweenness: all retained junction pairs')
    gi=ig.Graph(n=N,edges=[(e['u'],e['v']) for e in edges],directed=False)
    bet=gi.edge_betweenness(weights=[e['length'] for e in edges],directed=False)
    save('centrality.json',{'meanMetres':(sums/(N-1)).tolist(),'harmonicPerMetre':harmonic.tolist(),'betweenness':[bet[i] for i in shown]})
    log('Exact centralities saved')
# Offline context map uses real water, rail and park geometry; online GSI optional.
if (RAW/'background.json').exists():
    fs=[]
    for e in read('background')['elements']:
        c=[[p['lon'],p['lat']] for p in e.get('geometry',[]) if 'lon' in p]
        if len(c)<2: continue
        t=e.get('tags',{}); kind='water' if 'waterway' in t or t.get('natural')=='water' else 'rail' if 'railway' in t else 'park'
        polygon=c[0]==c[-1] and len(c)>=4 and kind!='rail'
        fs.append({'type':'Feature','properties':{'kind':kind},'geometry':{'type':'Polygon' if polygon else 'LineString','coordinates':[c] if polygon else c}})
    save('background.geojson',{'type':'FeatureCollection','features':fs})
else: save('background.geojson',{'type':'FeatureCollection','features':[]})
meta={'source':'OpenStreetMap contributors','license':'ODbL 1.0','osmTimestamp':read('roads').get('osm3s',{}).get('timestamp_osm_base'),'boundaryRelation':boundary['id'],'bbox':boundary['bounds'],'nodes':N,'wardNodes':int(inside.sum()),'streets':len(shown),'routingEdges':len(edges),'poiCount':len(pois),'categories':[{'id':k,'name':t,'count':sum(p['category']==k for p in pois),'insideCount':sum(p['category']==k and p['inside'] for p in pois)} for k,t in categories],'discardedDisconnectedNodes':dropped,'deduplicatedPois':duplicates,'excludedFarPois':far,'distanceUnit':'metres, float32','walkingDefaultKmh':4.8,'demand':'one unit per retained inside-ward junction; illustrative, not population','supply':'one facility or declared type-based scenario weights; not observed capacity','routing':'undirected retained public street skeleton; buffered bounding box, no service alleys, footpaths, signal waits or slope','streetSampling':'two endpoints, equal weight; midpoint additionally when length exceeds 200 m','networkCentrality':'exact all-pair centralities on retained buffered junction graph, not space-syntax integration','poiConnector':'nearest retained junction; straight connector <=350 m; not an entrance-level route'}
save('metadata.json',meta)
log('COMPLETE',json.dumps(meta))
