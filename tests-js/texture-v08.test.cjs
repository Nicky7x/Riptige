'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8');
const html=read('android/app/src/main/assets/editor_template.html');
const webgl=read('web/scene3d.js'),loader=read('web/bundle_loader.js');
const java=read('android/app/src/main/java/com/nicky7x/riptidemaplab/ApfImporter.java');
const decoder=read('android/app/src/main/java/com/nicky7x/riptidemaplab/TexturePreview.java');
const uv=read('android/app/src/main/java/com/nicky7x/riptidemaplab/VisualPreviewMeta.java');
for(const token of ['setTextureCatalog','drawTextured','texture2D(image,vUV)','m.gpu.uv'])assert.ok(webgl.includes(token),token);
for(const token of ['__textures','__materials','getVisualUV','uvblob','setTextureCatalog'])assert.ok(loader.includes(token),token);
for(const token of ['makeVisualPreview','VisualPreviewMeta.parse','TexturePreview.png','arenas.put("__textures"','arenas.put("__materials"'])assert.ok(java.includes(token),token);
for(const token of ['decodeBC3','GL_DXT5','GL_ETC1','diffuseReference','ETC1.decodeImage'])assert.ok(decoder.includes(token),token);
assert.ok(uv.includes('uvOffset(stride)'));
for(const token of ['drawTextured','getVisualUV','__external_bundle','playerYaw-=','yaw-=(p.x-old.x)*.008','p.y-drag.y'])
 assert.ok(html.includes(token),'embedded '+token);
for(const token of ['web/scene3d.js','web/scene3d_fallback.js','web/bundle_loader.js','web/mobile_landscape.js'])
 new vm.Script(read(token));
let count=0;
for(let at=0;;){
 const a=html.indexOf('<script',at);if(a<0)break;
 const p=html.indexOf('>',a),b=html.indexOf('</script>',p);assert.ok(p>=0&&b>=0);
 const source=html.slice(p+1,b);
 if(source.trim()!=='__EMBEDDED_ASSETS__'){new vm.Script(source);count++;}
 at=b+9;
}
assert.ok(count>=6,'Scripts inline incompletos');
console.log('v0.8 material/texture import and WebGL UV script contracts: OK ('+count+' embedded scripts).');
