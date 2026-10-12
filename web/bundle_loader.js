(async()=>{'use strict';
const $=s=>document.getElementById(s);
let bundle=JSON.parse($('private-assets').textContent);
if(bundle.__external_bundle){const response=await fetch('/arenas_bundle.json');if(!response.ok)throw Error('Falha ao carregar arenas: '+response.status);bundle=await response.json();}
const visuals=bundle.__visuals||{};delete bundle.__visuals;
const editor=window.RiptideEditor;
const arena=$('arena-select'),zone=$('zone-select'),notes=$('bundle-message');
const cache=new Map(),modified=new Map(),scene=window.RiptideScene3D||null;
let arenaToken=0;
let viewMode='arena',layer='collision';
const visualCache=new Map();
$('arena-count').textContent=Object.keys(bundle).length;
$('mesh-count').textContent=Object.values(bundle).reduce((s,v)=>s+Object.keys(v).length,0);
const key=()=>arena.value+'/'+zone.value;
function saveCurrent(){const data=editor.getSnapshot();if(data?.name){modified.set(data.name,{bytes:data.bytes,patch:data.patch});}
  $('patch-count').textContent=Array.from(modified.values()).filter(x=>x.patch.changes.length).length;
}
function b64ToBytes(encoded){const bin=atob(encoded),bytes=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);return bytes;}
async function inflate(payload){
  if(!('DecompressionStream' in window))throw new Error('Chrome desatualizado: falta suporte DecompressionStream');
  const stream=new Blob([b64ToBytes(payload)]).stream().pipeThrough(new DecompressionStream('gzip'));
  return await new Response(stream).arrayBuffer();
}
function populateArenas(){const options=Object.keys(bundle).sort().map(x=>new Option(x,x));arena.replaceChildren(...options);}
function populateZones(){const options=Object.keys(bundle[arena.value]).sort((a,b)=>(a==='Zone01_col'?-1:b==='Zone01_col'?1:a.localeCompare(b))).map(x=>new Option(x,x));zone.replaceChildren(...options);}
async function getOriginal(ar,segment){const key=ar+'/'+segment,asset=bundle[ar][segment];
  if(cache.has(key))return cache.get(key);
  const b=await inflate(asset.blob);
  if(b.byteLength!==asset.size)throw Error('Tamanho incorreto '+key);
  cache.set(key,b);return b;}
async function getVisual(ar,name){
  const id='visual/'+ar+'/'+name,asset=visuals[ar]?.[name];
  if(!asset)throw new Error('Modelo visual não encontrado');
  if(visualCache.has(id))return visualCache.get(id);
  const bytes=await inflate(asset.blob);
  if(bytes.byteLength!==asset.size)throw new Error('Modelo visual corrompido: '+name);
  visualCache.set(id,bytes);return bytes;
}
function modelForSection(section){
  const models=Object.keys(visuals[arena.value]||{});
  const base=section.replace(/_col$/i,'');
  return models.find(x=>x===base) || models.find(x=>x.startsWith(base+'_')) || models[0] || '';
}
function setControls(){
  $('mode-arena')?.classList.toggle('primary',viewMode==='arena');
  $('mode-section')?.classList.toggle('primary',viewMode==='segment');
  $('layer-visual')?.classList.toggle('primary',layer==='visual');
  $('layer-collision')?.classList.toggle('primary',layer==='collision');
  if($('layer-visual'))$('layer-visual').disabled=!Object.keys(visuals[arena.value]||{}).length;
  if($('scene3d-move'))$('scene3d-move').disabled=layer==='visual';
  if($('scene3d-show-all')){$('scene3d-show-all').checked=true;$('scene3d-show-all').disabled=true;}
  if($('scene3d-all'))$('scene3d-all').disabled=viewMode==='segment';
  if($('scene3d-focus'))$('scene3d-focus').disabled=viewMode==='arena';
  if($('visual-layer-note'))$('visual-layer-note').textContent=layer==='visual'
    ?'Prévia dos modelos 3D do jogo SEM texturas. Somente leitura; a edição física continua independente.'
    :'Malhas físicas de colisão (editáveis). Não representam a aparência texturizada final.';
}
async function openSceneArena(){
  if(!scene)return;
  const token=++arenaToken,ar=arena.value,records=[];
  setControls();
  $('scene3d-info').textContent='Carregando '+(layer==='visual'?'geometria visual':'colisões')+' de '+ar+'…';
  try{
    if(layer==='visual'){
      let names=Object.keys(visuals[ar]||{}).sort();
      if(viewMode==='segment'){
        const base=zone.value.replace(/_col$/i,'');
        const subset=names.filter(n=>n===base||n.startsWith(base+'_'));
        names=subset.length?subset:(modelForSection(zone.value)?[modelForSection(zone.value)]:[]);
      }
      for(const name of names){
        const data=await getVisual(ar,name);if(token!==arenaToken)return;
        records.push({key:name,data});
      }
    }else{
      let names=Object.keys(bundle[ar]).sort();
      if(viewMode==='segment')names=names.filter(n=>n===zone.value);
      for(const section of names){
        const data=await getOriginal(ar,section);if(token!==arenaToken)return;
        const source=bundle[ar][section].source+'.bin';
        records.push({key:section,data:modified.get(source)?.bytes||data});
      }
    }
    if(token!==arenaToken)return;
    await scene.loadArena(records);
    if(layer==='collision')scene.select(zone.value);
    else if(viewMode==='segment')scene.select(modelForSection(zone.value));
    scene.focusAll();
    const type=layer==='visual'?'modelos visuais SEM texturas':'trechos de colisão';
    $('arena-summary').textContent='Arena '+ar+' · '+records.length+' '+type+
      (viewMode==='arena'?' exibidos juntos.':' · apenas o trecho selecionado.')+
      (layer==='visual'?' Visualização somente leitura.':'');
  }catch(err){if(token===arenaToken)$('scene3d-info').textContent='Falha na prévia 3D: '+err.message;}
}
$('mode-arena')?.addEventListener('click',()=>{viewMode='arena';openSceneArena();});
$('mode-section')?.addEventListener('click',()=>{viewMode='segment';openSceneArena();});
$('layer-visual')?.addEventListener('click',()=>{layer='visual';scene?.setMode('orbit');openSceneArena();});
$('layer-collision')?.addEventListener('click',()=>{layer='collision';openSceneArena();});
function syncScene(){if(!scene||layer!=='collision')return;const snap=editor.getSnapshot();if(snap&&zone.value)scene.update(zone.value,snap.bytes);}

let loading=0;
async function openZone(){const token=++loading;
  notes.textContent='Abrindo '+key()+'…';
  try{
    const id=key(),asset=bundle[arena.value][zone.value];
    if(!asset)return;
    const base=await getOriginal(arena.value,zone.value);
    if(token!==loading)return;
    if(base.byteLength!==asset.size)throw new Error('Tamanho do recurso não confere');
    cache.set(id,base);
    const edited=modified.get(asset.source+'.bin')?.bytes||null;
    editor.loadBytes(base,asset.source+'.bin',edited);scene?.select(zone.value);
    notes.textContent='Trecho '+id+' · '+asset.vertices.toLocaleString('pt-BR')+' vértices. Colisão apenas; não altera visual do jogo.';
  }catch(e){notes.textContent='Falha ao abrir recurso: '+e.message;}
}
arena.addEventListener('change',()=>{saveCurrent();populateZones();if(layer==='visual'&&!Object.keys(visuals[arena.value]||{}).length)layer='collision';openZone();openSceneArena();});
zone.addEventListener('change',()=>{saveCurrent();openZone();if(viewMode==='segment')openSceneArena();});
async function moveEntireArena(){
  const delta=['bulk-x','bulk-y','bulk-z'].map(id=>Number($(id).value));
  if(delta.some(n=>!Number.isFinite(n)||Math.abs(n)>100000)){notes.textContent='Deslocamento inválido';return;}
  if(delta.every(n=>n===0)){notes.textContent='Defina um deslocamento diferente de zero.';return;}
  saveCurrent();
  const ar=arena.value;
  const segments=Object.keys(bundle[ar]);
  $('bulk-arena').disabled=true;
  notes.textContent='Movendo a arena '+ar+' inteira…';
  try{
    let count=0;
    for(const segment of segments){
      const asset=bundle[ar][segment],base=await getOriginal(ar,segment);
      const resource=asset.source+'.bin';
      const state=modified.get(resource);
      const current=(state?state.bytes:base).slice(0),parsed=window.RiptideCore.parse(current);
      for(let i=0;i<parsed.vertexCount;i++){
        const next=parsed.vertices[i].map((v,k)=>v+delta[k]);
        window.RiptideCore.updateVertex(parsed,i,next);
      }
      const original=window.RiptideCore.parse(base.slice(0));
      const changes=window.RiptideCore.diff(original,parsed).map(v=>({index:v.vertex,before:v.before,after:v.after}));
      modified.set(resource,{bytes:parsed.buffer,patch:{resource_name:resource.replace(/\\.bin$/i,''),vertex_count:parsed.vertexCount,triangle_count:parsed.triangleCount,changes}});
      scene?.update(segment,parsed.buffer);
      count++;
      if(count%2===0)await new Promise(resolve=>setTimeout(resolve,0));
    }
    await openZone();scene?.focusAll();
    $('patch-count').textContent=Array.from(modified.values()).filter(x=>x.patch.changes.length).length;
    notes.textContent='Arena '+ar+' inteira deslocada: '+count+' trechos. Exporte o patch para salvar.';
  }catch(e){notes.textContent='Falha ao mover arena: '+e.message;}
  finally{$('bulk-arena').disabled=false;}
}
$('bulk-arena')?.addEventListener('click',moveEntireArena);


$('bulk-apply').addEventListener('click',()=>{
 const delta=['bulk-x','bulk-y','bulk-z'].map(id=>Number($(id).value));
 try{editor.moveAll(...delta);saveCurrent();syncScene();}catch(e){notes.textContent=e.message;}
});
function saveFile(text,name){if(window.AndroidBridge&&window.AndroidBridge.exportJson){window.AndroidBridge.exportJson(name,text);return;}const blob=new Blob([text],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),12000);}
$('bundle-export').addEventListener('click',()=>{
 saveCurrent();const changes=[...modified.values()].map(v=>v.patch).filter(p=>p.changes.length);
 const manifest={format:'riptide-collision-multi-patch-v1',created:new Date().toISOString(),
  arenas_included:Object.keys(bundle),changes,
  warning:'APF/APK NÃO modificado. Apenas geometria física experimental; sem atualização dos dados desconhecidos de colisão. Não é pista jogável.'};
 saveFile(JSON.stringify(manifest,null,2),'riptide-arenas-patch.json');
 notes.textContent='Patch único exportado: '+changes.length+' malhas modificadas.';
});
// Keep the selector on the same mesh state even if user exports individual BIN.
['apply','undo','redo'].forEach(id=>$(id).addEventListener('click',()=>queueMicrotask(()=>{saveCurrent();syncScene();})));
$('stage').addEventListener('pointerup',()=>queueMicrotask(()=>{saveCurrent();syncScene();}));
if(scene){scene.on({
  onSelect(section){if(layer==='visual')return;if(zone.value===section)return;zone.value=section;zone.dispatchEvent(new Event('change'));},
  onMove(section,delta){if(layer==='visual'||zone.value!==section)return;
    try{editor.moveAll(...delta);saveCurrent();syncScene();
      notes.textContent='Trecho '+section+' deslocado em 3D. '+editor.getSnapshot().patch.changes.length+' vértices alterados.';
    }catch(err){notes.textContent='Não foi possível mover: '+err.message;}}
 });}
populateArenas();populateZones();openZone();openSceneArena();
})();