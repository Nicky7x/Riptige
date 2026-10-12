(()=>{'use strict';
const $=id=>document.getElementById(id),core=window.RiptideCore;
let original=null,mesh=null,selected=-1,fileName='',edits=[],history=[],future=[];
let axis=[0,1],viewBox=null,dragging=false,dragFrom=null,showEdges=true;
const names=['X','Y','Z'],canvas=$('stage'),ctx=canvas.getContext('2d');
const fmt=n=>Number.isFinite(n)?n.toLocaleString('pt-BR',{maximumFractionDigits:2}):'—';
function log(msg,err=false){$('status').textContent=msg;$('status').dataset.error=err?'yes':'no';}
function setEnabled(v){document.querySelectorAll('[data-requires]').forEach(el=>el.disabled=!v);}
function refreshCanvas(){const r=canvas.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2);canvas.width=Math.max(1,Math.round(r.width*d));canvas.height=Math.max(1,Math.round(r.height*d));ctx.setTransform(d,0,0,d,0,0);}
function limits(){const {width,height}=canvas.getBoundingClientRect();if(!mesh)return{cx:0,cy:0,scale:1,width,height};
const xs=mesh.vertices.map(v=>v[axis[0]]),ys=mesh.vertices.map(v=>v[axis[1]]);
const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
return{cx:(x0+x1)/2,cy:(y0+y1)/2,scale:Math.max(.00001,Math.min((width-44)/Math.max(1,x1-x0),(height-44)/Math.max(1,y1-y0))),width,height};}
function toPixel(v){const {cx,cy,scale,width,height}=viewBox;return[width/2+(v[axis[0]]-cx)*scale,height/2-(v[axis[1]]-cy)*scale];}
function toWorld(x,y){const {cx,cy,scale,width,height}=viewBox;return[cx+(x-width/2)/scale,cy-(y-height/2)/scale];}
function render(){
refreshCanvas();const{width:w,height:h}=canvas.getBoundingClientRect();
ctx.fillStyle='#0e1727';ctx.fillRect(0,0,w,h);ctx.strokeStyle='#1e2a3b';ctx.lineWidth=1;
for(let x=0;x<w;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
for(let y=0;y<h;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
if(!mesh){ctx.fillStyle='#8496b3';ctx.textAlign='center';ctx.font='15px system-ui';ctx.fillText('Carregue uma malha .bin local',w/2,h/2-4);ctx.font='12px system-ui';ctx.fillText('Prévia 2D • sem internet',w/2,h/2+22);return;}
viewBox=limits();const points=mesh.vertices.map(toPixel);
if(showEdges){ctx.strokeStyle='rgba(81,171,190,.17)';ctx.lineWidth=.75;ctx.beginPath();
const step=Math.max(1,Math.ceil(mesh.triangleCount/15000));
for(let t=0;t<mesh.triangleCount;t+=step){
const a=points[core.getIndex(mesh,t*3)],b=points[core.getIndex(mesh,t*3+1)],c=points[core.getIndex(mesh,t*3+2)];
ctx.moveTo(...a);ctx.lineTo(...b);ctx.lineTo(...c);ctx.closePath();}ctx.stroke();}
ctx.fillStyle='#5ddac2';const stride=Math.max(1,Math.ceil(points.length/12000));
for(let i=0;i<points.length;i+=stride)ctx.fillRect(points[i][0]-1.4,points[i][1]-1.4,2.8,2.8);
if(selected>=0){const[x,y]=points[selected];ctx.beginPath();ctx.arc(x,y,8,0,Math.PI*2);ctx.strokeStyle='#ffcc80';ctx.lineWidth=2.2;ctx.stroke();
ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fillStyle='#ffcc80';ctx.fill();}
ctx.fillStyle='#a6bed0';ctx.textAlign='left';ctx.font='11px system-ui';ctx.fillText(names[axis[0]]+' →',12,h-13);ctx.fillText(names[axis[1]]+' ↑',65,h-13);
}
function updateUI(){
$('filename').textContent=fileName||'Nenhum arquivo';
$('vertices').textContent=mesh?fmt(mesh.vertexCount):'—';$('triangles').textContent=mesh?fmt(mesh.triangleCount):'—';
$('unknown').textContent=mesh?fmt(mesh.unknownBytes)+' bytes':'—';$('changed').textContent=edits.length;
$('selection').textContent=selected<0?'Nenhum vértice selecionado':'Vértice #'+selected;
const v=selected>=0?mesh.vertices[selected]:[];
['coord-x','coord-y','coord-z'].forEach((id,i)=>{$(id).disabled=selected<0;$(id).value=v[i]===undefined?'':v[i];});
$('apply').disabled=selected<0;$('undo').disabled=!history.length;$('redo').disabled=!future.length;
}
function recalc(){edits=mesh&&original?core.diff(original,mesh):[];updateUI();}
function select(i){selected=i;updateUI();render();}
function commit(i,before,after){if(before.every((n,k)=>n===after[k]))return;history.push({i,before:[...before],after:[...after]});future=[];recalc();}
$('file').addEventListener('change',async e=>{
const f=e.target.files?.[0];if(!f)return;
try{const b=await f.arrayBuffer();original=core.parse(b.slice(0));mesh=core.parse(b.slice(0));fileName=f.name;selected=-1;history=[];future=[];edits=[];setEnabled(true);updateUI();render();log('Malha validada. Selecione um ponto para editar.');}
catch(err){mesh=null;original=null;fileName='';selected=-1;edits=[];history=[];future=[];setEnabled(false);updateUI();render();log('Arquivo incompatível: '+err.message,true);}
});
$('apply').addEventListener('click',()=>{
if(selected<0)return;try{
const c=['coord-x','coord-y','coord-z'].map(id=>Number($(id).value)),before=mesh.vertices[selected].slice();
const after=core.updateVertex(mesh,selected,c);commit(selected,before,after);render();
log('Vértice alterado localmente; ainda NÃO modifica o jogo.');}
catch(e){log(e.message,true);}
});
$('projection').addEventListener('change',e=>{axis=e.target.value.split(',').map(Number);render();});
$('edges').addEventListener('change',e=>{showEdges=e.target.checked;render();});
$('undo').addEventListener('click',()=>{const h=history.pop();if(!h)return;if(h.bulk){for(const v of h.bulk)core.updateVertex(mesh,v.i,v.before);}else core.updateVertex(mesh,h.i,h.before);future.push(h);recalc();render();});
$('redo').addEventListener('click',()=>{const h=future.pop();if(!h)return;if(h.bulk){for(const v of h.bulk)core.updateVertex(mesh,v.i,v.after);}else core.updateVertex(mesh,h.i,h.after);history.push(h);recalc();render();});
function download(blob,name){const a=document.createElement('a'),url=URL.createObjectURL(blob);a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),15000);}
$('savebin').addEventListener('click',()=>{if(!mesh)return;download(new Blob([mesh.buffer],{type:'application/octet-stream'}),fileName.replace(/\.bin$/i,'')+'.edited.bin');log('Malha .bin exportada; o restante do arquivo não foi modificado. Compatibilidade in-game NÃO testada.');});
$('savepatch').addEventListener('click',()=>{if(!mesh)return;const patch={format:'riptide-collision-vertex-patch-v1',source_filename:fileName,
vertex_count:mesh.vertexCount,triangle_count:mesh.triangleCount,
changes:edits.map(v=>({index:v.vertex,before:v.before,after:v.after})),
caveat:'Experimental; APF/APK não reconstruídos. Estruturas de física adicionais podem precisar de atualização.'};
download(new Blob([JSON.stringify(patch,null,2)],{type:'application/json'}),fileName.replace(/\.bin$/i,'')+'.patch.json');log('Patch exportado localmente.');});
function pos(e){const r=canvas.getBoundingClientRect();return[e.clientX-r.left,e.clientY-r.top];}
canvas.addEventListener('pointerdown',e=>{if(!mesh)return;const[x,y]=pos(e);const pts=mesh.vertices.map(toPixel);let best=-1,d=Infinity;
for(let i=0;i<pts.length;i++){const dx=x-pts[i][0],dy=y-pts[i][1],dist=dx*dx+dy*dy;if(dist<d){d=dist;best=i;}}
if(best>=0&&d<22*22){select(best);if($('drag').checked){dragging=true;dragFrom=mesh.vertices[best].slice();canvas.setPointerCapture(e.pointerId);}}
else select(-1);});
canvas.addEventListener('pointermove',e=>{if(!dragging||selected<0)return;const[x,y]=pos(e),[wx,wy]=toWorld(x,y);
const c=mesh.vertices[selected].slice();c[axis[0]]=wx;c[axis[1]]=wy;core.updateVertex(mesh,selected,c);updateUI();render();});
function finish(){if(!dragging)return;dragging=false;commit(selected,dragFrom,mesh.vertices[selected]);dragFrom=null;render();}
canvas.addEventListener('pointerup',finish);canvas.addEventListener('pointercancel',finish);window.addEventListener('resize',render);
window.RiptideEditor={
 loadBytes(source,name,edited=null){
   original=core.parse(source.slice(0));mesh=core.parse((edited||source).slice(0));
   fileName=name;selected=-1;history=[];future=[];recalc();setEnabled(true);updateUI();render();
   log('Malha embutida carregada: '+name);
 },
 getSnapshot(){return !mesh?null:{name:fileName,bytes:mesh.buffer.slice(0),
   patch:{resource_name:fileName.replace(/\.bin$/i,''),vertex_count:mesh.vertexCount,
     triangle_count:mesh.triangleCount,
     changes:edits.map(v=>({index:v.vertex,before:v.before.slice(),after:v.after.slice()}))}};},
 moveAll(dx,dy,dz){
   if(!mesh)throw new Error('Selecione um trecho primeiro');
   const delta=[dx,dy,dz];if(delta.some(v=>!Number.isFinite(v)||Math.abs(v)>1e5))throw new Error('Deslocamento inválido');
   const bulk=[];
   for(let i=0;i<mesh.vertexCount;i++){
     const old=mesh.vertices[i].slice(),next=old.map((v,k)=>v+delta[k]);
     if(next.every((v,k)=>v===old[k]))continue;
     const after=core.updateVertex(mesh,i,next);bulk.push({i,before:old,after});
   }
   if(bulk.length){history.push({bulk});future=[];recalc();render();}
   log('Movidos '+bulk.length+' vértices. APF/APK não alterados.');
   return bulk.length;
 }
};
setEnabled(false);updateUI();render();
})();
