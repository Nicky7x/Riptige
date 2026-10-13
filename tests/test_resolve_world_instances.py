"""Synthetic-only tests of T*R*S, prefab hierarchy and field overrides.
No proprietary original game data appears in this file.
"""
import math,unittest,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools') if pathlib.Path(__file__).parent.name=='tests' else str(pathlib.Path(__file__).resolve().parent))
from resolve_world_instances import IDENTITY,SceneResolver,ResolveError,mul,point,transform


def n(name='',typ='VuGroupEntity',pos=None,rot=None,scale=None,children=None,model=None):
    props={}
    if pos is not None:props['Position']=dict(zip('XYZ',pos))
    if rot is not None:props['Rotation']=dict(zip('XYZ',rot))
    if scale is not None:props['Scale']=dict(zip('XYZ',scale))
    comps={'VuTransformComponent':{'Properties':props}}
    if model:comps['Vu3dDrawStaticModelComponent']={'Properties':{'Model Asset':model}}
    data={'Components':comps}
    if children is not None:data['ChildEntities']=children
    return {'name':name,'type':typ,'data':data}

class WorldTransformTests(unittest.TestCase):
    def test_identity_parent(self):
        self.assertEqual(point(IDENTITY,[1,2,3]),[1,2,3])
        obj=n(pos=[5,-3,8]);self.assertEqual(point(transform(obj),[0,0,0]),[5,-3,8])

    def test_parent_rotates_child_translation(self):
        parent=transform(n(rot=[0,0,90],pos=[10,10,0]))
        child=transform(n(pos=[4,0,2]))
        p=point(mul(parent,child),[0,0,0])
        for a,b in zip(p,[10,14,2]):self.assertAlmostEqual(a,b,places=5)

    def test_nonuniform_scale_and_euler(self):
        a=transform(n(pos=[8,-3,4],scale=[2,3,4]))
        self.assertEqual(point(a,[1,1,1]),[10,-0.,8])
        angle=transform(n(rot=[90,0,0]))
        p=point(angle,[0,1,0]);self.assertAlmostEqual(p[2],1)

    def test_nested_prefab_overrides_composed(self):
        prefab=n('pref','VuGroupEntity',children=[n('ChildModel',model='Props/Synthetic')])
        alias=n('Copy','#Prefab/Synthetic',pos=[10,20,4],rot=[0,0,90])
        alias['data']['ChildEntities']={
            'ChildModel':{'Components':{'VuTransformComponent':{
                'Properties':{'Position':{'X':4,'Y':0,'Z':3}}}}}
        }
        root=n('scene',children=[alias])
        resolver=SceneResolver({'VuTemplateAsset/Prefab/Synthetic':object()},lambda k:b'')
        resolver.cache['Prefab/Synthetic']=prefab
        result=resolver.resolve(root,'TEST')
        self.assertEqual(result['summary']['applied_prefab_child_overrides'],1)
        self.assertEqual(result['summary']['warnings'],{})
        self.assertEqual(len(result['instances']),1)
        p=result['instances'][0]['world_position']
        for a,b in zip(p,[10,24,7]):self.assertAlmostEqual(a,b,places=5)

    def test_override_merges_only_explicit_axis(self):
        prefab=n('pref',children=[n('Shape',pos=[4,5,6],model='Props/Synthetic')])
        alias=n('Alias','#Prefab/Other')
        alias['data']['ChildEntities']={'Shape':{'Components':{
            'VuTransformComponent':{'Properties':{'Position':{'Y':14}}}
        }}}
        resolver=SceneResolver({'VuTemplateAsset/Prefab/Other':None},lambda k:b'')
        resolver.cache['Prefab/Other']=prefab
        result=resolver.resolve(n(children=[alias]),'TEST')
        self.assertEqual(result['instances'][0]['world_position'],[4.,14.,6.])

    def test_prefab_cycles_are_reported_and_bounded(self):
        a=n('a','#Prefab/B');b=n('b','#Prefab/A')
        resolver=SceneResolver({},lambda k:b'')
        resolver.cache={'Prefab/A':n('A',children=[a]),'Prefab/B':n('B',children=[b])}
        result=resolver.resolve(n(children=[n('start','#Prefab/A')]),'TEST')
        self.assertGreater(result['summary']['warnings'].get('recursive_prefab_cycle',0),0)

    def test_reject_nonfinite_coordinates(self):
        with self.assertRaises(ResolveError):transform(n(pos=[0,float('nan'),0]))

if __name__=='__main__':unittest.main()