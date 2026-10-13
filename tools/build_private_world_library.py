#!/usr/bin/env python3
"""Generate ONE private, offline Android world library for all nine Renegade arenas.

The ZIP contains original geometry, transforms and water metadata from the user's
own XAPK. It is strictly personal: NEVER upload it to this public repository.
Requires numpy and trimesh (pip install numpy trimesh).
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import tempfile
import zipfile

from scene_dependencies import LEVELS, index_apf, local_apf, water_map_header

FORMAT = 'riptide-private-world-library-v1'
# Source game uses XY horizontal / Z up. glTF uses Y up.
BASIS = (1., 0., 0., 0., 0., 0., -1., 0.,
         0., 1., 0., 0., 0., 0., 0., 1.)


def multiply(a, b):
    """Column-major 4x4 matrix multiplication."""
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4))
            for c in range(4) for r in range(4)]


def size_value(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    value = float(value)
    return value if math.isfinite(value) and 0 < value <= 1_000_000 else None


def water_records(world):
    """Preserve original positions and references, no invented water sizes.

    Sized surfaces are *approximate previews*: the real water tessellation,
    ramps, displacement maps and game shaders are not known.
    """
    items = []
    for entity in world['instances']:
        if entity.get('kind') != 'water':
            continue
        src = entity.get('world_matrix')
        if not isinstance(src, (list, tuple)) or len(src) != 16:
            continue
        if not all(isinstance(v, (float, int)) and math.isfinite(v)
                   and abs(v) < 1e9 for v in src):
            continue
        dims = entity.get('size') or {}
        x = size_value(dims.get('X Size'))
        y = size_value(dims.get('Y Size'))
        matrix = multiply(BASIS, src)
        # Preserve metadata even when surface dimensions are undecodable.
        items.append({
            'path': str(entity.get('path', ''))[:500],
            'kind': entity.get('type'),
            'waterMap': entity.get('water_map') if isinstance(entity.get('water_map'), str) else None,
            'matrix': matrix,
            'width': x,
            'length': y,
            'drawable': bool(x is not None and y is not None),
        })
    return items


def build_library(source: pathlib.Path, output: pathlib.Path, levels=LEVELS):
    # Delayed: documentation and lightweight unit tests work without numpy/trimesh.
    from export_world_glb import build_private_scene
    from resolve_world_instances import build as resolve

    source = source.resolve()
    output = output.resolve()
    if source == output:
        raise ValueError('Não sobrescreva o XAPK/APF original')
    if not source.is_file():
        raise FileNotFoundError(source)
    if output.suffix.lower() != '.zip':
        raise ValueError('Saída deve terminar em .zip')
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.name + '.partial')
    manifest = {'format': FORMAT, 'arenas': {},
                'note': 'Cenas privadas. Prévia de água aproximada e SEM shaders/ondas/refração originais.'}
    try:
        with tempfile.TemporaryDirectory(prefix='riptide-private-world-') as folder:
            with zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=1, allowZip64=True) as archive:
                for arena in levels:
                    if arena not in LEVELS:
                        raise ValueError('Arena não reconhecida: ' + arena)
                    glb = pathlib.Path(folder) / (arena + '.glb')
                    counts, _ = build_private_scene(source, arena, glb)
                    if not glb.is_file() or glb.stat().st_size < 28:
                        raise ValueError('GLB não foi gerado para ' + arena)
                    water = water_records(resolve(source, arena))
                    # Original water-map metadata is indexed by the *actual* WaterMap
                    # reference on each surface, not guessed by proximity or arena name.
                    water_maps = {}
                    with local_apf(source) as apf:
                        entries = index_apf(apf)
                        for ref in sorted({w['waterMap'] for w in water if w['waterMap']}):
                            key = 'VuWaterMapAsset/' + ref.removeprefix('VuWaterMapAsset/')
                            if key not in entries:
                                water_maps[ref] = {'status': 'missing'}
                                continue
                            try:
                                header = water_map_header(apf, entries[key])
                                water_maps[ref] = {'status': 'indexed', **header}
                            except (ValueError, OSError, EOFError) as exc:
                                water_maps[ref] = {'status': 'unsupported',
                                                   'reason': type(exc).__name__}
                    world_name = 'world/' + arena + '.glb'
                    water_name = 'water/' + arena + '.json'
                    archive.write(glb, world_name, compress_type=zipfile.ZIP_STORED)
                    archive.writestr(water_name, json.dumps({
                        'format': 'riptide-water-preview-v1',
                        'arena': arena, 'entities': water, 'waterMaps': water_maps
                    }, separators=(',', ':')))
                    manifest['arenas'][arena] = {
                        'glb': world_name,
                        'water': water_name,
                        'models': counts.get('exported_instances', 0),
                        'waterEntities': len(water),
                        'drawableWater': sum(bool(w['drawable']) for w in water),
                        'indexedWaterMaps': sum(m['status']=='indexed' for m in water_maps.values()),
                        'uvMaterialParts': counts.get('uv_material_parts', 0),
                    }
                archive.writestr('manifest.json', json.dumps(manifest, indent=2))
        tmp.replace(output)
    finally:
        if tmp.exists():
            tmp.unlink()
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=pathlib.Path, help='Sua cópia original .xapk, .apk ou .apf')
    p.add_argument('--output', type=pathlib.Path, required=True,
                   help='ZIP privado para importar no Android, NÃO publicar no GitHub')
    args = p.parse_args()
    result = build_library(args.source, args.output)
    print(json.dumps({'output': str(args.output), 'arenas': result['arenas']},
                     indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
