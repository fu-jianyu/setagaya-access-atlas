import {loadRouteBuffer} from './route-loader.mjs';
import {kernelOf,evaluate,powerMean} from './model.mjs';
let network,allPois,central,loadedCategory=null,distances,pois,N,used;
const get=async url=>{const r=await fetch(url);if(!r.ok)throw Error(`Could not load ${url} (${r.status})`);return r;};
async function init(){if(network)return;[network,allPois,central]=await Promise.all(['data/network.json','data/pois.json','data/centrality.json'].map(async x=>(await get(x)).json()));N=network.nodes.length;used=[...new Set(network.streets.flatMap(s=>[s.u,s.v]))];}
async function loadCategory(category,id){
 if(loadedCategory===category)return;
 postMessage({type:'progress',id,text:'Opening the bundled '+category+' route table…'});
 distances=null;loadedCategory=null;
 const buffer=await loadRouteBuffer(category,(part,total)=>postMessage({type:'progress',id,text:`Opening ${category} route data · ${part} / ${total} parts…`}));
 const src=new Float32Array(buffer);pois=allPois.filter(p=>p.category===category);const M=pois.length;
 if(src.length!==N*M)throw Error('Route table dimensions do not match the dataset.');
 distances=new Float32Array(src.length);
 // Blocked transpose: contiguous facility rows -> contiguous origin rows.
 for(let i=0;i<N;i+=64)for(let j=0;j<M;j++)for(let k=i;k<Math.min(N,i+64);k++)distances[k*M+j]=src[j*N+k];
 loadedCategory=category;
}
function networkScore(s){
 if(s.networkMetric==='betweenness')return Float64Array.from(central.betweenness);
 const metresPerMinute=s.speed*1000/60;
 const v=Float64Array.from(central.meanMetres,(d,i)=>s.networkMetric==='mean'?d/metresPerMinute:s.networkMetric==='closeness'?metresPerMinute/d:central.harmonicPerMetre[i]*metresPerMinute);
 return Float64Array.from(network.streets,e=>powerMean([v[e.u],v[e.v]],s.p));
}
async function calculate(s,id){
 await init();const started=performance.now();
 if(s.domain==='network'){const values=networkScore(s);postMessage({type:'result',id,values,elapsed:performance.now()-started,excluded:0},[values.buffer]);return;}
 await loadCategory(s.category,id);
 postMessage({type:'progress',id,text:'Recalculating street accessibility from shortest paths…'});
 const M=pois.length,rate=s.speed*1000/60,mass=Float64Array.from(pois,p=>s.supply==='one'?1:p.weight),demand=new Float64Array(M),G=kernelOf(s,true);
 let excluded=0;
 if(s.gamma>0){
  for(let i=0;i<N;i++)if(network.inside[i]){let off=i*M;for(let j=0;j<M;j++)demand[j]+=G(distances[off+j]/rate);}
  for(let j=0;j<M;j++){if(Number.isNaN(demand[j]))throw Error('This demand kernel is undefined at a zero walking cost. Choose a non-singular distance kernel.');if(demand[j]>0&&Number.isFinite(demand[j]))mass[j]/=demand[j]**s.gamma;else{mass[j]=0;excluded++;}}
 }
 const costs=new Float64Array(M),scratch={c:new Float64Array(M),w:new Float64Array(M)},nodeValues=new Float64Array(N);
 for(const i of used){let off=i*M;for(let j=0;j<M;j++)costs[j]=distances[off+j]/rate;nodeValues[i]=evaluate(costs,mass,s,scratch);}
 const values=new Float64Array(network.streets.length);
 for(let e=0;e<network.streets.length;e++){
  const street=network.streets[e];const samples=[nodeValues[street.u],nodeValues[street.v]];
  if(street.m>200){const a=street.u*M,b=street.v*M;for(let j=0;j<M;j++)costs[j]=(Math.min(distances[a+j],distances[b+j])+street.m/2)/rate;samples.push(evaluate(costs,mass,s,scratch));}
  values[e]=powerMean(samples,s.p);
 }
 postMessage({type:'result',id,values,elapsed:performance.now()-started,excluded},[values.buffer]);
}
// Serialize jobs; collapse pending adjustments to the most recent state.
let running=false,pending=null;
self.onmessage=({data})=>{pending=data;if(!running)drain();};
async function drain(){running=true;while(pending){const job=pending;pending=null;try{await calculate(job.state,job.id);}catch(e){postMessage({type:'error',id:job.id,text:e.message});}}running=false;}
