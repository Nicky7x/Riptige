/* Riptide Map Lab v0.9: offline GLB world-scene viewport and AI-readable scene edits.
   No network, no commercial assets shipped. Parses only files explicitly chosen by user.
   Schema: riptide-world-edit-v1 (references private GLB mesh assets, no vertex data). */
(function(root){ 'use strict';
const MAX_BYTES=140*1024*1024, MAX_NODES=60000;
const $=id=>document.getElementById(id);
function fail(message){throw new Error(message)}
const I=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
function mul(a,b){const o=new Array(16).fill(0);for(let c=0;c<4;c++)for(let r=0;r<4;r++)for(let k=0;k<4;k++)o[c*4+r]+=a[k*4+r]*b[c*4+k];return o;}
function quaternion(q){const [x,y,z,w]=q;const xx=x*x,yy=y*y,zz=z*z,xy=x*y,xz=x*z,yz=y*z,wx=w*x,wy=w*y,wz=w*z;
 return [1-2*(yy+zz),2*(xy+wz),2*(xz-wy),0,2*(xy-wz),1-2*(xx+zz),2*(yz+wx),0,2*(xz+wy),2*(yz-wx),1-2*(xx+yy),0,0,0,0,1];}
function local(n){if(Array.isArray(n.matrix)&&n.matrix.length===16)return n.matrix.slice();const t=n.translation||[0,0,0],s=n.scale||[1,1,1];const m=quaternion(n.rotation||[0,0,0,1]);for(let c=0;c<3;c++)for(let r=0;r<3;r++)m[c*4+r]*=s[c];m[12]=t[0];m[13]=t[1];m[14]=t[2];return m;}
function vec(a){const l=Math.hypot(...a)||1;return a.map(v=>v/l)}
function cross(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]}
function dot(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]}
function look(eye,target){const z=vec(eye.map((v,i)=>v-target[i])),x=vec(cross([0,1,0],z)),y=cross(z,x);return[x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1]}
function projection(aspect,far){const n=.15,f=Math.max(300,far),q=1/Math.tan(Math.PI/6);return[q/aspect,0,0,0,0,q,0,0,0,0,(f+n)/(n-f),-1,0,0,2*f*n/(n-f),0]}
function proj(m,p){const a=[p[0],p[1],p[2],1],v=[0,0,0,0];for(let r=0;r<4;r++)for(let c=0;c<4;c++)v[r]+=m[c*4+r]*a[c];return v}
function readGLB(array){if(!(array instanceof ArrayBuffer)||array.byteLength<28||array.byteLength>MAX_BYTES)fail('GLB inválido ou maior que 140 MB');
 const d=new DataView(array);if(d.getUint32(0,true)!==0x46546c67||d.getUint32(4,true)!==2||d.getUint32(8,true)!==array.byteLength)fail('Arquivo não é GLB 2.0');
 let ptr=12,g=null,bin=null;
 while(ptr+8<=array.byteLength){let length=d.getUint32(ptr,true),kind=d.getUint32(ptr+4,true);ptr+=8;
 if(length>array.byteLength-ptr)fail('Bloco GLB truncado');if(kind===0x4e4f534a){if(g)fail('JSON duplicado');g=JSON.parse(new TextDecoder().decode(new Uint8Array(array,ptr,length)).trim());}
 if(kind===0x004e4942){if(bin)fail('BIN duplicado');bin=new Uint8Array(array,ptr,length);}ptr+=length;}
 if(ptr!==array.byteLength||!g||!bin||!Array.isArray(g.meshes)||!Array.isArray(g.nodes))fail('Cena GLB incompleta');
 if(g.nodes.length>MAX_NODES||g.meshes.length>MAX_NODES)fail('Cena grande demais');
 if(g.extensionsRequired?.length)fail('Extensões glTF requeridas não suportadas: '+g.extensionsRequired.join(', '));
 function accessor(id){const a=g.accessors[id],v=g.bufferViews[a?.bufferView];if(!a||!v||v.buffer!==0||a.sparse||a.byteOffset<0||v.byteOffset<0)fail('Accessor GLB não suportado');
 const elem=a.type==='VEC3'?3:a.type==='SCALAR'?1:0,bytes=a.componentType===5126||a.componentType===5125?4:a.componentType===5123?2:a.componentType===5121?1:0;
 if(!elem||!bytes||a.count>8000000)fail('Atributo GLB inválido');const stride=v.byteStride||elem*bytes;
 if(stride<elem*bytes||stride>256)fail('Stride GLB inválido');const off=(v.byteOffset||0)+(a.byteOffset||0);
 if(off+(a.count?a.count-1:0)*stride+elem*bytes>bin.byteLength)fail('Accessor GLB ultrapassa BIN');
 const view=new DataView(bin.buffer,bin.byteOffset,bin.byteLength),out=new (a.componentType===5126?Float32Array:a.componentType===5125?Uint32Array:a.componentType===5123?Uint16Array:Uint8Array)(a.count*elem);
 for(let i=0;i<a.count;i++)for(let k=0;k<elem;k++){const at=off+i*stride+k*bytes;
 out[i*elem+k]=a.componentType===5126?view.getFloat32(at,true):a.componentType===5125?view.getUint32(at,true):a.componentType===5123?view.getUint16(at,true):view.getUint8(at);}
 return {array:out,count:a.count,type:a.type,componentType:a.componentType,min:a.min,max:a.max};}
 const cache=new Map(),geometry=new Map();
 for(let mi=0;mi<g.meshes.length;mi++){
 const m=g.meshes[mi];if(!m.primitives?.length)continue;const groups=[];
 for(const p of m.primitives){if(p.mode!==undefined&&p.mode!==4)continue;let key=p.attributes?.POSITION+'|'+p.indices;
 if(!geometry.has(key)){
 const pos=cache.get(p.attributes.POSITION)||accessor(p.attributes.POSITION);cache.set(p.attributes.POSITION,pos);
 if(pos.type!=='VEC3'||pos.componentType!==5126)fail('Posições devem ser VEC3 FLOAT');
 let ix;if(p.indices===undefined){ix={array:Uint32Array.from({length:pos.count},(_,i)=>i),type:'SCALAR'};}
 else{ix=cache.get('i'+p.indices)||accessor(p.indices);cache.set('i'+p.indices,ix);}if(ix.type!=='SCALAR'||ix.array.length%3)fail('Triângulos inválidos');
 geometry.set(key,{key,positions:pos.array,indices:ix.array,min:pos.min||[0,0,0],max:pos.max||[0,0,0],group:[]});}
 groups.push(key);
 }m.__riptide=groups;
 }
 const nodes=[],orig=g.nodes;
 function walk(id,parent,chain){if(chain.has(id))fail('Ciclo na hierarquia GLB');const n=orig[id];if(!n)fail('Nó GLB desconhecido');const m=mul(parent,local(n));const next=new Set(chain);next.add(id);
 if(Number.isInteger(n.mesh)&&g.meshes[n.mesh]){nodes.push({id:'glb-'+id,name:n.name||'Objeto '+id,mesh:n.mesh,geometry:g.meshes[n.mesh].__riptide, matrix:m,hidden:false});}
 for(const child of n.children||[])walk(child,m,next);}
 for(const n of (g.scenes?.[g.scene||0]?.nodes||[]))walk(n,I(),new Set());
 if(!nodes.length)fail('Nenhum modelo renderizável no GLB');
 for(const n of nodes)if(n.matrix.some(v=>!Number.isFinite(v)||Math.abs(v)>1e8))fail('Transformação fora do limite');
 return {nodes,geometry,meshNames:g.meshes.map((m,i)=>m.name||'Mesh '+i),sourceBytes:array.byteLength};
}
// Use a dedicated canvas to leave the previously validated collision/texture viewer untouched.
let shell=$('v07-shell'),viewport=$('v07-viewport');if(!shell||!viewport)return;
const style=document.createElement('style');style.textContent=`
#rw-world{position:absolute;inset:0;z-index:16;background:#071525;display:none;touch-action:none}
#rw-world.show{display:block}#rw-world canvas{width:100%;height:100%;min-height:0;border-radius:0;touch-action:none}
#rw-bar{position:absolute;top:8px;left:8px;right:8px;display:flex;align-items:center;gap:6px;pointer-events:none;z-index:3}
#rw-bar>*{pointer-events:auto}#rw-title{font-size:11px;background:#082532e8;color:#75e8d6;border-radius:8px;padding:6px 10px;max-width:46%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#rw-tools{position:absolute;bottom:8px;left:8px;right:8px;display:flex;gap:5px;align-items:center;z-index:3;background:#0b2538ec;border:1px solid #44647b;border-radius:10px;padding:5px;flex-wrap:wrap;max-height:52%;overflow-y:auto}
#rw-tools button,#rw-bar button{font-size:11px;min-height:30px;padding:5px 8px;border-radius:7px}
#rw-tools input{font-size:11px;width:67px;padding:4px;min-height:30px}
#rw-meta{color:#a9cde0;font-size:10px;overflow:hidden;text-overflow:ellipsis;flex:1;white-space:nowrap}
#rw-world .rw-hidden{display:none}#rw-toast{position:absolute;top:42px;left:8px;background:#0c293bbd;padding:5px 8px;border-radius:8px;max-width:75%;font-size:11px;color:#bee9f4;pointer-events:none}
`;document.head.append(style);
const wrap=document.createElement('div');wrap.id='rw-world';wrap.innerHTML=`<canvas id="rw-canvas" aria-label="Cena 3D com instâncias reais"></canvas>
<div id="rw-bar"><span id="rw-title">Cena 3D — carregue um GLB</span><button id="rw-home">Enquadrar</button><button id="rw-close">Voltar ✕</button></div>
<div id="rw-toast">Arraste para girar · gesto com dois dedos para zoom · toque para selecionar objeto</div>
<div id="rw-tools"><span id="rw-meta">Nenhum objeto selecionado</span><label>X <input id="rw-x" type="number" step="0.5" aria-label="Posição X"/></label><label>Y <input id="rw-y" type="number" step="0.5" aria-label="Posição Y"/></label><label>Z <input id="rw-z" type="number" step="0.5" aria-label="Posição Z"/></label><button id="rw-apply">Mover</button><button id="rw-copy">Duplicar</button><button id="rw-hide">Ocultar</button><button id="rw-save">Cena JSON</button><button id="rw-load">Importar JSON</button></div>`;viewport.append(wrap);
const input=document.createElement('input');input.type='file';input.accept='.glb,model/gltf-binary,application/octet-stream';input.style.display='none';document.body.append(input);
const jsonInput=document.createElement('input');jsonInput.type='file';jsonInput.accept='.json,application/json';jsonInput.style.display='none';document.body.append(jsonInput);
const canvas=$('rw-canvas'),gl=canvas.getContext('webgl',{antialias:true,alpha:false});
let ext=gl?.getExtension('ANGLE_instanced_arrays'),UINT=gl?.getExtension('OES_element_index_uint'),loaded=null,selected=null,dirty=true,cacheGPU=new Map(),batches=[],center=[0,0,0],distance=500,yaw=.7,pitch=.58,vp=null,pointers=new Map(),gesture=null;
function note(s){$('rw-toast').textContent=s}
function shader(type,code){const o=gl.createShader(type);gl.shaderSource(o,code);gl.compileShader(o);if(!gl.getShaderParameter(o,gl.COMPILE_STATUS))fail('Shader: '+gl.getShaderInfoLog(o));return o}
let program=null,loc=null;
if(gl){program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,`
attribute vec3 pos;attribute vec4 m0,m1,m2,m3;uniform mat4 viewProj;varying float shade;
void main(){vec4 p=mat4(m0,m1,m2,m3)*vec4(pos,1.0);shade=clamp(.48+.003*p.y,.22,.95);gl_Position=viewProj*p;}`));
gl.attachShader(program,shader(gl.FRAGMENT_SHADER,`precision mediump float;varying float shade;void main(){gl_FragColor=vec4(vec3(.37,.57,.66)*shade,1.);}`));gl.linkProgram(program);
if(!gl.getProgramParameter(program,gl.LINK_STATUS))fail(gl.getProgramInfoLog(program));
loc={pos:gl.getAttribLocation(program,'pos'),matrix:[0,1,2,3].map(i=>gl.getAttribLocation(program,'m'+i)),vp:gl.getUniformLocation(program,'viewProj')};}
function clearGPU(){if(!gl)return;for(const g of cacheGPU.values()){gl.deleteBuffer(g.pos);gl.deleteBuffer(g.idx);}for(const b of batches)gl.deleteBuffer(b.matrixBuffer);cacheGPU.clear();batches=[]}
function recompute(){if(!loaded||!gl)return;for(const b of batches)gl.deleteBuffer(b.matrixBuffer);batches=[];
 const sorted=new Map();for(const node of loaded.nodes){if(node.hidden)continue;for(const key of node.geometry||[]){if(!sorted.has(key))sorted.set(key,[]);sorted.get(key).push(node);}}
 for(const [key,nodes] of sorted){const resource=loaded.geometry.get(key);if(!resource)continue;let gpu=cacheGPU.get(key);if(!gpu){let indices=resource.indices;let type=indices instanceof Uint32Array?gl.UNSIGNED_INT:indices instanceof Uint8Array?gl.UNSIGNED_BYTE:gl.UNSIGNED_SHORT;
 if(type===gl.UNSIGNED_INT&&!UINT){const maxIndex=indices.reduce((max,v)=>Math.max(max,v),0);if(maxIndex>65535){note('GPU sem índices de 32 bits; parte da cena não será exibida.');continue;}indices=Uint16Array.from(indices);type=gl.UNSIGNED_SHORT;}
 const pos=gl.createBuffer(),idx=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,pos);gl.bufferData(gl.ARRAY_BUFFER,resource.positions,gl.STATIC_DRAW);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,idx);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,indices,gl.STATIC_DRAW);
 gpu={pos,idx,type,count:indices.length};cacheGPU.set(key,gpu);}
 const matrices=new Float32Array(nodes.length*16);nodes.forEach((n,i)=>matrices.set(n.matrix,i*16));const matrixBuffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,matrixBuffer);gl.bufferData(gl.ARRAY_BUFFER,matrices,gl.DYNAMIC_DRAW);
 batches.push({gpu,matrixBuffer,count:nodes.length,nodes,matrices});
 }dirty=true;draw();}
