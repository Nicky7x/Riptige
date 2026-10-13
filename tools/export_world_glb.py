#!/usr/bin/env python3
"""Export personal APF-derived static scene to glTF .glb for transform inspection.

This is an offline preview, not an in-game scene or original shader/water renderer.
All game geometry and world transforms remain local, do not commit GLB to public GitHub.
"""
from __future__ import annotations
import argparse,collections,json,pathlib,sys
import numpy as np
import trimesh
from resolve_world_instances import SceneResolver
from scene_dependencies import index_apf,local_apf,payload
from parse_scene_graph import TemplateReader
from visual_models import parse_static_model,VisualModelError
import lzma,struct,zlib


def convert_model(payload_bytes, face_limit=1_000_000):
    model=parse_static_model(payload_bytes,preview_first_lod=True)
    vertices=[];faces=[];offset=0
    for stream in model.streams:
        vertices.extend(stream.positions)
        faces.extend(tuple(offset+stream.indices[i+j] for j in range(3)) for i in range(0,len(stream.indices),3))
        offset+=len(stream.positions)
    if len(faces)>face_limit:raise VisualModelError('Too many faces')
    if not faces:raise VisualModelError('Empty mesh')
    m=trimesh.Trimesh(vertices=vertices,faces=faces,process=False,validate=False)
    if not np.all(np.isfinite(m.vertices)) or m.is_empty:raise VisualModelError('Invalid geometry')
    return m


def preview_payload(f,entry):
    """Read-only preview: original LZMA static assets sometimes have one extra NUL pad.
    Refuse every other decompression discrepancy.
    """
    try:return payload(f,entry,max_bytes=40_000_000)
    except ValueError as e:
        if not str(e).startswith('Tamanho do recurso divergente VuStaticModelAsset/') or entry.flags>>16!=2:
            raise
        f.seek(entry.offset);raw=f.read(entry.stored_size)
        if len(raw)<5:raise
        prop=raw[0];dic=struct.unpack_from('<I',raw,1)[0]
        filters=[dict(id=lzma.FILTER_LZMA1,dict_size=dic,lc=prop%9,lp=(prop//9)%5,pb=prop//45)]
        out=lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=filters).decompress(raw[5:])
        if len(out)!=entry.decoded_size+1 or out[-1:]!=b'\0':raise
        return out[:-1]


def build_private_scene(source,arena,out_glb,limit=None):
    scene=trimesh.Scene()
    details=collections.Counter()
    with local_apf(source) as f:
        entries=index_apf(f)
        def read(name):return preview_payload(f,entries[name])
        resolver=SceneResolver(entries,read)
        root=TemplateReader(read('VuTemplateAsset/Levels/'+arena)).root()
        resolved=resolver.resolve(root,arena)
        assets={}
        for item in resolved['instances']:
            if item['kind']!='static':continue
            key=item['model']
            if key not in assets:
                ref='VuStaticModelAsset/'+key
                if ref not in entries:
                    assets[key]=None;details['unknown_model_refs']+=1
                else:
                    try:
                        assets[key]=convert_model(read(ref));details['parsed_models']+=1
                    except (ValueError,VisualModelError,IndexError) as e:
                        assets[key]=None;details['invalid_models']+=1
            mesh=assets[key]
            if mesh is None:details['omitted_instances']+=1;continue
            local=np.array(item['world_matrix'],dtype='float64').reshape(4,4,order='F')
            # glTF is Y-up. Transform root positions from original (X,Y,Z) to (X,Z,-Y) for portability.
            root_basis=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],dtype='float64')
            matrix=root_basis@local
            scene.add_geometry(mesh,geom_name=key,node_name=f'{details["exported_instances"]:06}:{item["path"]}',transform=matrix)
            details['exported_instances']+=1
            if limit and details['exported_instances']>=limit:break
    scene.export(out_glb,file_type='glb')
    return dict(details),resolved['summary']


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source',type=pathlib.Path)
    cli.add_argument('--arena',default='CityB')
    cli.add_argument('--output',required=True,type=pathlib.Path)
    cli.add_argument('--limit',type=int)
    a=cli.parse_args()
    result,stats=build_private_scene(a.source,a.arena,a.output,a.limit)
    print(json.dumps({'glb':str(a.output),'glb_bytes':a.output.stat().st_size,'export':result,'resolver':stats},indent=2))

if __name__=='__main__':main()