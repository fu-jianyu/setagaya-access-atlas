export const DEFAULT={domain:'poi',networkMetric:null,category:'health',supply:'one',kernel:'exponential',radius:65,beta:.08,shape:1,exponent:1.3,gamma:0,a:1,tau:0,rank:3,lower:0,b:1,threshold:1,p:1,speed:4.8};
const preset=(id,name,family,description,formula,changes)=>({id,name,family,description,formula,params:{...DEFAULT,...changes}});
export const PRESETS=[
 preset('N1','Mean network depth','Network structure','Average shortest walking distance to all other retained junctions. Lower values mean a more central location.','K(c)=c · a=0 · b=1',{domain:'network',networkMetric:'mean',kernel:'identity',a:0}),
 preset('N2','Closeness centrality','Network structure','The reciprocal of mean network depth. Computed at junctions and mapped to street endpoints.','K(c)=c · a=0 · b=−1',{domain:'network',networkMetric:'closeness',kernel:'identity',a:0,b:-1}),
 preset('N3','Harmonic centrality','Network structure','Sum of inverse walking costs to all other retained junctions; self is excluded.','K(c)=1/c · a=1 · b=1',{domain:'network',networkMetric:'harmonic',kernel:'power',exponent:1}),
 preset('N4','Edge betweenness','Network structure','How many shortest junction-to-junction routes pass along a street. Exact, unnormalised, all-pair calculation.','λ=1 · K=1 · q=1',{domain:'network',networkMetric:'betweenness',kernel:'constant'}),
 preset('O1','Cumulative opportunities','Opportunities','Count mapped places inside your walking radius. Every place counts once.','K=1[c≤R] · q=1 · a=1',{kernel:'step',radius:15}),
 preset('O2','Weighted opportunities','Opportunities','Count scenario-weighted opportunities inside your walking radius. Weights are declared assumptions.','K=1[c≤R] · q=w · a=1',{kernel:'step',radius:15,supply:'weighted'}),
 preset('O3','Opportunity coverage','Opportunities','Share of sampled street positions meeting the minimum opportunity requirement.','K=1[c≤R] · b=0 · t=6',{kernel:'step',radius:15,b:0,threshold:6,supply:'weighted'}),
 preset('G1','Exponential gravity','Distance decay','Nearby destinations matter more. The benefit fades as the walk gets longer.','K=exp(−βc) · γ=0 · a=1',{}),
 preset('G2','Gaussian gravity','Distance decay','A smooth walking catchment that falls away increasingly fast beyond its characteristic distance.','K=exp(−βc²) · γ=0 · a=1',{kernel:'gaussian',shape:2,beta:.01}),
 preset('G3','Power-law gravity','Distance decay','Strongly favour nearby places while retaining a longer-distance tail. Zero-cost inverse powers are undefined.','K=c^(−α) · γ=0 · a=1',{kernel:'power',exponent:1.3}),
 preset('G4','Linear gravity','Distance decay','Value decreases evenly with walking time, reaching zero at the radius.','K=max(1−c/R,0) · a=1',{kernel:'linear',radius:20}),
 preset('C1','Nearest destination','Minimum cost','Walking time to the nearest mapped place. Lower values mean easier access.','K(c)=c · τ=1 · r=1 · a=0',{kernel:'identity',a:0,tau:1,rank:1}),
 preset('C2','Nth-nearest destination','Minimum cost','Walking time needed to reach your nth mapped destination, giving you more choice.','K(c)=c · τ=1 · r=3 · q=1',{kernel:'identity',a:0,tau:1,rank:3}),
 preset('C3','Minimum quota cost','Minimum cost','Walking time needed to accumulate the requested scenario-weighted opportunity amount.','K(c)=c · τ=1 · r=6 · q=w',{kernel:'identity',a:0,tau:1,rank:6,supply:'weighted'}),
 preset('D1','2SFCA','Competition','Two-step floating catchment access, using equal junction demand and scenario supply weights.','K=G=1[c≤R] · γ=1',{kernel:'step',radius:15,gamma:1,supply:'weighted'}),
 preset('D2','E2SFCA','Competition','Two-step access with three distance bands. Uses the published 1 / 0.42 / 0.09 weight convention.','K=G: 1 / .42 / .09 · γ=1',{kernel:'bands',radius:30,gamma:1,supply:'weighted'}),
 preset('D3','Continuous competition','Competition','Smooth distance decay at both steps of the facility-to-demand calculation.','K=G=exp(−βc) · γ=1',{gamma:1,supply:'weighted'})
];
export function radiusOf(s){return s.radius>=65?Infinity:s.radius;}
export function kernelOf(s,demand=false){
 const R=radiusOf(s),type=demand&&['identity','constant'].includes(s.kernel)?'exponential':s.kernel;
 const beta=demand&&['identity','constant'].includes(s.kernel)?.08:s.beta;
 return c=>{
  if(!Number.isFinite(c)||c<0)return 0;
  if(c>R)return 0;
  switch(type){
   case 'identity':return c;
   case 'constant':case 'step':return 1;
   case 'exponential':case 'gaussian':return Math.exp(-beta*c**s.shape);
   case 'power':return c===0?NaN:c**(-s.exponent);
   case 'linear':return Math.max(0,1-c/R);
   case 'bands':return c<=R/3?1:c<=2*R/3?.42:.09;
  }
 };
}
export function powerMean(values,p){
 if(values.some(Number.isNaN))return NaN;
 if(p>=5)return Math.max(...values);
 if(p<=-5)return Math.min(...values);
 if(p===0){if(values.includes(0))return values.includes(Infinity)?NaN:0;return Math.exp(values.reduce((a,v)=>a+Math.log(v),0)/values.length);}
 if(p<0&&values.includes(0))return 0;
 return (values.reduce((a,v)=>a+v**p,0)/values.length)**(1/p);
}
// Linear-time weighted selection. The caller's costs and masses remain unchanged.
export function quantile(cost,mass,r,scratch){
 let n=0,total=0;const C=scratch?.c??new Float64Array(cost.length),W=scratch?.w??new Float64Array(cost.length);
 for(let j=0;j<cost.length;j++)if(mass[j]>0&&Number.isFinite(cost[j])){C[n]=cost[j];W[n]=mass[j];total+=mass[j];n++;}
 if(total+1e-11*Math.max(1,total)<r)return Infinity;
 let lo=0,hi=n-1;
 while(lo<=hi){
  const pivot=C[(lo+hi)>>1];let lt=lo,i=lo,gt=hi;
  while(i<=gt){if(C[i]<pivot){[C[i],C[lt]]=[C[lt],C[i]];[W[i],W[lt]]=[W[lt],W[i]];i++;lt++;}else if(C[i]>pivot){[C[i],C[gt]]=[C[gt],C[i]];[W[i],W[gt]]=[W[gt],W[i]];gt--;}else i++;}
  let left=0,equal=0;for(let j=lo;j<lt;j++)left+=W[j];for(let j=lt;j<=gt;j++)equal+=W[j];
  if(r<=left){hi=lt-1;}else if(r<=left+equal+1e-12){return pivot;}else{r-=left+equal;lo=gt+1;}
 }
 return Infinity;
}
export function evaluate(cost,mass,s,scratch){
 const K=kernelOf(s);let W=0,sum=0;
 for(let j=0;j<cost.length;j++){if(mass[j]<=0||!Number.isFinite(cost[j]))continue;W+=mass[j];if(s.tau<1)sum+=mass[j]*K(cost[j]);}
 if(W===0){if(s.tau===1&&s.a===0&&s.kernel==='identity')return Infinity;if(s.a>0&&s.tau===0)return s.b===0?(0>=s.threshold?1:0):s.b<0?NaN:0;return NaN;}
 let mean=0;
 if(s.tau<1){
  if(s.lower>0){const cut=quantile(cost,mass,s.lower*W,scratch);let below=0,removed=0;for(let j=0;j<cost.length;j++)if(cost[j]<cut&&mass[j]>0){below+=mass[j];removed+=mass[j]*K(cost[j]);}sum-=removed+(s.lower*W-below)*K(cut);}
  mean=Math.max(0,sum)/(W*(1-s.lower));
 }
 let atom=0;if(s.tau>0){const q=quantile(cost,mass,s.rank,scratch);atom=Number.isFinite(q)?K(q):Infinity;}
 const mixed=(s.tau<1?(1-s.tau)*mean:0)+(s.tau>0?s.tau*atom:0);
 const z=W**s.a*mixed;if(s.b===0)return z>=s.threshold?1:0;if(s.b<0&&z===0)return NaN;return z**s.b;
}
export function matchPreset(s){
 if(s.domain==='network'){if(s.p!==1)return null;return PRESETS.find(p=>p.params.networkMetric===s.networkMetric);}
 if(s.p!==1||s.lower!==0)return null;
 if(s.kernel==='identity'&&s.tau===1&&s.a===0&&s.b===1&&s.gamma===0&&s.radius>=65){
  return PRESETS.find(p=>p.id===(s.supply==='weighted'?'C3':s.rank===1?'C1':Number.isInteger(s.rank)&&s.rank>1?'C2':''));
 }
 if(s.a!==1||s.tau!==0)return null;
 const g=s.gamma,k=s.kernel;
 if(g===0&&s.b===0&&k==='step')return PRESETS.find(p=>p.id==='O3');
 if(s.b!==1)return null;
 if(g===0){if(k==='step')return PRESETS.find(p=>p.id===(s.supply==='one'?'O1':'O2'));if(k==='linear')return PRESETS.find(p=>p.id==='G4');if(s.radius>=65){if(k==='power')return PRESETS.find(p=>p.id==='G3');if(['exponential','gaussian'].includes(k)&&s.beta>0)return PRESETS.find(p=>p.id===(s.shape===1?'G1':s.shape===2?'G2':''));}}
 if(g===1){if(k==='step')return PRESETS.find(p=>p.id==='D1');if(k==='bands')return PRESETS.find(p=>p.id==='D2');if(['exponential','gaussian','power','linear'].includes(k))return PRESETS.find(p=>p.id==='D3');}
 return null;
}
export function interpretation(s){
 if(s.domain==='network')return {lower:s.networkMetric==='mean',unit:s.networkMetric==='mean'?'minutes':s.networkMetric==='betweenness'?'shortest-path pairs':'centrality score'};
 if(s.b===0)return {lower:s.kernel==='identity',unit:'share of street samples'};
 const cost=s.kernel==='identity';return {lower:cost&&s.b>0,unit:cost&&s.a===0&&s.b===1?'minutes':cost&&s.a===0&&s.b===-1?'per minute':s.gamma===0&&s.a===1&&s.b===1?'effective opportunities':'model score'};
}