function bounds(){let lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(const n of loaded.nodes){if(n.hidden)continue;for(const key of n.geometry||[]){const g=loaded.geometry.get(key);if(!g)continue;
 for(let k=0;k<8;k++){const xyz=[k&1?g.max[0]:g.min[0],k&2?g.max[1]:g.min[1],k&4?g.max[2]:g.min[2]];const p=proj(n.matrix,xyz);for(let a=0;a<3;a++){lo[a]=Math.min(lo[a],p[a]);hi[a]=Math.max(hi[a],p[a]);}}}}
 if(!Number.isFinite(lo[0]))fail('Limites da cena desconhecidos');return{lo,hi};}
function focus(){if(!loaded)return;const b=bounds();center=b.lo.map((v,i)=>(v+b.hi[i])/2);const diag=Math.hypot(...b.lo.map((v,i)=>b.hi[i]-v));distance=Math.max(15,diag*1.4);yaw=.7;pitch=.55;dirty=true;draw();}
function eye(){return [center[0]+distance*Math.cos(pitch)*Math.sin(yaw),center[1]+distance*Math.sin(pitch),center[2]+distance*Math.cos(pitch)*Math.cos(yaw)]}
function resize(){const rect=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,1.7),w=Math.max(1,Math.floor(rect.width*dpr)),h=Math.max(1,Math.floor(rect.height*dpr));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;dirty=true;}return[w,h]}
function draw(){if(!loaded||!gl||!wrap.classList.contains('show')||!dirty)return;dirty=false;const[w,h]=resize();gl.viewport(0,0,w,h);gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);gl.clearColor(.028,.061,.106,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);vp=mul(projection(w/h,distance*10+500),look(eye(),center));gl.useProgram(program);gl.uniformMatrix4fv(loc.vp,false,new Float32Array(vp));
 for(const batch of batches){gl.bindBuffer(gl.ARRAY_BUFFER,batch.gpu.pos);gl.enableVertexAttribArray(loc.pos);gl.vertexAttribPointer(loc.pos,3,gl.FLOAT,false,0,0);
 gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,batch.gpu.idx);gl.bindBuffer(gl.ARRAY_BUFFER,batch.matrixBuffer);
 for(let i=0;i<4;i++){const a=loc.matrix[i];gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,4,gl.FLOAT,false,64,i*16);if(ext)ext.vertexAttribDivisorANGLE(a,1);}
 if(ext)ext.drawElementsInstancedANGLE(gl.TRIANGLES,batch.gpu.count,batch.gpu.type,0,batch.count);
 else{for(let i=0;i<Math.min(batch.count,600);i++){for(let col=0;col<4;col++){const a=loc.matrix[col];gl.disableVertexAttribArray(a);gl.vertexAttrib4fv(a,batch.matrices.subarray(i*16+col*4,i*16+col*4+4));}gl.drawElements(gl.TRIANGLES,batch.gpu.count,batch.gpu.type,0);}}
 if(ext)for(const a of loc.matrix)ext.vertexAttribDivisorANGLE(a,0);
 }
 if(selected){const p=proj(vp,[selected.matrix[12],selected.matrix[13],selected.matrix[14]]);if(p[3]>0){let x=(p[0]/p[3]*.5+.5)*w,y=(1-(p[1]/p[3]*.5+.5))*h;const marker=$('rw-toast');marker.style.left=Math.max(8,Math.min(canvas.clientWidth-100,x/(w/canvas.clientWidth)))+'px';marker.style.top=Math.max(42,Math.min(canvas.clientHeight-90,y/(h/canvas.clientHeight)))+'px';} }
 }
