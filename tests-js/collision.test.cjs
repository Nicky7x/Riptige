const assert=require('node:assert/strict');
const core=require('../web/collision_core.js');
function fixture(){
 const n=3,indices=3,buffer=new ArrayBuffer(4+n*16+4+indices*2+7),v=new DataView(buffer);
 v.setUint32(0,n,true);
 [[1,2,3],[4,5,6],[7,8,9]].forEach((p,i)=>p.forEach((x,k)=>v.setFloat32(4+16*i+k*4,x,true)));
 v.setUint32(4+n*16,indices,true);
 [0,1,2].forEach((x,i)=>v.setUint16(4+n*16+4+i*2,x,true));
 return buffer;
}
const source=core.parse(fixture()),target=core.parse(fixture());
assert.equal(target.vertexCount,3);
assert.equal(target.triangleCount,1);
assert.equal(target.unknownBytes,7);
assert.deepEqual(target.vertices[0],[1,2,3]);
const snapshot=target.buffer.slice(0);
core.updateVertex(target,1,[12.5,30,6]);
assert.deepEqual(target.vertices[1],[12.5,30,6]);
assert.deepEqual(core.diff(source,target),[{vertex:1,before:[4,5,6],after:[12.5,30,6]}]);
const a=new Uint8Array(snapshot),b=new Uint8Array(target.buffer);
for(let i=0;i<a.length;i++)if(!(i>=20&&i<28))assert.equal(a[i],b[i],'unexpected byte '+i);
assert.throws(()=>core.updateVertex(target,1,[NaN,0,0]),/Coordenadas/);
assert.throws(()=>core.parse(new ArrayBuffer(3)),/pequeno/);
console.log('PASS: local collision mesh editing');
