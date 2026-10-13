/* Riptide Map Lab v0.7 — mobile-first HUD, no dependencies or network. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const scene=window.RiptideScene3D;
const shell=document.createElement('div');shell.id='v07-shell';
shell.innerHTML=`
 <div id="v07-top"><span id="v07-brand">≋ RIPTIDE MAP LAB</span>
 <label>Arena <select id="v07-arena" aria-label="Escolha a arena"></select></label>
 <label id="v07-zone-label">Trecho <select id="v07-zone" aria-label="Escolha o trecho"></select></label>
 <span id="v07-mode" role="status">Prévia 3D</span></div>
 <div id="v07-main">
  <nav class="v07-rail" aria-label="Navegação">
   <button class="v07-tool" data-action="orbit" aria-label="Orbitar câmera"><span class="v07-icon">◉</span><small>Orbitar</small></button>
   <button class="v07-tool" data-action="focus" aria-label="Centralizar câmera"><span class="v07-icon">◎</span><small>Focar</small></button>
   <button class="v07-tool" data-action="move" aria-label="Mover trecho físico"><span class="v07-icon">✥</span><small>Mover</small></button>
   <button class="v07-tool" data-action="player" aria-label="Perspectiva do jogador"><span class="v07-icon">♟</span><small>Jogador</small></button>
  </nav>
  <section id="v07-viewport" aria-label="Arena 3D em tempo real">
    <span id="v07-player-label">PERSPECTIVA DO JOGADOR · CÂMERA LIVRE</span>
    <span id="v07-joystick-desc">Mover</span>
    <div id="v07-stick" aria-label="Joystick virtual de movimento"><div id="v07-stick-knob"></div></div>
    <div id="v07-hint" role="status"><b>Editor 3D</b><span>Arraste para girar a câmera. Toque numa ferramenta para ver sua função.</span></div>
  </section>
  <nav class="v07-rail" aria-label="Ferramentas">
   <button class="v07-tool" data-action="arena" aria-label="Mostrar arena inteira"><span class="v07-icon">▣</span><small>Arena</small></button>
   <button class="v07-tool" data-action="segment" aria-label="Mostrar trecho individual"><span class="v07-icon">▤</span><small>Trecho</small></button>
   <button class="v07-tool" data-action="visual" aria-label="Mostrar modelos visuais"><span class="v07-icon">◈</span><small>Visual</small></button>
   <button class="v07-tool" data-action="collision" aria-label="Mostrar colisões"><span class="v07-icon">◇</span><small>Colisão</small></button>
   <button class="v07-tool" data-action="save" aria-label="Exportar patch"><span class="v07-icon">⇩</span><small>Exportar</small></button>
   <button class="v07-tool" data-action="tools" aria-label="Abrir ferramentas avançadas"><span class="v07-icon">⚙</span><small>Mais</small></button>
  </nav>
 </div>
 <div id="v07-drawer" hidden><div id="v07-drawer-top"><b>Ferramentas avançadas</b><button id="v07-close">Fechar ✕</button></div></div>`;
document.body.append(shell);
const view=document.querySelector('.view3d'),sidebar=document.querySelector('.sidebar');
if(view)$('v07-viewport').prepend(view);
if(sidebar)$('v07-drawer').append(sidebar);
document.body.classList.add('v07-active');
const descriptions={
 orbit:['Orbitar câmera','Arraste sobre a pista para girar; com dois dedos, aproxime e desloque.'],
 focus:['Centralizar câmera','Enquadra o trecho selecionado ou a arena completa.'],
 move:['Mover trecho','Na camada de colisões, arraste o trecho selecionado para deslocá-lo.'],
 player:['Perspectiva do jogador','Joystick esquerdo para andar; arraste na cena para olhar ao redor. Sem física ou colisões de pilotagem.'],
 arena:['Arena inteira','Exibe todos os modelos/trechos da arena em uma cena 3D.'],
 segment:['Trecho individual','Exibe somente os modelos associados ao trecho escolhido.'],
 visual:['Geometria visual','Mostra os modelos 3D sem texturas; ainda não permite editá-los.'],
 collision:['Geometria de colisão','Mostra as malhas físicas que já podem ser editadas experimentalmente.'],
 save:['Exportar alterações','Gera o patch JSON com suas mudanças locais de colisão.'],
 tools:['Ferramentas avançadas','Abre as coordenadas, filtros, seleção e opção de importar outro XAPK.']
};
function hint(action){const [name,desc]=descriptions[action]||['Editor',action];$('v07-hint').innerHTML='';
 const title=document.createElement('b'),text=document.createElement('span');title.textContent=name;text.textContent=desc;$('v07-hint').append(title,text);
}
let player=false;
const buttons=[...shell.querySelectorAll('[data-action]')];
function update(){
 for(const b of buttons){const cmd=b.dataset.action;
  let active=cmd==='player'?player:cmd==='orbit'?!player&&$('scene3d-orbit').classList.contains('primary'):cmd==='move'?!player&&$('scene3d-move').classList.contains('primary'):cmd==='arena'?$('mode-arena').classList.contains('primary'):cmd==='segment'?$('mode-section').classList.contains('primary'):cmd==='visual'?$('layer-visual').classList.contains('primary'):cmd==='collision'?$('layer-collision').classList.contains('primary'):false;
  b.setAttribute('aria-pressed',String(active));
  b.disabled=cmd==='move'&&($('scene3d-move').disabled||player)||cmd==='visual'&&$('layer-visual').disabled;
 }
 const layer=$('layer-visual').classList.contains('primary')?'Visual 3D':'Colisão';
 $('v07-mode').textContent=player?'Câmera: Jogador':layer+' · '+($('mode-arena').classList.contains('primary')?'Arena inteira':'Trecho');
 $('v07-zone-label').style.display=$('mode-arena').classList.contains('primary')?'none':'flex';
}
function resetPlayer(){if(!player)return;player=false;scene?.setPlayerMode?.(false);scene?.setJoystick?.(0,0);shell.classList.remove('player');resetStick();}
function click(action){hint(action);
 if(action==='player'){
   if(!scene?.setPlayerMode){hint('Jogador indisponível: este renderizador não suporta a câmera.');return;}
   if(player)resetPlayer();else{
     if(!scene.setPlayerMode(true)){hint('Selecione uma arena antes de entrar na perspectiva do jogador.');return;}
     player=true;shell.classList.add('player');$('v07-drawer').hidden=true;
   }
 }else if(action==='orbit'||action==='move'){
   resetPlayer();$('scene3d-'+action).click();
 }else if(action==='focus'){
   if(player){hint('Saia da perspectiva do jogador para centralizar a câmera.');return;}
   ($('mode-arena').classList.contains('primary')?$('scene3d-all'):$('scene3d-focus')).click();
 }else if(action==='arena'||action==='segment'||action==='visual'||action==='collision'){
   if(player)resetPlayer();$('mode-'+action)?.click();
   if(action==='visual'||action==='collision')$('layer-'+action)?.click();
 }else if(action==='save'){$('bundle-export').click();}
 else if(action==='tools'){$('v07-drawer').hidden=!$('v07-drawer').hidden;}
 update();
}
for(const b of buttons){b.addEventListener('click',()=>click(b.dataset.action));}
$('v07-close').addEventListener('click',()=>{$('v07-drawer').hidden=true;hint('tools');});
// Keep landscape selectors synchronized with the original, tested loader.
function syncSelect(original,mirror){
 if(!original||!mirror)return;
 const options=Array.from(original.options).map(o=>new Option(o.textContent,o.value));
 mirror.replaceChildren(...options);mirror.value=original.value;
}
function syncAll(){syncSelect($('arena-select'),$('v07-arena'));syncSelect($('zone-select'),$('v07-zone'));update();}
$('v07-arena').addEventListener('change',()=>{$('arena-select').value=$('v07-arena').value;$('arena-select').dispatchEvent(new Event('change'));syncAll();});
$('v07-zone').addEventListener('change',()=>{$('zone-select').value=$('v07-zone').value;$('zone-select').dispatchEvent(new Event('change'));syncAll();});
for(const [original] of [['arena-select'],['zone-select']]){
 const target=$(original);new MutationObserver(syncAll).observe(target,{childList:true});
 target.addEventListener('change',()=>queueMicrotask(syncAll));
}
for(const id of ['mode-arena','mode-section','layer-visual','layer-collision'])$(id).addEventListener('click',()=>queueMicrotask(syncAll));
// Two-pointer control: joystick gets its own pointer and never triggers scene rotation.
const pad=$('v07-stick'),knob=$('v07-stick-knob');let stickPointer=null;
function resetStick(){stickPointer=null;knob.style.transform='translate(0px,0px)';scene?.setJoystick?.(0,0);}
function steer(e){const r=pad.getBoundingClientRect(),cx=r.left+r.width/2,cy=r.top+r.height/2;
 const radius=Math.max(18,(Math.min(r.width,r.height)-36)/2),dx=e.clientX-cx,dy=e.clientY-cy;
 const mag=Math.hypot(dx,dy),k=Math.min(1,radius/Math.max(.001,mag));
 const x=dx*k,y=dy*k;knob.style.transform='translate('+x+'px,'+y+'px)';scene?.setJoystick?.(x/radius,y/radius);
}
pad.addEventListener('pointerdown',e=>{e.preventDefault();if(!player||stickPointer!==null)return;stickPointer=e.pointerId;pad.setPointerCapture(e.pointerId);steer(e);});
pad.addEventListener('pointermove',e=>{if(stickPointer===e.pointerId){e.preventDefault();steer(e);}});
for(const event of ['pointerup','pointercancel','lostpointercapture'])pad.addEventListener(event,e=>{if(stickPointer===e.pointerId)resetStick();});
// Native reimport is available from the tools panel via AndroidBridge.
if(window.AndroidBridge&&window.AndroidBridge.pickXapk){const button=document.createElement('button');button.textContent='Importar outro XAPK';button.className='v07-reimport';
 button.addEventListener('click',()=>window.AndroidBridge.pickXapk());$('v07-drawer-top').append(button);}
syncAll();requestAnimationFrame(()=>{window.dispatchEvent(new Event('resize'));scene?.focusAll?.();});
window.RiptideMobileHUD={hint,refresh:syncAll};
})();