function activateFile(file){if(!file)return;const reader=new FileReader();reader.onload=()=>{try{load(reader.result,file.name)}catch(err){note('Falha no GLB: '+err.message);console.error(err)}};reader.onerror=()=>note('Não foi possível abrir o arquivo.');reader.readAsArrayBuffer(file);}
function load(buffer,name){if(!gl)fail('WebGL indisponível para a visualização de instâncias.');let scene=readGLB(buffer);clearGPU();loaded=scene;selected=null;recompute();wrap.classList.add('show');$('rw-title').textContent='Cena: '+name+' · '+loaded.nodes.length+' objetos';$('rw-meta').textContent='Toque para selecionar';focus();note('Cena original carregada. Toque em uma peça, altere X/Y/Z ou exporte JSON para IA.');$('v07-drawer').hidden=true;}
function select(n){selected=n;for(const [k,i] of [['rw-x',12],['rw-y',13],['rw-z',14]])$(k).value=n?Number(n.matrix[i].toFixed(3)):'';
 $('rw-meta').textContent=n?(n.name+' · '+loaded.meshNames[n.mesh]):'Toque para selecionar';dirty=true;draw();}
function saveScene(){if(!loaded)return;const doc={format:'riptide-world-edit-v1',version:1,units:'glTF_Y_UP',assetSource:'user-selected-private-GLB',entities:loaded.nodes.map(n=>({id:n.id,name:n.name,mesh:loaded.meshNames[n.mesh],meshIndex:n.mesh,matrix:n.matrix.map(x=>Number(x.toFixed(6))),hidden:n.hidden}))};
 const payload=JSON.stringify(doc,null,2);if(root.AndroidBridge?.exportJson)root.AndroidBridge.exportJson('riptide-world-edit-v1.json',payload);
 else {let a=document.createElement('a'),url=URL.createObjectURL(new Blob([payload],{type:'application/json'}));a.href=url;a.download='riptide-world-edit-v1.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),15000);}note('Cena exportada: '+doc.entities.length+' entidades. JSON para IAs; modelos permanecem no GLB privado.');}
function applyJSON(s){if(!loaded)fail('Abra o GLB de referência antes do JSON');const obj=JSON.parse(s);if(obj.format!=='riptide-world-edit-v1'||!Array.isArray(obj.entities)||obj.entities.length>MAX_NODES)fail('Formato de edição de cena desconhecido');
 const newNodes=[],ids=new Set();for(const n of obj.entities){if(typeof n.id!=='string'||n.id.length>400||ids.has(n.id)||!Number.isInteger(n.meshIndex)||n.meshIndex<0||n.meshIndex>=loaded.meshNames.length||n.mesh!==loaded.meshNames[n.meshIndex]||!Array.isArray(n.matrix)||n.matrix.length!==16||n.matrix.some(v=>typeof v!=='number'||!Number.isFinite(v)||Math.abs(v)>1e7))fail('Entidade JSON inválida');ids.add(n.id);const geom=loaded.geometry;const keys=(loaded.baseMeshGeometry||[])[n.meshIndex];const available=(loaded.meshDefs[n.meshIndex]||[]);newNodes.push({id:n.id,name:String(n.name||n.id).slice(0,300),mesh:n.meshIndex,geometry:available.slice(),matrix:n.matrix.slice(),hidden:!!n.hidden});}
 loaded.nodes=newNodes;select(null);recompute();focus();note('Cena JSON aplicada: '+newNodes.length+' entidades.');}
// Set after parse; allows JSON import to refer to the original mesh geometry by stable meshIndex.
const oldRead=readGLB;readGLB=function(ab){const doc=oldRead(ab);doc.meshDefs=[];for(const n of doc.nodes)if(!doc.meshDefs[n.mesh])doc.meshDefs[n.mesh]=n.geometry;return doc;};
const button=document.createElement('button');button.textContent='Abrir cena 3D (GLB)';button.id='rw-import';button.addEventListener('click',()=>input.click());$('v07-drawer-top').append(button);
input.addEventListener('change',()=>{const f=input.files?.[0];if(f)activateFile(f);input.value='';});
jsonInput.addEventListener('change',()=>{const f=jsonInput.files?.[0];if(!f)return;f.text().then(applyJSON).catch(e=>note('JSON inválido: '+e.message));jsonInput.value='';});
$('rw-close').onclick=()=>{wrap.classList.remove('show');selected=null;note('Cena fechada; a visualização original permanece disponível.')};
$('rw-home').onclick=focus;
$('rw-apply').onclick=()=>{if(!selected)return note('Selecione um objeto antes de mover.');const val=['rw-x','rw-y','rw-z'].map(x=>Number($(x).value));if(val.some(n=>!Number.isFinite(n)||Math.abs(n)>1e7))return note('Coordenadas inválidas');selected.matrix[12]=val[0];selected.matrix[13]=val[1];selected.matrix[14]=val[2];recompute();note('Posição atualizada. Exporte a cena JSON para salvar.')};
$('rw-copy').onclick=()=>{if(!selected)return note('Selecione um objeto para duplicar');const id='object-copy-'+loaded.nodes.length+'-'+Math.floor(performance.now()).toString(36);const n={...selected,id,name:selected.name+' (cópia)',matrix:selected.matrix.slice(),geometry:selected.geometry.slice(),hidden:false};n.matrix[12]+=3;loaded.nodes.push(n);select(n);recompute();note('Objeto duplicado: '+n.name)};
$('rw-hide').onclick=()=>{if(!selected)return note('Selecione um objeto para ocultar');selected.hidden=!selected.hidden;const name=selected.name;recompute();note((selected.hidden?'Ocultado: ':'Restaurado: ')+name+' (exporte JSON)')};
$('rw-save').onclick=saveScene;$('rw-load').onclick=()=>jsonInput.click();
function xy(e){const r=canvas.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top}}
canvas.addEventListener('pointerdown',e=>{e.preventDefault();canvas.setPointerCapture(e.pointerId);const p=xy(e);pointers.set(e.pointerId,{...p,startX:p.x,startY:p.y,movement:0});if(pointers.size>1){const a=[...pointers.values()];gesture=Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y);} });
canvas.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;e.preventDefault();const p=xy(e),old=pointers.get(e.pointerId);p.movement=old.movement+Math.hypot(p.x-old.x,p.y-old.y);p.startX=old.startX;p.startY=old.startY;pointers.set(e.pointerId,p);if(pointers.size>1){const a=[...pointers.values()],newDist=Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y);if(gesture)distance*=Math.max(.85,Math.min(1.15,gesture/Math.max(1,newDist)));gesture=newDist;}else{yaw-=(p.x-old.x)*.008;pitch=Math.max(-1.52,Math.min(1.52,pitch+(p.y-old.y)*.008));}dirty=true;draw();});
function end(e){const o=pointers.get(e.pointerId);if(!o)return;pointers.delete(e.pointerId);gesture=null;if(o.movement>7||!loaded||!vp)return;const p=xy(e),r=canvas.getBoundingClientRect(),scaleX=canvas.width/r.width,scaleY=canvas.height/r.height;let best=null,dmin=900;
 for(const n of loaded.nodes){if(n.hidden)continue;const clip=proj(vp,[n.matrix[12],n.matrix[13],n.matrix[14]]);if(clip[3]<=0)continue;const x=(clip[0]/clip[3]*.5+.5)*canvas.width,y=(1-(clip[1]/clip[3]*.5+.5))*canvas.height;const d=(x-p.x*scaleX)**2+(y-p.y*scaleY)**2;if(d<dmin){dmin=d;best=n;}}
 if(best){select(best);note('Selecionado: '+best.name+'. Edite X/Y/Z para mover.')}else note('Nenhum objeto próximo do toque; aproxime a câmera.');}
canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',e=>pointers.delete(e.pointerId));canvas.addEventListener('wheel',e=>{e.preventDefault();distance*=Math.exp(e.deltaY*.001);dirty=true;draw();},{passive:false});
root.addEventListener('resize',()=>{dirty=true;draw()});
root.RiptideWorldV09={parse:readGLB,openFile:activateFile,loadArrayBuffer:load,getScene:()=>loaded,exportScene:saveScene,applyJSON};
})(typeof window!=='undefined'?window:null);