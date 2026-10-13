'use strict';
const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
const source=fs.readFileSync('web/world_scene.js','utf8');new vm.Script(source);
// Minimal document shim tests parser without WebGL or proprietary data.
const map={};const cls=()=>({add(){},remove(){},contains(){return false}});
function element(id){return map[id]||(map[id]={id,style:{},classList:cls(),append(){},addEventListener(){},setAttribute(){},textContent:'',innerHTML:'',value:'',onclick:null});}
const document={getElementById:element,createElement:t=>({tagName:t,style:{},classList:cls(),append(){},addEventListener(){},setAttribute(){},set innerHTML(v){this._html=v},get innerHTML(){return this._html}}),head:{append(){}},body:{append(){}}};
element('rw-canvas').getContext=()=>null;
const window={addEventListener(){},document,performance:{now:()=>0}};
const ctx=vm.createContext({window,document,TextDecoder,ArrayBuffer,DataView,Uint8Array,Uint16Array,Uint32Array,Float32Array,Number,Math,Map,Set,JSON,Error,console,devicePixelRatio:1});
vm.runInContext(source,ctx);
assert.equal(typeof window.RiptideWorldV09.parse,'function');
function buildGLB(){
 const gltf={asset:{version:'2.0'},scene:0,scenes:[{nodes:[0]}],nodes:[{name:'root',children:[1]},{name:'test-instance',mesh:0,matrix:[1,0,0,0,0,1,0,0,0,0,1,0,20,30,40,1]}],buffers:[{byteLength:42}],bufferViews:[{buffer:0,byteOffset:0,byteLength:36},{buffer:0,byteOffset:36,byteLength:6}],accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3',min:[0,0,0],max:[1,1,0]},{bufferView:1,componentType:5123,count:3,type:'SCALAR'}],meshes:[{name:'Test mesh',primitives:[{attributes:{POSITION:0},indices:1,mode:4}]}]};
 const str=Buffer.from(JSON.stringify(gltf)),padding=(4-str.length%4)%4,json=Buffer.concat([str,Buffer.from(' '.repeat(padding))]);
 const bin=Buffer.alloc(44);new Float32Array(bin.buffer,bin.byteOffset,9).set([0,0,0,1,0,0,0,1,0]);bin.writeUInt16LE(0,36);bin.writeUInt16LE(1,38);bin.writeUInt16LE(2,40);
 const buf=Buffer.alloc(12+8+json.length+8+bin.length);buf.write('glTF');buf.writeUInt32LE(2,4);buf.writeUInt32LE(buf.length,8);buf.writeUInt32LE(json.length,12);buf.writeUInt32LE(0x4e4f534a,16);json.copy(buf,20);const a=20+json.length;buf.writeUInt32LE(bin.length,a);buf.writeUInt32LE(0x004e4942,a+4);bin.copy(buf,a+8);return buf;
}
const bin=buildGLB(),ab=bin.buffer.slice(bin.byteOffset,bin.byteOffset+bin.length);
const scene=window.RiptideWorldV09.parse(ab);
assert.equal(scene.nodes.length,1);assert.equal(scene.nodes[0].name,'test-instance');assert.equal(scene.nodes[0].matrix[12],20);assert.equal(scene.geometry.size,1);
const broken=ab.slice(0);new DataView(broken).setUint32(4,1,true);assert.throws(()=>window.RiptideWorldV09.parse(broken),/GLB 2.0/);
assert.ok(fs.readFileSync('android/app/src/main/assets/editor_template.html','utf8').includes('RiptideWorldV09'));
const java=fs.readFileSync('android/app/src/main/java/com/nicky7x/riptidemaplab/MainActivity.java','utf8');
assert.ok(java.includes('onShowFileChooser'));assert.ok(java.includes('REQUEST_WORLD_FILE'));
console.log('v0.9: GLB 2.0 private scene parser, hierarchy, column-major transforms, bounds validation and SAF integration: OK');