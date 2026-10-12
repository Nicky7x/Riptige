(()=>{'use strict';
const $=s=>document.getElementById(s);
const bundle=JSON.parse($('private-assets').textContent);
const editor=window.RiptideEditor;
const arena=$('arena-select'),zone=$('zone-select'),notes=$('bundle-message');
const cache=new Map(),modified=new Map();
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
function populateZones(){const options=Object.keys(bundle[arena.value]).sort().map(x=>new Option(x,x));zone.replaceChildren(...options);}
let loading=0;
async function openZone(){const token=++loading;
  notes.textContent='Abrindo '+key()+'…';
  try{
    const id=key(),asset=bundle[arena.value][zone.value];
    if(!asset)return;
    const base=cache.has(id)?cache.get(id):await inflate(asset.blob);
    if(token!==loading)return;
    if(base.byteLength!==asset.size)throw new Error('Tamanho do recurso não confere');
    cache.set(id,base);
    const edited=modified.get(asset.source+'.bin')?.bytes||null;
    editor.loadBytes(base,asset.source+'.bin',edited);
    notes.textContent='Trecho '+id+' · '+asset.vertices.toLocaleString('pt-BR')+' vértices. Colisão apenas; não altera visual do jogo.';
  }catch(e){notes.textContent='Falha ao abrir recurso: '+e.message;}
}
arena.addEventListener('change',()=>{saveCurrent();populateZones();openZone();});
zone.addEventListener('change',()=>{saveCurrent();openZone();});
$('bulk-apply').addEventListener('click',()=>{
 const delta=['bulk-x','bulk-y','bulk-z'].map(id=>Number($(id).value));
 try{editor.moveAll(...delta);saveCurrent();}catch(e){notes.textContent=e.message;}
});
function saveFile(text,name){const blob=new Blob([text],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),12000);}
$('bundle-export').addEventListener('click',()=>{
 saveCurrent();const changes=[...modified.values()].map(v=>v.patch).filter(p=>p.changes.length);
 const manifest={format:'riptide-collision-multi-patch-v1',created:new Date().toISOString(),
  arenas_included:Object.keys(bundle),changes,
  warning:'APF/APK NÃO modificado. Apenas geometria física experimental; sem atualização dos dados desconhecidos de colisão. Não é pista jogável.'};
 saveFile(JSON.stringify(manifest,null,2),'riptide-arenas-patch.json');
 notes.textContent='Patch único exportado: '+changes.length+' malhas modificadas.';
});
// Keep the selector on the same mesh state even if user exports individual BIN.
['apply','undo','redo'].forEach(id=>$(id).addEventListener('click',()=>queueMicrotask(saveCurrent)));
$('stage').addEventListener('pointerup',()=>queueMicrotask(saveCurrent));
populateArenas();populateZones();openZone();
})();