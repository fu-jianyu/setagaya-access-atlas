// All stops run from low numerical values to high numerical values.
export const PALETTES = [
  {id:'blue-red',name:'Blue → Red',kind:'Diverging',colors:['#2166ac','#67a9cf','#d1e5f0','#fddbc7','#ef8a62','#b2182b']},
  {id:'teal-rose',name:'Teal → Rose',kind:'Diverging',colors:['#006d77','#68b8bc','#edf5ef','#f4b8bd','#ad254a']},
  {id:'purple-orange',name:'Purple → Orange',kind:'Diverging',colors:['#542788','#998ec3','#f7f7f7','#f1a340','#b35806']},
  {id:'brown-green',name:'Earth → Forest',kind:'Diverging',colors:['#8c510a','#d8b365','#f5f5f5','#5ab4ac','#01665e']},
  {id:'viridis',name:'Viridis',kind:'Sequential',colors:['#440154','#414487','#2a788e','#22a884','#7ad151','#fde725']},
  {id:'cividis',name:'Cividis',kind:'Sequential',colors:['#00224e','#434e6c','#7d7c78','#bcae6c','#fee838']},
  {id:'magma',name:'Magma',kind:'Sequential',colors:['#000004','#3b0f70','#8c2981','#de4968','#fe9f6d','#fcfdbf']},
  {id:'inferno',name:'Inferno',kind:'Sequential',colors:['#000004','#420a68','#932667','#dd513a','#fca50a','#fcffa4']},
  {id:'ocean',name:'Ocean blues',kind:'Sequential',colors:['#deebf7','#9ecae1','#4292c6','#2171b5','#084594']},
  {id:'forest',name:'Forest greens',kind:'Sequential',colors:['#e5f5e0','#a1d99b','#41ab5d','#238b45','#005a32']},
  {id:'turbo',name:'Turbo',kind:'Multihue',colors:['#30123b','#466be3','#28bbec','#32f298','#a4fc3c','#eecf3a','#fb7e21','#d02f05','#7a0403']},
  {id:'spectral',name:'Spectral',kind:'Multihue',colors:['#5e4fa2','#3288bd','#66c2a5','#e6f598','#ffffbf','#fee08b','#f46d43','#d53e4f','#9e0142']}
];
export const DEFAULT_APPEARANCE={palette:'blue-red',reversed:false,custom:['#2166ac','#f7f7f7','#b2182b']};
export const STORAGE_KEY='access-atlas-appearance-v1';
export const validHex=value=>typeof value==='string'&&/^#[0-9a-f]{6}$/i.test(value);
export function normalizeAppearance(input){return {palette:input?.palette==='custom'||PALETTES.some(p=>p.id===input?.palette)?input.palette:DEFAULT_APPEARANCE.palette,reversed:input?.reversed===true,custom:Array.isArray(input?.custom)&&input.custom.length===3&&input.custom.every(validHex)?input.custom.map(c=>c.toLowerCase()):[...DEFAULT_APPEARANCE.custom]};}
export function paletteStops(appearance){const a=normalizeAppearance(appearance),stops=a.palette==='custom'?a.custom:PALETTES.find(p=>p.id===a.palette).colors;return a.reversed?[...stops].reverse():[...stops];}
export const gradient=stops=>`linear-gradient(90deg,${stops.join(',')})`;
export function createColorScale(stops){const rgb=stops.map(hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)));return value=>{if(!Number.isFinite(value))return '#b8c5c9';const t=Math.max(0,Math.min(1,value))*(rgb.length-1),i=Math.min(rgb.length-2,Math.floor(t)),f=t-i;return `rgb(${rgb[i].map((v,k)=>Math.round(v*(1-f)+rgb[i+1][k]*f)).join(',')})`;};}
export function mountPalettePicker({onChange}){
  const $=id=>document.getElementById(id);let appearance;try{appearance=normalizeAppearance(JSON.parse(localStorage.getItem(STORAGE_KEY)));}catch{appearance=normalizeAppearance(null);}
  let frame=0,opener=null;
  const name=()=>appearance.palette==='custom'?'Custom palette':PALETTES.find(p=>p.id===appearance.palette).name;
  function sync(){const stops=paletteStops(appearance);document.documentElement.style.setProperty('--access-gradient',gradient(stops));$('palette-name').textContent=name()+(appearance.reversed?' · Reversed':'');$('palette-preview').style.background=gradient(stops);$('reverse-palette').checked=appearance.reversed;$('custom-colors').hidden=appearance.palette!=='custom';$('use-custom').setAttribute('aria-pressed',String(appearance.palette==='custom'));
    document.querySelectorAll('[data-palette]').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.palette===appearance.palette));});
    ['low','middle','high'].forEach((key,i)=>{const color=$('color-'+key),hex=$('hex-'+key);color.value=appearance.custom[i];hex.value=appearance.custom[i].toUpperCase();hex.setCustomValidity('');});
    $('palette-range-low').style.background=stops[0];$('palette-range-high').style.background=stops.at(-1);
  }
  function apply(patch){appearance=normalizeAppearance({...appearance,...patch});sync();try{localStorage.setItem(STORAGE_KEY,JSON.stringify(appearance));$('palette-save-note').textContent='Saved in this browser. Colors do not change the values.';}catch{$('palette-save-note').textContent='Colors apply now. Browser storage is unavailable.';}cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>onChange(paletteStops(appearance),{...appearance}));}
  for(const p of PALETTES){const button=document.createElement('button');button.type='button';button.className='palette-option';button.dataset.palette=p.id;button.dataset.kind=p.kind;button.setAttribute('aria-pressed','false');button.innerHTML=`<span class="palette-swatch" style="background:${gradient(p.colors)}" aria-hidden="true"></span><span class="palette-option-label">${p.name}<span class="palette-check" aria-hidden="true">✓</span></span><span class="palette-kind">${p.kind}</span>`;button.onclick=()=>apply({palette:p.id});$('palette-grid').append(button);}
  $('palette-filter').onchange=e=>document.querySelectorAll('[data-palette]').forEach(b=>b.hidden=e.target.value!=='All'&&b.dataset.kind!==e.target.value);
  $('reverse-palette').onchange=e=>apply({reversed:e.target.checked});
  $('use-custom').onclick=()=>apply({palette:'custom'});
  $('reset-palette').onclick=()=>{$('palette-filter').value='All';document.querySelectorAll('[data-palette]').forEach(b=>b.hidden=false);apply({...DEFAULT_APPEARANCE,custom:[...DEFAULT_APPEARANCE.custom]});};
  ['low','middle','high'].forEach((key,i)=>{const update=value=>{const custom=[...appearance.custom];custom[i]=value;apply({palette:'custom',custom});};$('color-'+key).oninput=e=>update(e.target.value);$('hex-'+key).oninput=e=>{e.target.setCustomValidity('');const v=e.target.value.trim();if(validHex(v))update(v);};$('hex-'+key).onchange=e=>{const v=e.target.value.trim();if(validHex(v))update(v);else{e.target.setCustomValidity('Enter a six-digit color, such as #2166AC.');e.target.reportValidity();}};});
  function close(){ $('appearance').close();opener?.focus(); }
  for(const id of ['open-colors','legend-colors'])$(id).onclick=()=>{if($('appearance').open){close();return;}opener=$(id);$('appearance').show();$('close-colors').focus();};
  $('close-colors').onclick=close;
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('appearance').open){e.preventDefault();close();}});
  sync();onChange(paletteStops(appearance),{...appearance});
  return {getState:()=>({...appearance,custom:[...appearance.custom]})};
}

