"""Independent vectorized definitions for the 17 built-in indicator presets."""
from pathlib import Path
import sys,json,gzip
ROOT=Path(__file__).resolve().parents[1]
import numpy as np
OUT=ROOT/'dist'/'data'
read=lambda n:json.loads((OUT/n).read_text(encoding='utf-8'))
net=read('network.json');pois=read('pois.json');meta=read('metadata.json');central=read('centrality.json');N=len(net['nodes'])
streets=net['streets'];used=sorted({e[k] for e in streets for k in ['u','v']});row={n:i for i,n in enumerate(used)};long=[e for e in streets if e['m']>200];mid={e['id']:len(used)+i for i,e in enumerate(long)}
def aggregate(arr):
    return [float(np.mean([arr[row[e['u']]],arr[row[e['v']]]] + ([arr[mid[e['id']]]] if e['id'] in mid else []))) for e in streets]
def dump(name,obj): (OUT/name).write_text(json.dumps(obj,separators=(',',':'),allow_nan=False),encoding='utf-8')
netresults={}
for key,vals in [('N1',np.array(central['meanMetres'])/80),('N2',80/np.array(central['meanMetres'])),('N3',np.array(central['harmonicPerMetre'])*80)]:netresults[key]=[float((vals[e['u']]+vals[e['v']])/2) for e in streets]
netresults['N4']=central['betweenness'];dump('network-presets.json',netresults)
defaults={}
for cat in [x['id'] for x in meta['categories']]:
    pp=[p for p in pois if p['category']==cat];M=len(pp);q=np.array([p['weight'] for p in pp],dtype=float)
    print('Precomputing independent definitions:',cat,flush=True)
    d=np.frombuffer(gzip.decompress((OUT/(cat+'.f32.gz')).read_bytes()),dtype='<f4').reshape(M,N)
    costs=np.empty((len(used)+len(long),M),dtype=np.float64);costs[:len(used)]=d[:,used].T.astype(float)/80
    for i,e in enumerate(long):costs[len(used)+i]=(np.minimum(d[:,e['u']],d[:,e['v']]).astype(float)+e['m']/2)/80
    c=costs;res={};res['O1']=aggregate(np.sum(c<=15,axis=1));res['O2']=aggregate((c<=15)@q);res['O3']=aggregate(((c<=15)@q>=6).astype(float))
    res['G1']=aggregate(np.exp(-.08*c).sum(axis=1));res['G2']=aggregate(np.exp(-.01*c*c).sum(axis=1))
    with np.errstate(divide='ignore'): power=c**-1.3
    res['G3']=aggregate(power.sum(axis=1));res['G4']=aggregate(np.maximum(0,1-c/20).sum(axis=1))
    res['C1']=aggregate(c.min(axis=1));res['C2']=aggregate(np.partition(c,2,axis=1)[:,2])
    ix=np.argpartition(c,5,axis=1)[:,:6];local=np.take_along_axis(c,ix,axis=1);sort=np.argsort(local,axis=1);ix=np.take_along_axis(ix,sort,axis=1);v=np.take_along_axis(c,ix,axis=1);cum=np.cumsum(q[ix],axis=1);res['C3']=aggregate(v[np.arange(len(v)),np.argmax(cum>=6,axis=1)])
    dc=d[:,np.array(net['inside'],dtype=bool)].astype(float)/80
    for key in ['D1','D2','D3']:
        if key=='D1':G=dc<=15;K=c<=15
        elif key=='D2':G=np.where(dc<=10,1,np.where(dc<=20,.42,np.where(dc<=30,.09,0)));K=np.where(c<=10,1,np.where(c<=20,.42,np.where(c<=30,.09,0)))
        else:G=np.exp(-.08*dc);K=np.exp(-.08*c)
        demand=G.sum(axis=1);mass=np.divide(q,demand,out=np.zeros_like(q),where=demand>0);res[key]=aggregate(K@mass)
    # Null explicitly represents a zero-cost inverse-power singularity.
    res={k:[round(v,9) if np.isfinite(v) else None for v in vv] for k,vv in res.items()}
    dump(cat+'-presets.json',res);defaults[cat]=res['G1'];print(cat,'13 built-in surfaces saved',flush=True)
    del d,costs,c,dc,G,K,power
dump('defaults.json',defaults)
print('All 69 distinct default surfaces are embedded (65 POI + 4 network).',flush=True)
