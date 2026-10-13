#!/usr/bin/env python3
"""Audit original Renegade water references in APF v6 without distributing game resources.

Identifies named water assets referenced by each level template, their image formats,
and scene classes. Does NOT guess transforms or synthesize fake water geometry.

Usage: python tools/scene_dependencies.py /path/to/Assets.apf --out scene-audit.json
"""
from __future__ import annotations
import argparse
import contextlib
import shutil
import tempfile
import zipfile
import json
import lzma
import pathlib
import re
import struct
import zlib
from dataclasses import dataclass

LEVELS = ('CityA', 'CityB', 'FactoryA', 'FactoryB', 'MilitaryA', 'OldCityA', 'ParkA', 'ParkB', 'SpaceportA')
RESOURCE_CLASSES = ('VuStaticModelAsset','VuAnimatedModelAsset','VuLightMapAsset','VuCubeTextureAsset','VuTextureAsset','VuMaterialAsset','VuTemplateAsset')
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
    # Some original LZMA1-encoded prefab templates decode to exactly one extra
    # NUL byte; the APF index and embedded template header agree on the true
    # length. Safely remove ONLY that observed padding byte, never other data.
    if (entry.name.startswith('VuTemplateAsset/') and kind==2 and
        len(out)==entry.decoded_size+1 and out[-1:]==b'\x00' and
        len(out)>=8 and struct.unpack_from('<I',out,4)[0]==entry.decoded_size):
        out=out[:-1]
    if len(out)!=entry.decoded_size:raise ValueError('Tamanho do recurso divergente '+entry.name)
    return out


def water_map_header(f, entry):
    """Read only the first 70 decompressed bytes, even for very large maps.

    VuWaterMapAsset uses a different image header from VuTextureAsset.
    Width/height/format are at offsets 20,24,32 respectively.
    """
    if entry.decoded_size<70:raise ValueError('Cabeçalho de mapa truncado')
    f.seek(entry.offset)
    kind=entry.flags>>16
    if kind==0:
        data=f.read(70)
    else:
        raw=f.read(min(entry.stored_size,262144))
        if kind==1:
            data=zlib.decompressobj().decompress(raw,70)
        elif kind==2:
            if len(raw)<5:raise ValueError('LZMA curto')
            prop=raw[0]; dic=struct.unpack_from('<I',raw,1)[0]
            if not 4096<=dic<=134217728:raise ValueError('Dicionário LZMA inválido')
            filters=[dict(id=lzma.FILTER_LZMA1,dict_size=dic,lc=prop%9,lp=(prop//9)%5,pb=prop//45)]
            data=lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=filters).decompress(raw[5:],max_length=70)
        else:raise ValueError('Compressão desconhecida')
    if len(data)<70:raise ValueError('Cabeçalho incompleto')
    w,h=struct.unpack_from('<II',data,20)
    fmt=struct.unpack_from('<I',data,32)[0]
    if not (1<=w<=16384 and 1<=h<=16384):raise ValueError('Dimensões inválidas')
    return {'width':w,'height':h,'format':GL_FORMATS.get(fmt,hex(fmt))}

def scan_scene(f,entries):
    arenas=[]
    for arena in LEVELS:
        level='VuTemplateAsset/Levels/'+arena
        if level not in entries:continue
        data=payload(f,entries[level])
        scene_names=set(data.split(b'\x00'))
        original_dependencies={}
        for cls in RESOURCE_CLASSES:
            original_dependencies[cls]=sorted(
                key.partition('/')[2] for key in entries
                if key.startswith(cls+'/') and key.partition('/')[2].encode('utf-8') in scene_names)
        prefix='VuWaterMapAsset/'+arena+'/'
        water=[e for n,e in entries.items() if n.startswith(prefix)]
        matched=[];formats={};unreadable=[]
        for e in water:
            ref=e.name.removeprefix('VuWaterMapAsset/')
            # Strings in template asset are null terminated. Exact match prevents false positives.
            if b'\x00'+ref.encode()+b'\x00' in data:matched.append(ref)
            try:
                formats[ref]=water_map_header(f,e)
            except Exception as ex:unreadable.append({'resource':ref,'reason':str(ex)})
        classes=[cls.decode() for cls in TYPES if b'\x00'+cls+b'\x00' in data]
        arenas.append({'arena':arena,'scene_asset':level,'scene_bytes':len(data),
            'water_assets':len(water),'water_references':len(matched),
            'unlinked_water':[e.name.removeprefix('VuWaterMapAsset/') for e in water if e.name.removeprefix('VuWaterMapAsset/') not in matched],
            'entity_types':classes,'scene_resource_dependencies':original_dependencies,'map_formats':formats,'unreadable':unreadable,
            'render_status':'requires original water entity transforms and surface topology'})
    return {'format':'riptide-scene-dependency-audit-v1','arenas':arenas,
            'limitations':['The water maps are compressed image/data resources, not water surface meshes.',
            'This audit does not decode entity transforms, water vertices, waves or shader properties.',
            'Resource paths referenced indirectly by prefab templates are not covered by this top-level scene scan.',
            'No resource contents from the game are included in this JSON, only references and metadata.']}

@contextlib.contextmanager
def local_apf(source):
    """Read a local APF or XAPK, extracting to temporary files only.

    No user data goes to GitHub or to a server. Temporary copies are deleted.
    """
    if source.suffix.lower()=='.apf':
        with source.open('rb') as stream:yield stream
        return
    if source.suffix.lower() not in ('.xapk','.apk'):
        raise ValueError('Selecione arquivo .apf, .apk ou .xapk')
    with tempfile.TemporaryDirectory(prefix='riptide-scene-') as temp:
        archive=source
        if source.suffix.lower()=='.xapk':
            with zipfile.ZipFile(source) as xapk:
                if 'base.apk' not in xapk.namelist():raise ValueError('base.apk não encontrado no XAPK')
                archive=pathlib.Path(temp)/'base.apk'
                with xapk.open('base.apk') as inp,archive.open('wb') as out:
                    shutil.copyfileobj(inp,out)
        with zipfile.ZipFile(archive) as apk:
            if 'assets/Assets.apf' not in apk.namelist():raise ValueError('Assets.apf não encontrado no APK')
            apf=pathlib.Path(temp)/'Assets.apf'
            with apk.open('assets/Assets.apf') as inp,apf.open('wb') as out:
                shutil.copyfileobj(inp,out)
        with apf.open('rb') as stream:yield stream

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('apf',type=pathlib.Path,help='Seu Assets.apf, base.apk ou XAPK original')
    cli.add_argument('--out',type=pathlib.Path)
    args=cli.parse_args()
    with local_apf(args.apf) as stream: audit=scan_scene(stream,index_apf(stream))
    output=json.dumps(audit,indent=2,ensure_ascii=False)
    if args.out:args.out.write_text(output+'\n',encoding='utf-8')
    else:print(output)

if __name__=='__main__':main()