#!/usr/bin/env python3
"""Audit prefab/template dependencies for original Riptide arenas (read-only).

The public summary contains counts only; never publish the detailed private
entity transforms, model instances, or game payloads returned by --out.
"""
from __future__ import annotations
import argparse
import collections
import json
import pathlib
from parse_scene_graph import TemplateReader,extract_instances
from scene_dependencies import LEVELS,index_apf,local_apf,payload


def scan_prefab_tree(node: dict) -> dict[str,set[str]]:
    result={'prefab_aliases':set(),'static_models':set(),'textures':set(),'animated_models':set()}
    def recurse(item):
        if not isinstance(item,dict):return
        typ=item.get('type')
        if isinstance(typ,str) and typ.startswith('#'):
            result['prefab_aliases'].add(typ[1:])
        data=item.get('data')
        if not isinstance(data,dict):return
        for props in [data.get('Properties')]:
            if isinstance(props,dict):read_properties(props)
        comps=data.get('Components')
        if isinstance(comps,dict):
            for component in comps.values():
                if isinstance(component,dict):
                    props=component.get('Properties')
                    if isinstance(props,dict):read_properties(props)
        children=data.get('ChildEntities')
        if isinstance(children,list):
            for c in children:recurse(c)
    def read_properties(props):
        for key,target in [('Model Asset','static_models'),('Texture Asset','textures'),
                           ('Animated Model Asset','animated_models')]:
            val=props.get(key)
            if isinstance(val,str) and val:result[target].add(val)
    recurse(node)
    return result


def audit(source: pathlib.Path):
    usage=collections.Counter()
    per_arena_counts=collections.Counter()
    referenced_from:dict[str,set[str]]=collections.defaultdict(set)
    with local_apf(source) as f:
        entries=index_apf(f)
        for arena in LEVELS:
            key=f'VuTemplateAsset/Levels/{arena}'
            if key not in entries:continue
            root=TemplateReader(payload(f,entries[key],max_bytes=40_000_000)).root()
            scenes=extract_instances(root,arena)
            for item in scenes['instances']:
                if item.get('model_reference_type')=='prefab_alias':
                    name=item['model_reference']
                    usage[name]+=1
                    per_arena_counts[arena]+=1
                    referenced_from[name].add(arena)
        defs={};missing=[]
        for name in sorted(usage):
            resource='VuTemplateAsset/'+name
            if resource not in entries:
                missing.append(name);continue
            reader=TemplateReader(payload(f,entries[resource],max_bytes=40_000_000))
            tree=scan_prefab_tree(reader.root())
            defs[name]={k:sorted(v) for k,v in tree.items()}
        all_nested=set(n for item in defs.values() for n in item['prefab_aliases'])
        static=set(n for item in defs.values() for n in item['static_models'])
        textured=set(n for item in defs.values() for n in item['textures'])
        def existing(ref,category):return category+'/'+ref in entries
        report={
         'prefab_references_from_scenes':sum(usage.values()),
         'distinct_prefabs_used_by_scenes':len(usage),
         'prefab_definitions_found':len(defs),
         'missing_direct_prefab_definitions':missing,
         'distinct_nested_prefab_links':len(all_nested),
         'nested_prefab_links_with_definition':sum(existing(n,'VuTemplateAsset') for n in all_nested),
         'distinct_static_model_references_in_prefabs':len(static),
         'static_model_resources_present':sum(existing(n,'VuStaticModelAsset') for n in static),
         'distinct_texture_references_in_prefabs':len(textured),
         'texture_resources_present':sum(existing(n,'VuTextureAsset') for n in textured),
         'arenas':{arena:{'prefab_instance_count':per_arena_counts[arena],
                          'distinct_prefabs':len([n for n in referenced_from if arena in referenced_from[n]])}
                   for arena in LEVELS},
         'limitations':['Counts are dependency/instance references, not distinct rendered meshes.',
                        'Nested prefabs may carry animated/dynamic data and transformations not applied.',
                        'Some Model Asset paths may refer to skinned/animated rather than static resources.',
                        'No proprietary model bytes or scene transforms are in this summary.']}
    return report,{'definitions':defs,'instanced_prefabs':dict(usage)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=pathlib.Path)
    p.add_argument('--out',type=pathlib.Path,help='Private detailed prefab map; never commit to public repo')
    args=p.parse_args()
    summary,private=audit(args.source)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if args.out:args.out.write_text(json.dumps(private,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()