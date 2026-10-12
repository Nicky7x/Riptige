/* Riptide Map Lab — parses and patches local collision mesh files only.
   No proprietary bytes are distributed and no network is used. */
(function(root) {
  'use strict';
  function parse(buffer) {
    if (!(buffer instanceof ArrayBuffer)) throw new Error('Escolha um arquivo .bin');
    const view=new DataView(buffer);
    if (buffer.byteLength<12) throw new Error('Arquivo pequeno demais');
    const count=view.getUint32(0,true);
    if (count<1||count>65536) throw new Error('Quantidade de vértices incompatível: '+count);
    const offset=4+16*count;
    if(offset+4>buffer.byteLength) throw new Error('Tabela de vértices truncada');
    const icount=view.getUint32(offset,true), end=offset+4+2*icount;
    if(icount>4_000_000 || icount%3 || end>buffer.byteLength) throw new Error('Índices triangulares inválidos');
    const verts=new Array(count),min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
    for(let i=0;i<count;i++){
      const start=4+i*16,v=[];
      for(let a=0;a<4;a++)v.push(view.getFloat32(start+a*4,true));
      if(v.some(x=>!Number.isFinite(x)||Math.abs(x)>1e7))throw new Error('Coordenadas inválidas no vértice '+i);
      if(v[3]!==0)throw new Error('Quarta coordenada diferente de zero, formato desconhecido');
      verts[i]=v.slice(0,3);
      for(let a=0;a<3;a++){min[a]=Math.min(min[a],v[a]);max[a]=Math.max(max[a],v[a]);}
    }
    const indexOffset=offset+4;
    for(let i=0;i<icount;i++)
      if(view.getUint16(indexOffset+2*i,true)>=count)throw new Error('Índice de triângulo inválido em '+i);
    return {buffer,view,vertices:verts,vertexCount:count,indexCount:icount,triangleCount:icount/3,
      indexOffset,knownBytes:end,unknownBytes:buffer.byteLength-end,min,max};
  }
  function updateVertex(mesh,i,coords){
    if(!Number.isInteger(i)||i<0||i>=mesh.vertexCount)throw new Error('Índice de vértice inválido');
    if(!Array.isArray(coords)||coords.length!==3||coords.some(v=>!Number.isFinite(v)||Math.abs(v)>1e7))
      throw new Error('Coordenadas inválidas');
    for(let k=0;k<3;k++)mesh.view.setFloat32(4+i*16+4*k,coords[k],true);
    mesh.vertices[i]=[0,1,2].map(k=>mesh.view.getFloat32(4+i*16+4*k,true));
    return mesh.vertices[i].slice();
  }
  function getIndex(mesh,i){return mesh.view.getUint16(mesh.indexOffset+2*i,true);}
  function diff(before,after){
    if(before.vertexCount!==after.vertexCount)throw new Error('Topologias diferentes');
    return before.vertices.flatMap((v,i)=>v.some((x,k)=>x!==after.vertices[i][k])?
      [{vertex:i,before:v.slice(),after:after.vertices[i].slice()}]:[]);
  }
  const api={parse,updateVertex,getIndex,diff};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(root)root.RiptideCore=api;
})(typeof window!=='undefined'?window:null);
