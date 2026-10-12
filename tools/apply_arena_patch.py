#!/usr/bin/env python3
"""Experimental APF v6 repacker for PRIVATE offline tests, no game binaries in Git.

Accepts patches emitted by the personal HTML editor. Changes vertex coordinates
inside selected collision assets and produces a new APF, leaving the input alone.

WARNING: integrity fields and runtime loading are not understood. The output
may NOT load inside Riptide GP: Renegade (including because of PairIP).
Do not distribute either APF. Never replace an installed game's files.

  python tools/apply_arena_patch.py --source original/Assets.apf \\
      --patch riptide-arenas-patch.json --out my-test/Assets.modified.apf
"""
from __future__ import annotations
import argparse, hashlib, json, lzma, shutil, struct, zlib
from pathlib import Path
from inspect_xapk import parse_apf_index, decompress_payload
from export_collision import decode_mesh_header

MAGIC='riptide-collision-multi-patch-v1'
PREFIX='VuCollisionMeshAsset/Level/'

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def codec_pack(original:bytes, flags:int, decoded:bytes)->bytes:
    kind=flags >> 16
    if kind == 1:return zlib.compress(decoded,6)
    if kind == 2:
        prop=original[0]; dictionary=struct.unpack_from('<I',original,1)[0]
        lc,lp,pb=prop%9,(prop//9)%5,prop//45
        flt=[{'id':lzma.FILTER_LZMA1,'dict_size':dictionary,'lc':lc,'lp':lp,'pb':pb}]
        return original[:5]+lzma.compress(decoded,format=lzma.FORMAT_RAW,filters=flt)
    raise ValueError('Unsupported APF compression codec '+str(kind))

def apply_asset_patch(payload:bytes,patch:dict)->tuple[bytes,int]:
    original=bytes(payload);out=bytearray(payload)
    meta=decode_mesh_header(original)
    if meta['vertices']!=patch['vertex_count'] or meta['triangles']!=patch['triangle_count']:
        raise ValueError('Patch metadata mismatch')
    seen=set()
    for op in patch['changes']:
        i=op['index']
        if not isinstance(i,int) or i<0 or i>=meta['vertices'] or i in seen:
            raise ValueError('Invalid/duplicate vertex index')
        seen.add(i)
        before=struct.unpack_from('<3f',original,4+16*i)
        if any(abs(before[k]-op['before'][k])>1e-5 for k in range(3)):
            raise ValueError('Original coordinates do not match patch at vertex '+str(i))
        coords=op['after']
        if len(coords)!=3 or any(not isinstance(n,(int,float)) or abs(n)>1e7 for n in coords):
            raise ValueError('Invalid target coordinates')
        struct.pack_into('<3f',out,4+16*i,*coords)
    if decode_mesh_header(bytes(out))['vertices']!=meta['vertices']:
        raise ValueError('Corrupted collision mesh')
    return bytes(out),len(seen)

def read_index_slots(idx:bytes,expected:int)->dict[str,int]:
    slots={};p=0
    for _ in range(expected):
        nul=idx.find(b'\0',p)
        if nul<0 or nul+21>len(idx):raise ValueError('Corrupted APF index')
        name=idx[p:nul].decode('utf8')
        if name in slots:raise ValueError('Duplicate APF index name')
        slots[name]=nul+1;p=nul+21
    if p!=len(idx):raise ValueError('Trailing unparsed index bytes')
    return slots

def repack(source:Path,patch_file:Path,out:Path)->dict:
    if source.resolve()==out.resolve():raise ValueError('Do not overwrite original APF')
    meta,entries=parse_apf_index(source)
    bundle=json.loads(patch_file.read_text('utf8'))
    if bundle.get('format')!=MAGIC:raise ValueError('Unsupported patch format')
    changes=bundle.get('changes',[])
    if not changes:raise ValueError('No patches to apply')
    by_name={e['name']:e for e in entries}
    patched={};sizes={}
    with source.open('rb') as f:
        for patch in changes:
            name=patch['resource_name']
            if not name.startswith(PREFIX) or name not in by_name or name in patched:
                raise ValueError('Invalid/duplicate resource: '+str(name))
            e=by_name[name]
            f.seek(e['offset']);packed=f.read(e['csize'])
            unpacked,_codec,_eof=decompress_payload(packed,e['usize'])
            decoded,count=apply_asset_patch(unpacked,patch)
            compressed=codec_pack(packed,e['flags'],decoded)
            verify,_,_=decompress_payload(compressed,len(decoded))
            if verify!=decoded:raise ValueError('Round-trip compression mismatch')
            patched[name]=compressed;sizes[name]={'vertices_modified':count,'previous_compressed_bytes':e['csize'],
                'new_compressed_bytes':len(compressed)}
        f.seek(meta['index_offset']);original_index=f.read(meta['index_size'])
    slots=read_index_slots(original_index,len(entries));index=bytearray(original_index)
    # Stable prefix until old index offset; append modified payloads, then updated index.
    # Unmodified payloads remain byte-identical and preserve their old offsets.
    new_index_offset=meta['index_offset']+sum(len(raw) for raw in patched.values())
    if new_index_offset>2**32-1:raise ValueError('APF v6 u32 offset overflow')
    out.parent.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as src,out.open('wb') as dest:
        left=meta['index_offset']
        while left:
            block=src.read(min(left,1024*1024))
            if not block:raise EOFError('Unexpected EOF')
            dest.write(block);left-=len(block)
        for name,compressed in patched.items():
            loc=dest.tell()
            dest.write(compressed)
            # Three fields rewritten: resource offset, compressed size and unchanged uncompressed size.
            struct.pack_into('<I',index,slots[name]+0,loc)
            struct.pack_into('<I',index,slots[name]+8,len(compressed))
        assert dest.tell()==new_index_offset
        dest.write(index)
        dest.seek(8);dest.write(struct.pack('<I',new_index_offset))
    next_meta,next_rows=parse_apf_index(out)
    if next_meta['resource_count']!=meta['resource_count'] or next_meta['index_size']!=meta['index_size']:
        raise ValueError('Repacked APF index not valid')
    with out.open('rb') as f:
        for e in next_rows:
            if e['name'] not in patched:continue
            f.seek(e['offset'])
            _raw,codec,_eof=decompress_payload(f.read(e['csize']),e['usize'])
    return {'source_sha256':sha256_file(source),'output_sha256':sha256_file(out),
        'original_bytes':source.stat().st_size,'output_bytes':out.stat().st_size,
        'resource_count_preserved':len(entries),'modified':sizes,
        'unvalidated_fields':['header_at_20','entry_unknown_u32','unused_index_flags'],
        'caveat':'Modified APF format is structurally parseable but in-game loading is NOT tested. PairIP might reject modifications.'}

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--source',type=Path,required=True)
    a.add_argument('--patch',type=Path,required=True)
    a.add_argument('--out',type=Path,required=True)
    args=a.parse_args()
    print(json.dumps(repack(args.source,args.patch,args.out),indent=2,ensure_ascii=False))