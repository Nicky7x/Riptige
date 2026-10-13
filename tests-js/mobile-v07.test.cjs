/* Static regression tests for the installable landscape HTML and first-person API. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const html=read('android/app/src/main/assets/editor_template.html');
const core=read('web/scene3d.js');
const fallback=read('web/scene3d_fallback.js');
const hud=read('web/mobile_landscape.js');
const css=read('web/mobile_landscape.css');
const manifest=read('android/app/src/main/AndroidManifest.xml');
assert.match(manifest,/screenOrientation="sensorLandscape"/);
for(const id of ['arena3d','mode-arena','mode-section','layer-visual','layer-collision','bundle-export','private-assets']){
  assert.ok(html.includes('id="'+id+'"'),'Missing '+id);
}
for(const expr of ['setPlayerMode','setJoystick','playerPos','requestAnimationFrame(frame)'])assert.ok(core.includes(expr),'WebGL missing '+expr);
for(const expr of ['setPlayerMode:firstPerson','setJoystick','requestAnimationFrame(tick)'])assert.ok(fallback.includes(expr),'Canvas missing '+expr);
for(const expr of ['v07-stick','data-action="player"','v07-arena','v07-hint','pickXapk'])assert.ok(hud.includes(expr),'HUD missing '+expr);
assert.ok(css.includes('#v07-viewport #arena3d'));
assert.ok(html.includes('await openSceneArena()'));
assert.ok(html.includes('AndroidBridge.editorReady'));
const scripts=[];
for(let start=0;;){
 const open=html.indexOf('<script',start);
 if(open<0)break;
 const body=html.indexOf('>',open),end=html.indexOf('</script>',body);
 if(body<0||end<0)throw Error('Invalid embedded script tags');
 scripts.push([null,html.slice(body+1,end)]);
 start=end+9;
}
assert.ok(scripts.length>=7,'Embedded scripts missing');
let validated=0;
for(const item of scripts){
 const src=item[1];
 if(src.trim()==='__EMBEDDED_ASSETS__')continue;
 new vm.Script(src);validated++;
}
for(const p of ['web/scene3d.js','web/scene3d_fallback.js','web/bundle_loader.js','web/mobile_landscape.js'])
 new vm.Script(read(p));
console.log('Landscape UI v0.7: '+validated+' embedded scripts compiled, key controls and Android orientation verified.');
