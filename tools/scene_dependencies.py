#!/usr/bin/env python3
"""Audit original Renegade water references in APF v6 without distributing game resources.

Identifies named water assets referenced by each level template, their image formats,
and scene classes. Does NOT guess transforms or synthesize fake water geometry.

Usage: python tools/scene_dependencies.py /path/to/Assets.apf --out scene-audit.json
"""
from __future__ import annotations
import argparse
import json
import lzma
import pathlib
import re
import struct
import zlib
from dataclasses import dataclass

LEVELS = ('CityA', 'CityB', 'FactoryA', 'FactoryB', 'MilitaryA', 'OldCityA', 'ParkA', 'ParkB', 'SpaceportA')
TYPES = (b'VuWaterSurfaceEntity', b'VuWaterRampEntity', b'VuInfiniteOceanWaveEntity', b'VuWaterTextureSettingsEntity')
GL_FORMATS = {0x83f1:'DXT1', 0x83f3:'DXT5', 0x8d64:'ETC1', 0x1908:'RGBA', 0x1909:'LUMINANCE'}

@dataclass(frozen=True)
class Entry:
    name: str
    offset: int
    decoded_size: int
    stored_size: int
    flags: int


def index_apf(f):
    f.seek(0)
    hdr=f.read(56)
    if len(hdr)!=56 or hdr[:4]!=b'FPUV':
        raise ValueError('APF sem assinatura FPUV')
    version,off,count,size=struct.unpack_from('<4I',hdr,4)
    f.seek(0,2); total=f.tell()
    if version!=6 or count>250000 or size>40_000_000 or off<56 or off+size>total:
        raise ValueError('Cabeçalho APF incorreto')
    f.seek(off); idx=f.read(size)
    p=0; entries={}
    for _ in range(count):
        end=idx.find(b'\0',p)
        if end<0 or end-p>4096 or end+21>len(idx):
            raise ValueError('Índice APF truncado')
        name=idx[p:end].decode('utf-8')
        ofs,usize,csize,_unknown,flags=struct.unpack_from('<5I',idx,end+1)
        if ofs<56 or ofs+csize>off:
            raise ValueError('Payload APF fora do limite: '+name)
        entries[name]=Entry(name,ofs,usize,csize,flags)
        p=end+21
    if p!=len(idx):raise ValueError('Sobra inesperada no índice')
    return entries


def payload(f,entry,max_bytes=15_000_000):
    if entry.decoded_size>max_bytes or entry.stored_size>max_bytes:
        raise ValueError('Recurso excedeu limite: '+entry.name)
    f.seek(entry.offset);raw=f.read(entry.stored_size)
    if len(raw)!=entry.stored_size:raise ValueError('Arquivo incompleto')
    kind=entry.flags>>16
    if kind==1:
        out=zlib.decompress(raw)
    elif kind==2:
        if len(raw)<5:raise ValueError('LZMA incompleto')
        prop=raw[0]; dic=struct.unpack_from('<I',raw,1)[0]
        filters=[dict(id=lzma.FILTER_LZMA1,dict_size=dic,lc=prop%9,lp=(prop//9)%5,pb=prop//45)]
        out=lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=filters).decompress(raw[5:],max_length=max_bytes)
    elif kind==0:out=raw
    else:raise ValueError('Compressão não suportada')
    if len(out)!=entry.decoded_size:raise ValueError('Tamanho do recurso divergente '+entry.name)
    return out


def scan_scene(f,entries):
    arenas=[]
    for arena in LEVELS:
        level='VuTemplateAsset/Levels/'+arena
        if level not in entries:continue
        data=payload(f,entries[level])
        prefix='VuWaterMapAsset/'+arena+'/'
        water=[e for n,e in entries.items() if n.startswith(prefix)]
        matched=[];formats={};unreadable=[]
        for e in water:
            ref=e.name.removeprefix('VuWaterMapAsset/')
            # Strings in template asset are null terminated. Exact match prevents false positives.
            if b'\x00'+ref.encode()+b'\x00' in data:matched.append(ref)
            try:
                header=payload(f,e,max_bytes=1_000_000)
                if len(header)<70:raise ValueError('mapa curto')
                w,h,format_code=struct.unpack_from('<III',header,21)[0:2]+(struct.unpack_from('<I',header,33)[0],)
                formats[ref]={'width':w,'height':h,'format':GL_FORMATS.get(format_code,hex(format_code))}
            except Exception as ex:unreadable.append({'resource':ref,'reason':str(ex)})
        classes=[cls.decode() for cls in TYPES if b'\x00'+cls+b'\x00' in data]
        arenas.append({'arena':arena,'scene_asset':level,'scene_bytes':len(data),
            'water_assets':len(water),'water_references':len(matched),
            'unlinked_water':[e.name.removeprefix('VuWaterMapAsset/') for e in water if e.name.removeprefix('VuWaterMapAsset/') not in matched],
            'entity_types':classes,'map_formats':formats,'unreadable':unreadable,
            'render_status':'requires original water entity transforms and surface topology'})
    return {'format':'riptide-scene-dependency-audit-v1','arenas':arenas,
            'limitations':['The water maps are compressed image/data resources, not water surface meshes.',
            'This audit does not decode entity transforms, water vertices, waves or shader properties.',
            'No resource contents from the game are included in this JSON, only references and metadata.']}

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('apf',type=pathlib.Path)
    cli.add_argument('--out',type=pathlib.Path)
    args=cli.parse_args()
    with args.apf.open('rb') as stream: audit=scan_scene(stream,index_apf(stream))
    output=json.dumps(audit,indent=2,ensure_ascii=False)
    if args.out:args.out.write_text(output+'\n',encoding='utf-8')
    else:print(output)

if __name__=='__main__':main()