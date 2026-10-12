const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const web=path.resolve(__dirname,'../web');
const native=path.resolve(__dirname,'../android/app/src/main/assets/editor_template.html');
const webgl=fs.readFileSync(path.join(web,'scene3d.js'),'utf8');
const fallback=fs.readFileSync(path.join(web,'scene3d_fallback.js'),'utf8');
const loader=fs.readFileSync(path.join(web,'bundle_loader.js'),'utf8');
const html=fs.readFileSync(native,'utf8');
for (const script of [webgl,fallback]) {
 assert.match(script,/onlySelected=false/, 'arena must start with all meshes visible');
 assert.match(script,/getVisibleCount\(\)/, 'scene introspection absent');
 assert.match(script,/scene3d-show-all/, 'full arena toggle missing');
}
assert.match(loader,/scene\.focusAll\(\)/,'opening arena must frame all sections');
assert.match(loader,/records\.length\+' malhas reunidas/, 'assembled count should be shown');
assert.match(html,/id="scene3d-show-all" type="checkbox" checked/);
assert.match(html,/id="arena-summary"/);
assert.match(html,/__EMBEDDED_ASSETS__/);
assert.doesNotMatch(html,/VuCollisionMeshAsset\/Level\/CityA\/Zone01_col/, 'proprietary assets leaked into app template');
console.log('PASS: default full-arena composition and selection-mode controls');