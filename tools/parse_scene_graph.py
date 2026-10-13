#!/usr/bin/env python3
"""Parse original Riptide Renegade APF v6 template scene graph (read-only).

Discovers field labels using FNV-1a64 over the trailing string table; parses
little-endian typed values with relative offsets. Entity transforms are LOCAL
unless a caller explicitly composes parent transforms. This is not a complete
scene renderer or a game patcher, and never sends game data over a network.

Usage: python tools/parse_scene_graph.py original.xapk --arena CityB --out private-cityb.json
"""
from __future__ import annotations
import argparse
import json
import math
import pathlib
import re
import struct
from collections import Counter
from scene_dependencies import LEVELS, index_apf, local_apf, payload

class SceneFormatError(ValueError):
    pass


def fnv1a64(text: str) -> int:
    value = 0xCBF29CE484222325
    for b in text.encode('utf-8'):
        value = ((value ^ b) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return value


class TemplateReader:
    """Decode strictly typed recursive variant blobs; no executing game code."""
    MAX_NODES = 250_000
    MAX_ARRAY = 80_000
    MAX_DEPTH = 90
    MAX_STRING = 8192

    def __init__(self, data: bytes):
        if len(data) < 24 or struct.unpack_from('<I', data)[0] != 1:
            raise SceneFormatError('Unexpected scene magic/version')
        if struct.unpack_from('<I', data, 4)[0] != len(data):
            raise SceneFormatError('Scene byte-size mismatch')
        self.data = data
        self.names: dict[int, str] = {}
        self.values: dict[int, object] = {}
        self.unresolved: set[int] = set()
        self._active: set[int] = set()
        # Reverse symbols to hashes, rather than hard-coding unstable field IDs.
        # Real files place the null-terminated symbol table after entity records.
        suffix = data[max(8, len(data)-min(500_000, max(120_000, len(data)//3))):]
        for candidate in re.findall(rb'[\x20-\x7e]{1,350}\x00', suffix):
            label = candidate[:-1].decode('ascii')
            self.names[fnv1a64(label)] = label

    def unpack(self, off: int, depth: int=0):
        d = self.data
        if off in self.values:
            return self.values[off]
        if off < 8 or off+8 > len(d) or depth > self.MAX_DEPTH:
            raise SceneFormatError('Invalid node offset or recursion depth')
        if len(self.values) >= self.MAX_NODES or off in self._active:
            raise SceneFormatError('Node count exceeded or cyclic reference')
        self._active.add(off)
        try:
            tag, num = struct.unpack_from('<II', d, off)
            if tag == 1:
                value = struct.unpack_from('<i', d, off+4)[0]
            elif tag == 2:
                value = struct.unpack_from('<f', d, off+4)[0]
                if not math.isfinite(value):
                    raise SceneFormatError(f'Unsupported float at {off:#x}: {value!r}')
            elif tag == 3:
                value = num
            elif tag == 4:
                # This is a signed offset RELATIVE TO THE NODE START,
                # *not* a length. For example 0x510+0x15969b points at
                # "VuAiWaypointEntity" in an observed original CityB template.
                relative = struct.unpack_from('<i', d, off+4)[0]
                at = off + relative
                if at < 8 or at >= len(d):
                    raise SceneFormatError('Invalid string pointer')
                end = d.find(b'\0', at, min(len(d), at+self.MAX_STRING))
                if end < 0:
                    raise SceneFormatError('Unterminated string')
                try: value = d[at:end].decode('utf-8')
                except UnicodeDecodeError as exc:
                    raise SceneFormatError('Unsupported string encoding') from exc
            elif tag == 5:
                if num > self.MAX_ARRAY or off+8+num*4 > len(d):
                    raise SceneFormatError('Bad array count')
                offsets = struct.unpack_from('<'+'I'*num, d, off+8) if num else ()
                if any(r < 8+num*4 or off+r >= len(d) for r in offsets):
                    raise SceneFormatError('Array element points outside record')
                value = [self.unpack(off+r, depth+1) for r in offsets]
            elif tag == 6:
                if num > self.MAX_ARRAY or off+8+num*16 > len(d):
                    raise SceneFormatError('Bad object property count')
                fields = []
                for i in range(num):
                    hashcode, _key_pointer, rel = struct.unpack_from('<QII', d, off+8+16*i)
                    if rel < 8+16*num or off+rel >= len(d):
                        raise SceneFormatError('Object property outside record')
                    label = self.names.get(hashcode)
                    if label is None:
                        self.unresolved.add(hashcode)
                        label = f'unknown_{hashcode:016x}'
                    fields.append((label, rel))
                if len({name for name,_ in fields}) != len(fields):
                    raise SceneFormatError('Duplicate property hash')
                value = {name: self.unpack(off+rel, depth+1) for name,rel in fields}
            else:
                raise SceneFormatError(f'Unknown variant tag {tag} at {off:#x}')
            self.values[off] = value
            return value
        finally:
            self._active.discard(off)

    def root(self) -> dict:
        graph = self.unpack(8)
        if not isinstance(graph, dict) or not isinstance(graph.get('RootEntity'), dict):
            raise SceneFormatError('Scene does not have expected RootEntity')
        return graph['RootEntity']


def _xyz(properties, key: str):
    values = properties.get(key) if isinstance(properties, dict) else None
    if not isinstance(values, dict):
        return None
    if not any(k in values for k in ('X','Y','Z')):
        return None
    # Only emit explicit values: missing components have engine defaults that
    # are not yet fully validated for every entity type.
    return {k: values[k] for k in ('X','Y','Z') if k in values and isinstance(values[k], (int,float))}


def extract_instances(root: dict, arena: str) -> dict:
    """Private read-only per-instance records, with LOCAL transforms."""
    result = []
    types = Counter()
    unresolved_transform = 0
    def visit(node, parent_parts, depth):
        nonlocal unresolved_transform
        if depth > 70:
            raise SceneFormatError('Entity hierarchy too deep')
        if not isinstance(node, dict): return
        kind = node.get('type')
        name = node.get('name')
        if not isinstance(kind, str): kind = 'unknown'
        if not isinstance(name, str): name = ''
        types[kind] += 1
        path = '/'.join(parent_parts+[name] if name else parent_parts)
        data = node.get('data') if isinstance(node.get('data'), dict) else {}
        components = data.get('Components') if isinstance(data.get('Components'), dict) else {}
        transform = components.get('VuTransformComponent') if isinstance(components.get('VuTransformComponent'), dict) else {}
        values = transform.get('Properties') if isinstance(transform.get('Properties'), dict) else {}
        pos = _xyz(values, 'Position')
        rot = _xyz(values, 'Rotation')
        scale = _xyz(values, 'Scale')
        own = data.get('Properties') if isinstance(data.get('Properties'), dict) else {}
        draw = components.get('Vu3dDrawStaticModelComponent') if isinstance(components.get('Vu3dDrawStaticModelComponent'), dict) else {}
        draw_props = draw.get('Properties') if isinstance(draw.get('Properties'), dict) else {}
        resource = draw_props.get('Model Asset') or own.get('Model Asset')
        if resource is None and kind.startswith('#'): resource = kind[1:]
        water_ref = own.get('WaterMap')
        is_water = kind in ('VuWaterSurfaceEntity','VuWaterRampEntity','VuInfiniteOceanWaveEntity')
        if is_water or resource or 'Vu3dDrawAnimatedModelComponent' in components:
            row = {'path':path, 'entity_type':kind,
                   'local_transform':{'position':pos,'rotation':rot,'scale':scale}}
            if resource:
                row['model_reference']=resource
                row['model_reference_type']='prefab_alias' if kind.startswith('#') and not (draw_props.get('Model Asset') or own.get('Model Asset')) else 'model_asset_reference'
            if is_water:
                row['water_map']=water_ref
                row['water_size']={k:own[k] for k in ('X Size','Y Size','Z Size') if k in own}
                row['water_attributes_present']=sorted(k for k in own if k not in ('WaterMap','X Size','Y Size','Z Size'))
            if pos is None:unresolved_transform+=1
            result.append(row)
        children = data.get('ChildEntities')
        if isinstance(children, list):
            for child in children:visit(child,parent_parts+[name] if name else parent_parts,depth+1)
    visit(root, [], 0)
    return {'format':'riptide-original-scene-instances-v1','arena':arena,
            'coordinate_space':'local to scene parent; hierarchy/world transform not yet composed',
            'entities_total':sum(types.values()),'entity_types':dict(types),
            'instances':result,'instances_without_explicit_position':unresolved_transform,
            'limitations':['No global transforms computed. Rotation units/axis conventions not yet verified.',
                           'Water plane is not rendered or inferred by this extractor.',
                           'Prefab references do not imply complete nested prefab expansion.']}


def summarize(scene: dict) -> dict:
    inst = scene['instances']
    water=[x for x in inst if 'water_size' in x]
    stat=[x for x in inst if 'model_reference' in x]
    return {'arena':scene['arena'],'entities':scene['entities_total'],
            'model_or_prefab_references':len(stat), 'water_entities':len(water),
            'water_with_position':sum(x['local_transform']['position'] is not None for x in water),
            'water_with_size':sum(bool(x['water_size']) for x in water),
            'water_with_map_reference':sum(isinstance(x.get('water_map'),str) for x in water),
            'instances_without_explicit_position':scene['instances_without_explicit_position']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=pathlib.Path,help='Private game APF/APK/XAPK')
    p.add_argument('--arena',choices=LEVELS,help='Analyze only one arena')
    p.add_argument('--out',type=pathlib.Path,help='Save local private instance data JSON')
    args=p.parse_args()
    records=[];reports=[]
    with local_apf(args.source) as stream:
        entries=index_apf(stream)
        for arena in ([args.arena] if args.arena else LEVELS):
            name=f'VuTemplateAsset/Levels/{arena}'
            if name not in entries:continue
            reader=TemplateReader(payload(stream,entries[name],max_bytes=40_000_000))
            scene=extract_instances(reader.root(),arena)
            scene['unresolved_field_hashes']=[f'{h:016x}' for h in sorted(reader.unresolved)]
            records.append(scene);reports.append(summarize(scene))
    if args.out:
        args.out.write_text(json.dumps({'format':'riptide-private-scene-hierarchy-v1','arenas':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Arquivo de instâncias privadas salvo em',args.out)
    print(json.dumps({'summary':reports,'all_fields_recognized':all(not s['unresolved_field_hashes'] for s in records)},ensure_ascii=False,indent=2))

if __name__=='__main__':main()