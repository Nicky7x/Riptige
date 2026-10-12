/* Riptide Map Lab / Scene 3D alpha. WebGL1, no external libraries.
 * Displays actual collision geometry, not textured visual assets.
 * Touch: orbit (one finger), pan (two fingers), pinch zoom, select by tapping.
 * Move mode translates whole collision meshes on XY, preserving the source BIN.
 */
(function (root) {
  'use strict';
  const $=id=>document.getElementById(id);
  const canvas=$('arena3d');
  if(!canvas)return;
  const info=$('scene3d-info');
  const gl=canvas.getContext('webgl',{alpha:false,antialias:true,depth:true,preserveDrawingBuffer:false});
  if(!gl){if(root.RiptideSceneFallback)root.RiptideSceneFallback(canvas);else info.textContent='WebGL indisponível.';return;}
  const C={bg:[.039,.078,.133,1],other:[.19,.38,.50,1],chosen:[.14,.91,.77,1],wire:[.76,.94,.94,1]};
  const versus=`attribute vec3 pos;attribute vec3 normal;uniform mat4 viewProj;uniform vec3 shift;varying float diffuse;void main(){vec3 n=normalize(normal);diffuse=max(0.25,abs(dot(n,normalize(vec3(.4,-.3,.85)))));gl_Position=viewProj*vec4(pos+shift,1.);}`;
  const fs=`precision mediump float;uniform vec4 shade;varying float diffuse;void main(){gl_FragColor=vec4(shade.rgb*diffuse,shade.a);}`;
  const flatV=`attribute vec3 pos;uniform mat4 viewProj;uniform vec3 shift;void main(){gl_Position=viewProj*vec4(pos+shift,1.);}`;
  const flatF=`precision mediump float;uniform vec4 shade;void main(){gl_FragColor=shade;}`;
  function shader(type,src){const x=gl.createShader(type);gl.shaderSource(x,src);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x;}
  function program(v,f){const p=gl.createProgram();gl.attachShader(p,shader(gl.VERTEX_SHADER,v));gl.attachShader(p,shader(gl.FRAGMENT_SHADER,f));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));return {program:p,pos:gl.getAttribLocation(p,'pos'),normal:gl.getAttribLocation(p,'normal'),matrix:gl.getUniformLocation(p,'viewProj'),shift:gl.getUniformLocation(p,'shift'),shade:gl.getUniformLocation(p,'shade')};}
  const smooth=program(versus,fs), flat=program(flatV,flatF);
  let meshes=[],meshByKey=new Map(),selected='',onlySelected=false,pickMeshes=[],callbacks={},mode='orbit',yaw=-.85,elevation=.64,range=1200,target=[0,0,0],bounds=null,drag=null,dirty=true;
  let viewproj=new Float32Array(16),grid=null,pickFbo=null,pickTex=null,pickDepth=null,pickW=0,pickH=0;
  const MIN_DIST=2;
  function cross(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];}
  function dot(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
  function unit(v){const d=Math.hypot(...v)||1;return v.map(x=>x/d);}
  function look(eye,at){const z=unit(eye.map((v,i)=>v-at[i])),x=unit(cross([0,0,1],z)),y=cross(z,x);return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1]);}
  function perspective(aspect){const f=1/Math.tan(Math.PI/6),near=Math.max(.05,range/3000),far=Math.max(100,range*25);return new Float32Array([f/aspect,0,0,0,0,f,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0]);}
  function mul(a,b){const o=new Float32Array(16);for(let c=0;c<4;c++)for(let r=0;r<4;r++)for(let k=0;k<4;k++)o[c*4+r]+=a[k*4+r]*b[c*4+k];return o;}
  function camera(){const ce=Math.cos(elevation);return[target[0]+range*ce*Math.cos(yaw),target[1]+range*ce*Math.sin(yaw),target[2]+range*Math.sin(elevation)];}
  function uploadBuffer(data,itemSize,targetType=gl.ARRAY_BUFFER){const buf=gl.createBuffer();gl.bindBuffer(targetType,buf);gl.bufferData(targetType,data,gl.STATIC_DRAW);return buf;}
  function makeMesh(key,array){const m=root.RiptideCore.parse(array);const positions=new Float32Array(m.vertexCount*3),normals=new Float32Array(m.vertexCount*3),indices=new Uint16Array(m.indexCount);
    for(let i=0;i<m.vertexCount;i++)for(let k=0;k<3;k++)positions[i*3+k]=m.vertices[i][k];
    for(let i=0;i<m.indexCount;i++)indices[i]=root.RiptideCore.getIndex(m,i);
    for(let i=0;i<indices.length;i+=3){const a=indices[i]*3,b=indices[i+1]*3,c=indices[i+2]*3;
      const u=[positions[b]-positions[a],positions[b+1]-positions[a+1],positions[b+2]-positions[a+2]],v=[positions[c]-positions[a],positions[c+1]-positions[a+1],positions[c+2]-positions[a+2]];
      const n=cross(u,v);for(const j of [a,b,c])for(let k=0;k<3;k++)normals[j+k]+=n[k];}
    for(let i=0;i<normals.length;i+=3){const n=unit([normals[i],normals[i+1],normals[i+2]]);normals.set(n,i);}
    const lines=new Uint16Array(indices.length*2);
    for(let i=0;i<indices.length;i+=3){const p=i*2;lines.set([indices[i],indices[i+1],indices[i+1],indices[i+2],indices[i+2],indices[i]],p);}
    const b=m.min,hi=m.max;
    return {key,positions,normals,indices,lines,min:b,max:hi,shift:[0,0,0],gpu:{positions:uploadBuffer(positions),normals:uploadBuffer(normals),indices:uploadBuffer(indices,2,gl.ELEMENT_ARRAY_BUFFER),lines:uploadBuffer(lines,2,gl.ELEMENT_ARRAY_BUFFER)}};}
  function dispose(g){if(!g)return;for(const val of Object.values(g))gl.deleteBuffer(val);}
  function calcBounds(items){let lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(const m of items)for(let k=0;k<3;k++){lo[k]=Math.min(lo[k],m.min[k]);hi[k]=Math.max(hi[k],m.max[k]);}return{lo,hi};}
  function focus(full=false){const list=full?meshes:(meshByKey.get(selected)?[meshByKey.get(selected)]:meshes);if(!list.length)return;
    const b=calcBounds(list);target=b.lo.map((v,i)=>(v+b.hi[i])/2);const d=Math.hypot(...b.lo.map((v,i)=>b.hi[i]-v));range=Math.max(MIN_DIST,d*Math.max(1.3,1.18/Math.max(.48,canvas.clientWidth/Math.max(1,canvas.clientHeight))));dirty=true;draw();}
  function createGrid(){if(grid)gl.deleteBuffer(grid.buf);if(!bounds)return;
    const lo=bounds.lo,hi=bounds.hi,span=Math.max(30,hi[0]-lo[0],hi[1]-lo[1]),step=Math.pow(10,Math.floor(Math.log10(span/13)));
    const stride=span/step>45?step*5:step;
    const z=lo[2]-Math.max(.5,span*.002),pts=[];
    for(let x=Math.floor(lo[0]/stride)*stride;x<=hi[0]+stride;x+=stride)pts.push(x,lo[1],z,x,hi[1],z);
    for(let y=Math.floor(lo[1]/stride)*stride;y<=hi[1]+stride;y+=stride)pts.push(lo[0],y,z,hi[0],y,z);
    grid={buf:uploadBuffer(new Float32Array(pts)),count:pts.length/3};}
  function resize(){const d=Math.min(window.devicePixelRatio||1,1.8),rect=canvas.getBoundingClientRect();const w=Math.max(1,Math.floor(rect.width*d)),h=Math.max(1,Math.floor(rect.height*d));
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;pickW=0;dirty=true;}
    return[w,h];}
  function use(p){gl.useProgram(p.program);gl.uniformMatrix4fv(p.matrix,false,viewproj);if(p.pos>=0)gl.enableVertexAttribArray(p.pos);if(p.normal>=0)gl.enableVertexAttribArray(p.normal);}
  function drawMesh(m,p,color,kind){gl.uniform3fv(p.shift,m.shift);gl.uniform4fv(p.shade,color);
    gl.bindBuffer(gl.ARRAY_BUFFER,m.gpu.positions);gl.vertexAttribPointer(p.pos,3,gl.FLOAT,false,0,0);
    if(p.normal>=0){gl.bindBuffer(gl.ARRAY_BUFFER,m.gpu.normals);gl.vertexAttribPointer(p.normal,3,gl.FLOAT,false,0,0);}
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,kind===gl.LINES?m.gpu.lines:m.gpu.indices);
    gl.drawElements(kind,kind===gl.LINES?m.lines.length:m.indices.length,gl.UNSIGNED_SHORT,0);}
  function render(picking=false){const[w,h]=resize();gl.viewport(0,0,w,h);gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.disable(gl.CULL_FACE);gl.clearColor(...C.bg);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    viewproj=mul(perspective(w/h),look(camera(),target));
    if(!meshes.length)return;
    if(!picking&&grid&&$('scene3d-grid').checked){use(flat);gl.uniform3fv(flat.shift,[0,0,0]);gl.uniform4fv(flat.shade,[.21,.34,.44,.55]);gl.bindBuffer(gl.ARRAY_BUFFER,grid.buf);gl.vertexAttribPointer(flat.pos,3,gl.FLOAT,false,0,0);gl.drawArrays(gl.LINES,0,grid.count);}
    use(picking?flat:smooth);
    gl.enable(gl.POLYGON_OFFSET_FILL);gl.polygonOffset(1,1);
    const visible=onlySelected&&meshByKey.has(selected)?[meshByKey.get(selected)]:meshes;pickMeshes=visible;
    visible.forEach((m,i)=>{const c=picking?[(i+1&255)/255,((i+1)>>8&255)/255,((i+1)>>16&255)/255,1]:m.key===selected?C.chosen:C.other;drawMesh(m,picking?flat:smooth,c,gl.TRIANGLES);});
    gl.disable(gl.POLYGON_OFFSET_FILL);
    if(!picking&&$('scene3d-wire').checked){use(flat);visible.forEach(m=>{if(m.key===selected)drawMesh(m,flat,C.wire,gl.LINES);});}
  }
  function draw(){if(!dirty)return;dirty=false;render();}
  function picker(){const [w,h]=resize();if(pickFbo&&pickW===w&&pickH===h)return;
    if(pickFbo){gl.deleteFramebuffer(pickFbo);gl.deleteTexture(pickTex);gl.deleteRenderbuffer(pickDepth);}
    pickW=w;pickH=h;pickFbo=gl.createFramebuffer();pickTex=gl.createTexture();pickDepth=gl.createRenderbuffer();
    gl.bindTexture(gl.TEXTURE_2D,pickTex);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,w,h,0,gl.RGBA,gl.UNSIGNED_BYTE,null);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.bindRenderbuffer(gl.RENDERBUFFER,pickDepth);gl.renderbufferStorage(gl.RENDERBUFFER,gl.DEPTH_COMPONENT16,w,h);
    gl.bindFramebuffer(gl.FRAMEBUFFER,pickFbo);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,pickTex,0);gl.framebufferRenderbuffer(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.RENDERBUFFER,pickDepth);gl.bindFramebuffer(gl.FRAMEBUFFER,null);
  }
  function pick(x,y){if(!meshes.length)return null;picker();gl.bindFramebuffer(gl.FRAMEBUFFER,pickFbo);render(true);
    const rect=canvas.getBoundingClientRect(),px=Math.min(canvas.width-1,Math.max(0,Math.floor(x*canvas.width/rect.width))),py=Math.min(canvas.height-1,Math.max(0,Math.floor((rect.height-y)*canvas.height/rect.height)));
    const pixel=new Uint8Array(4);gl.readPixels(px,py,1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);gl.bindFramebuffer(gl.FRAMEBUFFER,null);
    const idx=(pixel[0]|pixel[1]<<8|pixel[2]<<16)-1;dirty=true;draw();return pickMeshes[idx]||null;}
  function selectedKey(key){selected=key;const m=meshByKey.get(key);info.textContent=m?('Selecionado: '+key+' · '+m.positions.length/3+' vértices. Visualização física, sem texturas.'):'Toque em uma estrutura para selecioná-la.';dirty=true;draw();}
  const pointers=new Map();let prevGesture=null;
  function coords(e){const r=canvas.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top};}
  function moveTo(dx,dy){const height=canvas.getBoundingClientRect().height,scale=2*range*Math.tan(Math.PI/6)/Math.max(1,height);const right=unit([-Math.sin(yaw),Math.cos(yaw),0]);
    const forward=[Math.cos(yaw),Math.sin(yaw),0];return[right[0]*dx*scale+forward[0]*dy*scale,right[1]*dx*scale+forward[1]*dy*scale,0];}
  function gesture(){const pts=[...pointers.values()];if(pts.length<2)return null;return {dist:Math.hypot(pts[1].x-pts[0].x,pts[1].y-pts[0].y),cx:(pts[0].x+pts[1].x)/2,cy:(pts[0].y+pts[1].y)/2};}
  canvas.addEventListener('pointerdown',e=>{e.preventDefault();canvas.setPointerCapture(e.pointerId);const p=coords(e);pointers.set(e.pointerId,{...p,startX:p.x,startY:p.y,travel:0});prevGesture=gesture();
    if(pointers.size!==1){drag=null;return;}
    const match=pick(p.x,p.y);
    if(mode==='move'&&match&&match.key===selected){drag={key:selected,delta:[0,0,0],x:p.x,y:p.y};}
  });
  canvas.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;e.preventDefault();const p=coords(e),old=pointers.get(e.pointerId);p.startX=old.startX;p.startY=old.startY;p.travel=old.travel+Math.hypot(p.x-old.x,p.y-old.y);pointers.set(e.pointerId,p);
    if(pointers.size>1){const g=gesture();if(prevGesture){range=Math.max(MIN_DIST,range*Math.exp((prevGesture.dist-g.dist)/Math.max(100,range*.05)));const delta=moveTo(prevGesture.cx-g.cx,g.cy-prevGesture.cy);target=target.map((x,i)=>x+delta[i]);}prevGesture=g;drag=null;
    }else if(drag){const d=moveTo(p.x-drag.x,drag.y-p.y);drag.x=p.x;drag.y=p.y;drag.delta=drag.delta.map((v,i)=>v+d[i]);meshByKey.get(drag.key).shift=drag.delta.slice();
    }else{yaw+=(p.x-old.x)*.008;elevation=Math.min(1.5,Math.max(-1.45,elevation+(p.y-old.y)*.008));}
    dirty=true;draw();
  });
  function release(e){const p=pointers.get(e.pointerId);if(!p)return;const current=coords(e);pointers.delete(e.pointerId);prevGesture=gesture();
    if(drag){const move=drag,ob=meshByKey.get(move.key);ob.shift=[0,0,0];drag=null;
      if(Math.hypot(...move.delta)>0.0001 && callbacks.onMove)callbacks.onMove(move.key,move.delta);
    }else if(p.travel<9&&mode==='orbit'){const hit=pick(current.x,current.y);if(hit){selectedKey(hit.key);callbacks.onSelect?.(hit.key);}}
    dirty=true;draw();}
  canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);
  canvas.addEventListener('wheel',e=>{e.preventDefault();range=Math.max(MIN_DIST,range*Math.exp(e.deltaY*.001));dirty=true;draw();},{passive:false});
  root.RiptideScene3D={
    on(cb){callbacks=cb||{};},
    async loadArena(records){meshes.forEach(m=>dispose(m.gpu));meshes=[];meshByKey.clear();
      const bad=[];for(const {key,data} of records){try{const m=makeMesh(key,data);meshes.push(m);meshByKey.set(key,m);}catch(e){bad.push(key+': '+e.message);}}
      bounds=meshes.length?calcBounds(meshes):null;createGrid();if(meshes.length)focus(true);selectedKey('');
      info.textContent=meshes.length+' trechos físicos carregados'+(bad.length?' · '+bad.length+' ignorados':'')+' · arraste para orbitar.';
      return bad;
    },
    select:selectedKey,
    update(key,bytes){const prev=meshByKey.get(key);if(!prev)return;const m=makeMesh(key,bytes);m.shift=prev.shift;dispose(prev.gpu);meshes[meshes.indexOf(prev)]=m;meshByKey.set(key,m);dirty=true;draw();},
    focusAll(){focus(true);},focusSelected(){focus(false);},
    setMode(next){mode=next==='move'?'move':'orbit';canvas.style.cursor=mode==='move'?'grab':'crosshair';},
    getCount(){return meshes.length;},
    getVisibleCount(){return onlySelected&&meshByKey.has(selected)?1:meshes.length;}
  };
  $('scene3d-orbit').addEventListener('click',()=>{root.RiptideScene3D.setMode('orbit');$('scene3d-orbit').classList.add('primary');$('scene3d-move').classList.remove('primary');});
  $('scene3d-move').addEventListener('click',()=>{root.RiptideScene3D.setMode('move');$('scene3d-move').classList.add('primary');$('scene3d-orbit').classList.remove('primary');});
  $('scene3d-focus').addEventListener('click',()=>focus(false));$('scene3d-all').addEventListener('click',()=>{onlySelected=false;$('scene3d-show-all').checked=true;focus(true);});
  $('scene3d-show-all').addEventListener('change',e=>{onlySelected=!e.target.checked;dirty=true;draw();});
  $('scene3d-wire').addEventListener('change',()=>{dirty=true;draw();});$('scene3d-grid').addEventListener('change',()=>{dirty=true;draw();});
  window.addEventListener('resize',()=>{dirty=true;draw();});dirty=true;draw();
})(typeof window!=='undefined'?window:null);