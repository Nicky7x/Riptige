#!/usr/bin/env python3
"""Expand original APF scene/prefab hierarchy into *candidate* world-space render instances.

Does not redistribute original game data: detailed JSON stays in user-local output.
Euler/scale/override conventions are hypotheses until validated in-game.
"""
from __future__ import annotations
import argparse, collections, json, math, pathlib, sys
from dataclasses import dataclass
from typing import Any

try:
    from parse_scene_graph import TemplateReader, SceneFormatError
    from scene_dependencies import LEVELS, index_apf, local_apf, payload
except ModuleNotFoundError:
    sys.path.append(str(pathlib.Path(__file__).resolve().parent))
    from parse_scene_graph import TemplateReader, SceneFormatError
    from scene_dependencies import LEVELS, index_apf, local_apf, payload

IDENTITY = (1.,0.,0.,0., 0.,1.,0.,0., 0.,0.,1.,0., 0.,0.,0.,1.)
MAX_RECURSION=90
MAX_INSTANCES=120_000

class ResolveError(ValueError): pass


def mul(a, b):
    """Multiply two 4x4 column-major matrices."""
    return tuple(sum(a[k*4+r]*b[c*4+k] for k in range(4)) for c in range(4) for r in range(4))


def point(m, xyz):
    x,y,z=xyz
    return [sum(m[c*4+r]*v for c,v in enumerate((x,y,z,1.))) for r in range(3)]


def xyz(v,default):
    if not isinstance(v,dict):return tuple(float(x) for x in default)
    ans=[]
    for key,base in zip('XYZ',default):
        q=v.get(key,base)
        if not isinstance(q,(int,float)) or not math.isfinite(q):raise ResolveError('Invalid coordinate '+key)
        ans.append(float(q))
    return tuple(ans)


def transform(node):
    data=node.get('data') or {}
    comps=data.get('Components') or {}
    tc=comps.get('VuTransformComponent') or {}
    props=tc.get('Properties') or {}
    p=xyz(props.get('Position'),(0.,0.,0.))
    rx,ry,rz=xyz(props.get('Rotation'),(0.,0.,0.))
    sx,sy,sz=xyz(props.get('Scale'),(1.,1.,1.))
    if any(abs(v)>1e8 for v in p) or any(abs(v)>1e5 for v in (rx,ry,rz)) or any(abs(v)>1e6 for v in (sx,sy,sz)):
        raise ResolveError('Transform outside preview limits')
    # Working convention: degrees, local Euler order ZYX (apply Rx then Ry then Rz), and T*R*S.
    x,y,z=map(math.radians,(rx,ry,rz))
    cx,sxang=math.cos(x),math.sin(x)
    cy,syang=math.cos(y),math.sin(y)
    cz,szang=math.cos(z),math.sin(z)
    # Rz @ Ry @ Rx as column-major columns.
    return (
       cz*cy*sx, szang*cy*sx,-syang*sx,0.,
       (cz*syang*sxang-szang*cx)*sy,(szang*syang*sxang+cz*cx)*sy,cy*sxang*sy,0.,
       (cz*syang*cx+szang*sxang)*sz,(szang*syang*cx-cz*sxang)*sz,cy*cx*sz,0.,
       p[0],p[1],p[2],1.)


def children(node):
    data=node.get('data') if isinstance(node.get('data'),dict) else {}
    arr=data.get('ChildEntities')
    return arr if isinstance(arr,list) else []


def transform_override(node, over):
    """Apply only explicit nested component/property overrides of a prefab instance.
    An override does not erase omitted fields from the original entity definition.
    """
    if not isinstance(over,dict):return node
    base_data=node.get('data') if isinstance(node.get('data'),dict) else {}
    merged_data=dict(base_data)
    for key,value in over.items():
        if key=='ChildEntities':continue # Keep real template children; overrides are separately passed by name.
        if key in ('Components','Properties') and isinstance(value,dict):
            previous=base_data.get(key) if isinstance(base_data.get(key),dict) else {}
            combined=dict(previous)
            for cname,cbody in value.items():
                if isinstance(cbody,dict) and isinstance(previous.get(cname),dict):
                    old=previous[cname];new=dict(old)
                    for k,v in cbody.items():
                        if k=='Properties' and isinstance(v,dict):
                            prop=dict(old.get('Properties') or {})
                            for field,detail in v.items():
                                if isinstance(detail,dict) and isinstance(prop.get(field),dict):
                                    prop[field]={**prop[field],**detail}
                                else:prop[field]=detail
                            new[k]=prop
                        else:new[k]=v
                    combined[cname]=new
                else:combined[cname]=cbody
            merged_data[key]=combined
        else:
            merged_data[key]=value
    return {**node,'data':merged_data}


@dataclass
class State:
    output: list
    counts: collections.Counter
    warnings: collections.Counter
    total: int=0


