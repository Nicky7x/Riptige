"""Read-only parser for Vector Unit static model geometry (verified subset).

Structure inferred from Riptide GP Renegade APF v6; not official docs.
Retains no game data. No reparsing or editing into the original game.
"""
from __future__ import annotations
import math
import struct
from dataclasses import dataclass

class VisualModelError(ValueError):
    pass

@dataclass
class VertexStream:
    stride: int
    positions: list[tuple[float,float,float]]
    indices: list[int]
    uvs: list[tuple[float,float]] | None = None

@dataclass
class VisualModel:
    materials: list[str]
    groups: list[dict]
    streams: list[VertexStream]
    trailing: bytes


def parse_static_model(data: bytes, max_vertices=150000, max_indices=900000, *, preview_first_lod=False) -> VisualModel:
    """Read a VuStaticModelAsset; position = first 3 little-endian f32 in each vertex.

    For every material group, returns (material, buffer, index_start, triangle_count).
    All absolute placements are part of the stored positions; templates may add transforms.
    """
    if len(data) < 64:
        raise VisualModelError('small model')
    # All tested models begin with three float LOD thresholds, followed by bbox and material table.
    lod=struct.unpack_from('<3f', data)
    if any(not math.isfinite(x) or x<0 or x>1e6 for x in lod):
        raise VisualModelError('unknown static header')
    p=46
    material_count=struct.unpack_from('<I',data,p)[0];p+=4
    if material_count>256:
        raise VisualModelError('too many materials')
    materials=[]
    for _ in range(material_count):
        end=data.find(b'\0',p,p+1025)
        if end<0:raise VisualModelError('missing material terminator')
        try:name=data[p:end].decode('utf-8')
        except UnicodeDecodeError as e:raise VisualModelError('non-utf8 material') from e
        if not name or any(ord(c)<32 for c in name):raise VisualModelError('bad material name')
        materials.append(name);p=end+1
    if p+4>len(data):raise VisualModelError('missing group table')
    n_groups=struct.unpack_from('<I',data,p)[0];p+=4
    if n_groups>8192 or p+48*n_groups+8>len(data):
        raise VisualModelError('bad group table')
    groups=[]
    for k in range(n_groups):
        stream,mat,start,triangles=struct.unpack_from('<4I',data,p)
        bound=struct.unpack_from('<8f',data,p+16)
        # Bounding floats at 4th and 8th positions sometimes contain sentinel garbage: ignore w.
        if mat>=material_count or triangles>max_indices//3:
            raise VisualModelError('group/material invalid')
        if any(not math.isfinite(v) or abs(v)>1e7 for v in [*bound[:3],*bound[4:7]]):
            raise VisualModelError('bounds invalid')
        groups.append(dict(material_index=mat,stream_index=stream,index_start=start,
                           triangles=triangles, bounds_min=list(bound[:3]),bounds_max=list(bound[4:7])))
        p+=48
    unknown,stream_count=struct.unpack_from('<2I',data,p);p+=8
    if unknown!=0 or not 1<=stream_count<=64:
        raise VisualModelError('unknown vertex stream table')
    streams=[]
    for k in range(stream_count):
        if p+8>len(data):raise VisualModelError('stream truncated')
        stride,size=struct.unpack_from('<2I',data,p);p+=8
        if stride<12 or stride>128 or size%stride or size>len(data)-p:
            raise VisualModelError('invalid vertex buffer')
        count=size//stride
        if count>max_vertices:raise VisualModelError('too many vertices')
        positions=[]
        # UV position agrees with Android VisualPreviewMeta. Unknown strides are
        # deliberately kept untextured instead of guessing vertex layouts.
        uv_at={20:12,24:16,28:16,32:20,36:24}.get(stride)
        uvs=[] if uv_at is not None else None
        for i in range(count):
            coords=struct.unpack_from('<3f',data,p+i*stride)
            if any(not math.isfinite(x) or abs(x)>1e7 for x in coords):
                raise VisualModelError('non-finite vertex')
            positions.append(coords)
            if uvs is not None:
                uv=struct.unpack_from('<2f',data,p+i*stride+uv_at)
                if not all(math.isfinite(a) and abs(a)<=1e6 for a in uv):
                    uv=(0.,0.)
                uvs.append(uv)
        p+=size
        if p+4>len(data):raise VisualModelError('index count missing')
        icount=struct.unpack_from('<I',data,p)[0];p+=4
        if icount>max_indices or icount%3 or icount*2>len(data)-p:
            raise VisualModelError('invalid index buffer')
        indices=list(struct.unpack_from('<'+str(icount)+'H',data,p)) if icount else []
        if indices and max(indices)>=count:raise VisualModelError('triangle references absent vertex')
        p+=2*icount
        streams.append(VertexStream(stride,positions,indices,uvs))
    for group in groups:
        si=group['stream_index']
        if si>=len(streams):raise VisualModelError('group references unknown stream')
        if group['index_start']+group['triangles']*3>len(streams[si].indices):
            raise VisualModelError('group indices outside vertex stream')
    trailing=data[p:]
    if len(trailing)>32:
        # Some verified static assets contain one or more additional LOD blocks.
        # The reader does not decode those blocks yet; ONLY for a private preview,
        # permit the validated first stream when trailing data starts with finite
        # position-like floats. Normal parsing remains strict by default.
        if not preview_first_lod or len(trailing)<64:
            raise VisualModelError('unexpected trailing bytes')
        floats=struct.unpack_from('<3f',trailing)
        if any(not math.isfinite(v) or abs(v)>1e7 for v in floats):
            raise VisualModelError('unrecognized extra LOD header')
    return VisualModel(materials,groups,streams,trailing)


def visual_to_collision_preview(model:VisualModel,max_vertices=65535,max_triangles=160000) -> bytes:
    """Produce synthetic (not original) collision-shaped preview with xyz f32 vertices.

    Preserves per-stream triangulation; material IDs and UV/color attributes are not exported.
    This is a preview format only, NEVER an in-game substitute.
    """
    n=sum(len(st.positions) for st in model.streams)
    total_tris=sum(len(st.indices)//3 for st in model.streams)
    if n>max_vertices or total_tris>max_triangles:raise VisualModelError('preview model too large')
    result=bytearray(4+16*n+4+6*total_tris)
    struct.pack_into('<I',result,0,n)
    at=4
    for st in model.streams:
        for x,y,z in st.positions:
            struct.pack_into('<4f',result,at,x,y,z,0.0);at+=16
    struct.pack_into('<I',result,at,3*total_tris);at+=4
    offset=0
    for st in model.streams:
        for index in st.indices:
            struct.pack_into('<H',result,at,index+offset);at+=2
        offset+=len(st.positions)
    assert at==len(result)
    return bytes(result)