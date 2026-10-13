
/* Riptide Map Lab — CPU Canvas 3D fallback for browsers without WebGL.
   Renders actual collision geometry using perspective projection & depth ordering.
   Deliberately caps rendered triangles for mobile performance. */
(function(root){'use strict';
 root.RiptideSceneFallback=function(canvas){
  const $=id=>document.getElementById(id),ctx=canvas.getContext('2d');
  if(!ctx){$('scene3d-info').textContent='Não foi possível iniciar a visualização 3D.';return;}
  let meshes=[],map=new Map(),selected='',onlySelected=false,callbacks={},mode='orbit',yaw=-.85,elevation=.64,range=1000,target=[0,0,0],bounds=null;
  let facesDrawn=[],pending=false,dirty=true,drag=null;const points=new Map();let prevMulti=null;
  let player=false,playerPos=[0,0,3],playerYaw=0,playerPitch=0,stick=[0,0],lastFrame=0;
  function firstPerson(on){
    if(!on){player=false;stick=[0,0];mode='orbit';lastFrame=0;focus(true);return true;}
    if(!meshes.length)return false;
    const b=worldBounds(map.has(selected)?[map.get(selected)]:meshes);
    playerPos=[(b.lo[0]+b.hi[0])/2,(b.lo[1]+b.hi[1])/2,b.lo[2]+Math.min(3,Math.max(1.8,(b.hi[2]-b.lo[2])*.08))];
    playerYaw=yaw+Math.PI;playerPitch=0;stick=[0,0];mode='player';player=true;schedule();return true;
  }
  function tick(t){if(player){const dt=lastFrame?Math.min(.05,(t-lastFrame)/1000):0;lastFrame=t;
      const c=Math.cos(playerYaw),v=Math.sin(playerYaw),[sx,sy]=stick;
      if(Math.abs(sx)+Math.abs(sy)>.015){const span=bounds?Math.max(...bounds.hi.map((x,i)=>x-bounds.lo[i])):100;
      const speed=Math.max(3,Math.min(65,span*.035));
      playerPos[0]+=dt*speed*(-sy*c-sx*v);playerPos[1]+=dt*speed*(-sy*v+sx*c);schedule();}}
      else lastFrame=0;requestAnimationFrame(tick);}
  requestAnimationFrame(tick);
  const norm=v=>{const l=Math.hypot(...v)||1;return v.map(x=>x/l);}, dot=(a,b)=>a.reduce((v,n,i)=>v+n*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  function camera(){const c=Math.cos(elevation);return[target[0]+range*c*Math.cos(yaw),target[1]+range*c*Math.sin(yaw),target[2]+range*Math.sin(elevation)];}
  function basis(){const eye=player?playerPos:camera(),forward=player?norm([Math.cos(playerPitch)*Math.cos(playerYaw),Math.cos(playerPitch)*Math.sin(playerYaw),Math.sin(playerPitch)]):norm(target.map((x,i)=>x-eye[i])),right=norm(cross(forward,[0,0,1])),up=cross(right,forward);return{eye,forward,right,up};}
  function resize(){const r=canvas.getBoundingClientRect(),d=Math.min(window.devicePixelRatio||1,1.6),w=Math.max(1,Math.round(r.width*d)),h=Math.max(1,Math.round(r.height*d));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}ctx.setTransform(d,0,0,d,0,0);return[r.width,r.height];}
  function project(v,b,w,h){const rel=v.map((x,i)=>x-b.eye[i]),depth=dot(rel,b.forward);if(depth<.02)return null;const f=h*.95;return[w*.5+dot(rel,b.right)*f/depth,h*.5-dot(rel,b.up)*f/depth,depth];}
  function worldBounds(items){const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(const mesh of items){for(let k=0;k<3;k++){lo[k]=Math.min(lo[k],mesh.min[k]);hi[k]=Math.max(hi[k],mesh.max[k]);}}return{lo,hi};}
  function schedule(){dirty=true;if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;if(dirty)render();});}
  function make(key,source){const bin=root.RiptideCore.parse(source),verts=bin.vertices.map(v=>v.slice()),tri=[];
    for(let i=0;i<bin.indexCount;i+=3){const a=root.RiptideCore.getIndex(bin,i),b=root.RiptideCore.getIndex(bin,i+1),c=root.RiptideCore.getIndex(bin,i+2);tri.push([a,b,c]);}
    return{key,verts,tri,min:bin.min,max:bin.max,shift:[0,0,0]};}
  function focus(full){const arr=full?meshes:(map.has(selected)?[map.get(selected)]:meshes);if(!arr.length)return;const b=worldBounds(arr);
    target=b.lo.map((x,i)=>(x+b.hi[i])/2);range=Math.max(3,Math.hypot(...b.hi.map((v,i)=>v-b.lo[i]))*Math.max(1.3,1.18/Math.max(.48,canvas.clientWidth/Math.max(1,canvas.clientHeight))));schedule();}
  function drawLine(a,b,col){if(!a||!b)return;ctx.strokeStyle=col;ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke();}
  function render(){dirty=false;const[w,h]=resize();ctx.fillStyle='#0c1828';ctx.fillRect(0,0,w,h);
    const b=basis();if(!meshes.length){ctx.fillStyle='#a0bbce';ctx.textAlign='center';ctx.font='13px sans-serif';ctx.fillText('Selecione uma arena',w/2,h/2);return;}
    if($('scene3d-grid').checked && bounds){ctx.lineWidth=.8;const stride=Math.pow(10,Math.floor(Math.log10(Math.max(20,bounds.hi[1]-bounds.lo[1])/12))),z=bounds.lo[2]-3;
      for(let x=Math.floor(bounds.lo[0]/stride)*stride;x<=bounds.hi[0]+stride;x+=stride)drawLine(project([x,bounds.lo[1],z],b,w,h),project([x,bounds.hi[1],z],b,w,h),'#243f53');
      for(let y=Math.floor(bounds.lo[1]/stride)*stride;y<=bounds.hi[1]+stride;y+=stride)drawLine(project([bounds.lo[0],y,z],b,w,h),project([bounds.hi[0],y,z],b,w,h),'#243f53');}
    facesDrawn=[];const visible=onlySelected&&map.has(selected)?[map.get(selected)]:meshes;const total=visible.reduce((n,m)=>n+m.tri.length,0),step=Math.max(1,Math.ceil(total/9000));
    for(const mesh of visible){const vertices=mesh.verts.map(v=>project(v.map((x,i)=>x+mesh.shift[i]),b,w,h));
      for(let i=0;i<mesh.tri.length;i+=step){const p=mesh.tri[i],q=vertices[p[0]],r=vertices[p[1]],s=vertices[p[2]];if(!q||!r||!s)continue;
        const cr=(r[0]-q[0])*(s[1]-q[1])-(r[1]-q[1])*(s[0]-q[0]);if(Math.abs(cr)<.15)continue;
        const depth=(q[2]+r[2]+s[2])/3,shade=.55+.45*Math.abs(cr)/Math.max(1,Math.hypot(r[0]-q[0],r[1]-q[1])*Math.hypot(s[0]-q[0],s[1]-q[1]));
        facesDrawn.push({key:mesh.key,pts:[q,r,s],depth,shade});
      }}
    facesDrawn.sort((a,b)=>b.depth-a.depth);
    ctx.lineWidth=.6;
    for(const f of facesDrawn){ctx.beginPath();ctx.moveTo(f.pts[0][0],f.pts[0][1]);ctx.lineTo(f.pts[1][0],f.pts[1][1]);ctx.lineTo(f.pts[2][0],f.pts[2][1]);ctx.closePath();
      const s=f.shade;ctx.fillStyle=f.key===selected?`rgba(${Math.round(20*s)},${Math.round(212*s)},${Math.round(176*s)},.90)`:`rgba(${Math.round(39*s)},${Math.round(125*s)},${Math.round(159*s)},.90)`;ctx.fill();
      if(f.key===selected&&$('scene3d-wire').checked){ctx.strokeStyle='#b3eced';ctx.stroke();}
    }
    ctx.textAlign='left';ctx.fillStyle='#9bb3c8';ctx.font='11px system-ui';ctx.fillText('Visualização 3D em modo compatível · '+facesDrawn.length+' triângulos exibidos',10,h-10);
  }
  function pick(x,y){for(let i=facesDrawn.length-1;i>=0;i--){const f=facesDrawn[i],p=f.pts,a=p[0],b=p[1],c=p[2];const d=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);if(!d)continue;
      const u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/d,v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/d;
      if(u>=0&&v>=0&&u+v<=1)return f.key;
    }return null;}
  function translate(dx,dy){const h=canvas.getBoundingClientRect().height||1,scale=2*range*Math.tan(Math.PI/6)/h;
    return[-Math.sin(yaw)*dx*scale+Math.cos(yaw)*dy*scale,Math.cos(yaw)*dx*scale+Math.sin(yaw)*dy*scale,0];}
  function xy(e){const r=canvas.getBoundingClientRect();return{x:e.clientX-r.left,y:e.clientY-r.top};}
  function multi(){const a=[...points.values()];if(a.length<2)return null;return{cx:(a[0].x+a[1].x)/2,cy:(a[0].y+a[1].y)/2,dist:Math.hypot(a[0].x-a[1].x,a[0].y-a[1].y)};}
  canvas.addEventListener('pointerdown',e=>{e.preventDefault();canvas.setPointerCapture(e.pointerId);const p=xy(e);points.set(e.pointerId,{...p,travel:0});prevMulti=multi();
    if(points.size>1){drag=null;return;}if(player)return;if(mode==='move'&&selected&&pick(p.x,p.y)===selected)drag={key:selected,delta:[0,0,0],x:p.x,y:p.y};});
  canvas.addEventListener('pointermove',e=>{const old=points.get(e.pointerId);if(!old)return;e.preventDefault();const p=xy(e);p.travel=old.travel+Math.hypot(p.x-old.x,p.y-old.y);points.set(e.pointerId,p);
    if(player){playerYaw+=(p.x-old.x)*.005;playerPitch=Math.max(-1.45,Math.min(1.45,playerPitch-(p.y-old.y)*.005));schedule();return;}
    if(points.size>1){const m=multi();if(prevMulti){range=Math.max(3,range*prevMulti.dist/Math.max(1,m.dist));const d=translate(prevMulti.cx-m.cx,m.cy-prevMulti.cy);target=target.map((x,i)=>x+d[i]);}prevMulti=m;drag=null;
    }else if(drag){const d=translate(p.x-drag.x,drag.y-p.y);drag.x=p.x;drag.y=p.y;drag.delta=drag.delta.map((x,i)=>x+d[i]);map.get(selected).shift=drag.delta.slice();
    }else{yaw+=(p.x-old.x)*.008;elevation=Math.min(1.45,Math.max(-1.42,elevation+(p.y-old.y)*.008));}schedule();});
  function done(e){const state=points.get(e.pointerId);if(!state)return;points.delete(e.pointerId);prevMulti=multi();
    if(player){schedule();return;}
    if(drag){const ob=map.get(drag.key),delta=drag.delta;ob.shift=[0,0,0];drag=null;if(Math.hypot(...delta)>0.0001)callbacks.onMove?.(ob.key,delta);
    }else if(state.travel<9&&mode==='orbit'){const hit=pick(...Object.values(xy(e)));if(hit){selected=hit;updateInfo();callbacks.onSelect?.(hit);}}schedule();}
  canvas.addEventListener('pointerup',done);canvas.addEventListener('pointercancel',done);
  canvas.addEventListener('wheel',e=>{e.preventDefault();range=Math.max(3,range*Math.exp(e.deltaY*.001));schedule();},{passive:false});
  function updateInfo(){const m=map.get(selected);$('scene3d-info').textContent=m?'Selecionado: '+m.key+' · '+m.verts.length+' vértices de colisão.':'Toque em uma estrutura para selecionar um trecho.';schedule();}
  const api={
    on(cb){callbacks=cb||{};},
    async loadArena(records){meshes=[];map.clear();const bad=[];for(const x of records){try{const v=make(x.key,x.data);meshes.push(v);map.set(x.key,v);}catch(e){bad.push(x.key+': '+e.message);}}
      bounds=meshes.length?worldBounds(meshes):null;if(meshes.length)focus(true);selected='';updateInfo();if(player)firstPerson(true);return bad;},
    select(k){selected=k;updateInfo();},
    update(key,bytes){if(!map.has(key))return;const m=make(key,bytes);const i=meshes.indexOf(map.get(key));meshes[i]=m;map.set(key,m);schedule();},
    setMode(s){if(player)firstPerson(false);mode=s==='move'?'move':'orbit';},
    setPlayerMode:firstPerson,isPlayer(){return player;},setJoystick(x,y){stick=[Math.max(-1,Math.min(1,Number(x)||0)),Math.max(-1,Math.min(1,Number(y)||0))];},
    focusAll(){focus(true);},focusSelected(){focus(false);},getCount(){return meshes.length;},getVisibleCount(){return onlySelected&&map.has(selected)?1:meshes.length;}
  };root.RiptideScene3D=api;
  $('scene3d-orbit').addEventListener('click',()=>{mode='orbit';$('scene3d-orbit').classList.add('primary');$('scene3d-move').classList.remove('primary');});
  $('scene3d-move').addEventListener('click',()=>{mode='move';$('scene3d-move').classList.add('primary');$('scene3d-orbit').classList.remove('primary');});
  $('scene3d-focus').addEventListener('click',()=>focus(false));$('scene3d-all').addEventListener('click',()=>{onlySelected=false;$('scene3d-show-all').checked=true;focus(true);});
  $('scene3d-show-all').addEventListener('change',e=>{onlySelected=!e.target.checked;schedule();});
  $('scene3d-wire').addEventListener('change',schedule);$('scene3d-grid').addEventListener('change',schedule);window.addEventListener('resize',schedule);
  updateInfo();schedule();
 };
})(typeof window!=='undefined'?window:null);
