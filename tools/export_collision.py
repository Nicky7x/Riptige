#!/usr/bin/env python3
"""Export private collision mesh resources from your XAPK/APK/APF for local Android GUI.
Never commit or redistribute the resulting .bin files.

  python tools/export_collision.py --source game.xapk --list --track CityA
  python tools/export_collision.py --source game.xapk --track CityA --all --out ~/storage/downloads/RiptideMapLab
  python tools/export_collision.py --source Assets.apf --name VuCollisionMeshAsset/Level/CityA/Zone01_col --one
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import json
import math
from pathlib import Path
import shutil
import struct
import tempfile
import zipfile
from inspect_xapk import decompress_payload, parse_apf_index

PREFIX='VuCollisionMeshAsset/Level/'
def decode_mesh_header(data:bytes)->dict:
    """Verified prefix: <u32 vertex_count> + 16-byte xyzw vertices + <u32 index_count> + u16 indices.
    Trailing unknown bytes are preserved on export, not interpreted.
    """
    if len(data)<8:raise ValueError('Malha muito curta')
    n=struct.unpack_from('<I',data)[0]
    if not 1<=n<=65536:raise ValueError('Contagem de vértices incompatível')
    pos=4+16*n
    if pos+4>len(data):raise ValueError('Tabela de vértices truncada')
    icount=struct.unpack_from('<I',data,pos)[0]
    end=pos+4+2*icount
    if icount>4_000_000 or icount%3 or end>len(data):
        raise ValueError('Índices triangulares incompatíveis')
    lo=[float('inf')]*3;hi=[float('-inf')]*3
    for i in range(n):
        vec=struct.unpack_from('<4f',data,4+16*i)
        if any(not math.isfinite(x) or abs(x)>1e7 for x in vec):
            raise ValueError(f'Coordenada inválida {i}')
        if vec[3]!=0:raise ValueError('Quarta componente inesperada')
        for j in range(3):
            lo[j]=min(lo[j],vec[j]);hi[j]=max(hi[j],vec[j])
    for (idx,) in struct.iter_unpack('<H',memoryview(data)[pos+4:end]):
        if idx>=n:raise ValueError('Triângulo aponta para vértice inexistente')
    return dict(vertices=n,triangles=icount//3,index_count=icount,unknown_tail_bytes=len(data)-end,bounds=dict(min=lo,max=hi),bytes=len(data))

@contextmanager
def local_apf(source:Path):
    if source.suffix.lower()=='.apf':
        yield source;return
    with tempfile.TemporaryDirectory(prefix='riptide-') as tmp:
        apf=Path(tmp)/'Assets.apf'
        if source.suffix.lower()=='.xapk':
            base=Path(tmp)/'base.apk'
            with zipfile.ZipFile(source) as z:
                with z.open('base.apk') as f,base.open('wb') as dst:shutil.copyfileobj(f,dst,1024*1024)
        elif source.suffix.lower()=='.apk':base=source
        else:raise ValueError('Forneça .xapk, .apk ou .apf')
        with zipfile.ZipFile(base) as z:
            with z.open('assets/Assets.apf') as f,apf.open('wb') as dst:shutil.copyfileobj(f,dst,1024*1024)
        yield apf

def export(source:Path,outdir:Path,track='',name='',all_meshes=False,list_only=False):
    result=[]
    with local_apf(source) as apf:
        _meta,rows=parse_apf_index(apf)
        rows=[r for r in rows if r['name'].startswith(PREFIX)
              and (not track or r['name'].startswith(PREFIX+track+'/'))
              and (not name or r['name']==name)]
        if name and len(rows)!=1:raise ValueError('Nome de recurso não encontrado: '+name)
        if not list_only and not (all_meshes or name):raise ValueError('Use --one --name ou --all')
        with apf.open('rb') as f:
            for r in rows:
                item=dict(name=r['name'],compressed_bytes=r['csize'],claimed_uncompressed=r['usize'])
                if not list_only:
                    try:
                        if r['usize']>64*1024*1024:raise ValueError('Recurso muito grande')
                        f.seek(r['offset'])
                        decoded,codec,eos=decompress_payload(f.read(r['csize']),r['usize'])
                        item['geometry']=decode_mesh_header(decoded)
                        # Generated path; never allow arbitrary archive paths to escape the output folder.
                        filename=r['name'][len(PREFIX):].replace('/','__')+'.bin'
                        dest=outdir/filename
                        dest.parent.mkdir(parents=True,exist_ok=True)
                        dest.write_bytes(decoded)
                        item.update(status='ok',saved_to=str(dest),codec=codec,eos=eos)
                    except (OSError,ValueError,EOFError,RuntimeError) as e:
                        item.update(status='unverified',reason=str(e))
                result.append(item)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--out',type=Path,default=Path('analysis/collision'))
    p.add_argument('--track',default='')
    p.add_argument('--name',default='')
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--list',action='store_true')
    g.add_argument('--all',action='store_true')
    g.add_argument('--one',action='store_true')
    args=p.parse_args()
    if args.one and not args.name:p.error('--one requires --name')
    result=export(args.source,args.out,args.track,args.name,args.all or args.one,args.list)
    for r in result:print(r['name'],r.get('status','listed'),r.get('reason',''),r.get('geometry',{}).get('vertices',''))
    if not args.list:
        args.out.mkdir(parents=True,exist_ok=True)
        (args.out/'manifest.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print('Saída local/privada:',args.out)
    print(sum(r.get('status')=='ok' for r in result),'/',len(result),'extraídos' if not args.list else 'listados')

if __name__=='__main__':main()
