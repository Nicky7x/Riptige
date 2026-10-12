#!/usr/bin/env python3
"""Somente leitura: identifica recursos APF v6 dentro de XAPK Android.
Uso: python tools/inspect_xapk.py --xapk /caminho/arquivo.xapk --out analysis/report.json
Não repacota, altera ou distribui recursos do jogo.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import struct
import tempfile
import zipfile
import zlib

HEADER_SIZE = 60
RESOURCE_FIELDS = struct.Struct('<IIIII')
MAX_PROBE_SIZE = 64 * 1024 * 1024
TRACK_PREFIX = 'VuTemplateAsset/Levels/'
PROBES = (
    'Assets/AssetData', 'VuTemplateAsset/Levels/CityA',
    'VuWorkspaceAsset/Games/CityA', 'VuWaterMapAsset/CityA/WS01',
    'VuCollisionMeshAsset/Level/CityA/Zone01_col',
)
MARKERS = (b'VuAiWaypointEntity', b'CheckPoint Width', b'CheckPoint Height', b'Spline', b'Water')


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def parse_apf_index(path: Path) -> tuple[dict, list[dict]]:
    size = path.stat().st_size
    with path.open('rb') as src:
        header = src.read(HEADER_SIZE)
        if len(header) != HEADER_SIZE or header[:4] != b'FPUV':
            raise ValueError('Cabeçalho FPUV ausente ou incompleto')
        version, index_offset, count, index_size, unknown20 = struct.unpack_from('<5I', header, 4)
        if version != 6:
            raise ValueError(f'Apenas APF v6 verificado; encontrado {version}')
        if not (HEADER_SIZE <= index_offset <= size and index_size <= size - index_offset):
            raise ValueError('Índice fora dos limites')
        if count > 250_000 or index_size > 100_000_000:
            raise ValueError('Índice excessivo')
        src.seek(index_offset)
        index = src.read(index_size)
    pos, rows = 0, []
    for i in range(count):
        nul = index.find(b'\0', pos)
        if nul < 0:
            raise ValueError(f'Nome sem NUL na entrada {i}')
        name = index[pos:nul].decode('utf-8')
        pos = nul + 1
        if pos + RESOURCE_FIELDS.size > len(index):
            raise ValueError(f'Entrada truncada: {i}')
        off, usize, csize, unknown, flags = RESOURCE_FIELDS.unpack_from(index, pos)
        pos += RESOURCE_FIELDS.size
        if off < HEADER_SIZE or off + csize > index_offset:
            raise ValueError(f'Recurso fora dos limites: {name}')
        rows.append(dict(name=name, offset=off, usize=usize, csize=csize,
                         unknown_u32=unknown, flags=flags))
    if pos != len(index):
        raise ValueError(f'{len(index)-pos} bytes não interpretados no índice')
    return dict(magic='FPUV', version=version, file_size=size, index_offset=index_offset,
                resource_count=count, index_size=index_size,
                unknown_header_u32_at_20=unknown20,
                build_label=header[24:56].split(b'\0',1)[0].decode('ascii','replace')), rows


def decompress_payload(payload: bytes, expected_size: int) -> tuple[bytes,str,bool]:
    if expected_size < 0 or expected_size > MAX_PROBE_SIZE:
        raise ValueError('Recurso excede limite de sondagem')
    if payload[:2] in (b'\x78\x01', b'\x78\x5e', b'\x78\x9c', b'\x78\xda'):
        data = zlib.decompress(payload)
        codec, end = 'zlib', True
    elif len(payload) >= 5:
        prop = payload[0]
        lc, lp, pb = prop % 9, (prop // 9) % 5, prop // 45
        dictionary = int.from_bytes(payload[1:5], 'little')
        if lc + lp > 4 or pb > 4 or not (4096 <= dictionary <= 128*1024*1024):
            raise ValueError('Propriedades LZMA1 inválidas')
        d = lzma.LZMADecompressor(format=lzma.FORMAT_RAW,
            filters=[dict(id=lzma.FILTER_LZMA1, dict_size=dictionary,
                          lc=lc, lp=lp, pb=pb)])
        data = d.decompress(payload[5:], max_length=expected_size + 1)
        codec, end = 'LZMA1 raw / props 5 bytes', d.eof
    else:
        raise ValueError('Codec desconhecido')
    if len(data) != expected_size:
        raise ValueError(f'Tamanho decodificado {len(data)} != {expected_size}')
    return data, codec, end


def inspect(xapk: Path) -> dict:
    report = dict(schema_version=1, analysed_at=datetime.now(timezone.utc).isoformat(),
                  input_filename=xapk.name, source_sha256=sha256_path(xapk),
                  size_bytes=xapk.stat().st_size, mode='read-only')
    with zipfile.ZipFile(xapk) as package:
        report['xapk_files'] = [m.filename for m in package.infolist()]
        if 'base.apk' not in package.namelist():
            raise ValueError('Não encontrei base.apk no XAPK')
        with tempfile.TemporaryDirectory(prefix='apf-inspect-') as td:
            base = Path(td) / 'base.apk'
            with package.open('base.apk') as src, base.open('wb') as dst:
                shutil.copyfileobj(src, dst)
            with zipfile.ZipFile(base) as apk:
                if 'assets/Assets.apf' not in apk.namelist():
                    raise ValueError('Não encontrei assets/Assets.apf em base.apk')
                apf = Path(td) / 'Assets.apf'
                with apk.open('assets/Assets.apf') as src, apf.open('wb') as dst:
                    shutil.copyfileobj(src,dst)
            meta, rows = parse_apf_index(apf)
            meta['sha256'] = sha256_path(apf)
            meta['class_counts'] = dict(sorted(Counter(e['name'].split('/')[0] for e in rows).items()))
            report['apf'] = meta
            report['tracks'] = sorted({e['name'][len(TRACK_PREFIX):] for e in rows
                if e['name'].startswith(TRACK_PREFIX) and
                '/' not in e['name'][len(TRACK_PREFIX):]})
            by_name = {e['name']:e for e in rows}
            probes = []
            with apf.open('rb') as f:
                for name in PROBES:
                    e=by_name.get(name)
                    if e is None:
                        probes.append(dict(name=name,status='missing')); continue
                    f.seek(e['offset'])
                    data,codec,eos=decompress_payload(f.read(e['csize']),e['usize'])
                    probes.append(dict(name=name,status='ok',codec=codec,
                        usize=len(data),sha256=hashlib.sha256(data).hexdigest(),
                        eos=eos,marker_offsets={k.decode():data.find(k) for k in MARKERS}))
            report['probes'] = probes
            report['resources'] = rows
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--xapk',required=True,type=Path)
    p.add_argument('--out',default=Path('analysis/report.json'),type=Path)
    args=p.parse_args()
    result=inspect(args.xapk)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Recursos:',result['apf']['resource_count'])
    print('Níveis:',', '.join(result['tracks']))
    print('Relatório:',args.out)