class SceneResolver:
    def __init__(self, index, reader):
        self.index=index
        self.reader=reader
        self.cache={}

    def prefab(self,key):
        if key not in self.cache:
            full='VuTemplateAsset/'+key
            if full not in self.index:raise ResolveError('Missing prefab '+key)
            node=TemplateReader(self.reader(full)).root()
            self.cache[key]=node
        return self.cache[key]

    def resolve(self,root,arena):
        state=State([],collections.Counter(),collections.Counter())
        self._visit(root,IDENTITY,'',state,0,(),None,False)
        return {
           'format':'riptide-private-world-instances-v1',
           'arena':arena,
           'basis':'Right-handed XY horizontal Z up; matrix column-major; Rz*Ry*Rx Euler degrees (hypothesis)',
           'instances':state.output,
           'summary':{
              'entities_visited':state.total,
              'renderable_static_references':state.counts['static'],
              'water_entities':state.counts['water'],
              'prefab_instances_expanded':state.counts['prefab'],
              'animated_references':state.counts['animated'],
              'applied_prefab_child_overrides':state.counts['applied_overrides'],
              'warnings':dict(state.warnings)
           },
           'limitations':[
             'Euler ordering and transform convention provisional: validate with in-game captures',
             'Not all game effects, particle systems, water meshes or animated geometry are decoded',
             'Dynamic/conditional visibility and runtime-generated models not simulated',
             'Prefab entity overrides are applied only to fields understood by this parser',
           ],
        }

    def _visit(self,node,parent,path,state,depth,stack,override,in_prefab,named_overrides=None):
        if depth>=MAX_RECURSION:raise ResolveError('Recursion limit reached')
        if not isinstance(node,dict):return
        state.total+=1
        if state.total>MAX_INSTANCES:raise ResolveError('Instance count limit reached')
        if not isinstance(override,dict): override={}
        nested=override.get('ChildEntities')
        if isinstance(nested,dict):
            named_overrides={**(named_overrides or {}),**nested}
        node=transform_override(node,override)
        local=transform(node)
        world=mul(parent,local)
        name=node.get('name')
        kind=node.get('type') or ''
        p=path+'/'+name if isinstance(name,str) and name else path
        data=node.get('data') if isinstance(node.get('data'),dict) else {}
        comps=data.get('Components') if isinstance(data.get('Components'),dict) else {}
        props=data.get('Properties') if isinstance(data.get('Properties'),dict) else {}
        draw=comps.get('Vu3dDrawStaticModelComponent') or {}
        drawprops=draw.get('Properties') if isinstance(draw,dict) else {}
        if not isinstance(drawprops,dict):drawprops={}
        model=drawprops.get('Model Asset') or props.get('Model Asset')
        if isinstance(model,str) and model:
            state.counts['static']+=1
            state.output.append({'path':p,'type':kind,'kind':'static',
              'model':model,'world_matrix':list(world),'world_position':point(world,(0,0,0))})
        animated=((comps.get('Vu3dDrawAnimatedModelComponent') or {}).get('Properties') or {})
        animodel=animated.get('Animated Model Asset') or animated.get('Model Asset')
        if isinstance(animodel,str) and animodel:
            state.counts['animated']+=1
            state.output.append({'path':p,'type':kind,'kind':'animated','model':animodel,
              'world_matrix':list(world),'world_position':point(world,(0,0,0))})
        if kind in ('VuWaterSurfaceEntity','VuWaterRampEntity','VuInfiniteOceanWaveEntity'):
            state.counts['water']+=1
            state.output.append({'path':p,'type':kind,'kind':'water',
              'world_matrix':list(world),'world_position':point(world,(0,0,0)),
              'water_map':props.get('WaterMap'),
              'size':{key:props[key] for key in ('X Size','Y Size','Z Size') if key in props}})
        if isinstance(kind,str) and kind.startswith('#'):
            ref=kind[1:]
            if ref in stack:
                state.warnings['recursive_prefab_cycle']+=1
            else:
                try:
                    pref=self.prefab(ref)
                    state.counts['prefab']+=1
                    supplied=data.get('ChildEntities')
                    overrides=supplied if isinstance(supplied,dict) else {}
                    # Root may hold a prefab transform, and entity-provided overrides.
                    prefab_root=transform_override(pref,data.get('PrefabProperties'))
                    self._visit(prefab_root,world,p+'::'+ref,state,depth+1,stack+(ref,),None,True,overrides)
                except ResolveError as exc:
                    if str(exc).startswith('Missing prefab'):
                        state.warnings['missing_prefab']+=1
                    else:raise
        # Node may hold actual list of ChildEntities, not prefab override dictionary.
        existing=children(node)
        available={c.get('name') for c in existing if isinstance(c,dict) and isinstance(c.get('name'),str)}
        named_overrides=named_overrides or {}
        for unused in set(named_overrides)-available:
            state.warnings['unknown_prefab_child_override']+=1
        for child in existing:
            chosen=child.get('name') if isinstance(child,dict) else None
            ov=named_overrides.get(chosen) if isinstance(chosen,str) else None
            if ov is not None:state.counts['applied_overrides']+=1
            self._visit(child,world,p,state,depth+1,stack,ov,in_prefab)


def build(source,arena):
    with local_apf(source) as f:
        index=index_apf(f)
        def read(name):return payload(f,index[name],max_bytes=40_000_000)
        resolver=SceneResolver(index,read)
        root=TemplateReader(read('VuTemplateAsset/Levels/'+arena)).root()
        return resolver.resolve(root,arena)


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source',type=pathlib.Path)
    cli.add_argument('--arena',choices=LEVELS,default='CityB')
    cli.add_argument('--out',type=pathlib.Path,required=True,help='Private JSON; never publish')
    args=cli.parse_args()
    result=build(args.source,args.arena)
    args.out.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps(result['summary'],indent=2,ensure_ascii=False))

if __name__=='__main__':main()