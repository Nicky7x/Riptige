import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from resolve_scene_prefabs import scan_prefab_tree

class PrefabDependencyTests(unittest.TestCase):
    def test_extract_nested_models_and_textures(self):
        prefab={'type':'VuGroupEntity','data':{'ChildEntities':[
            {'type':'#Plants/TreeA','data':{'Components':{'Vu3dDrawStaticModelComponent':
              {'Properties':{'Model Asset':'Plants/TreeStem'}}}}},
            {'type':'VuGamePropEntity','data':{'Properties':{'Texture Asset':'Props/Sign'},
                 'Components':{'Vu3dDrawStaticModelComponent':
                   {'Properties':{'Model Asset':'Props/SignA'}}}}}
        ]}}
        found=scan_prefab_tree(prefab)
        self.assertEqual(found['prefab_aliases'],{'Plants/TreeA'})
        self.assertEqual(found['static_models'],{'Plants/TreeStem','Props/SignA'})
        self.assertEqual(found['textures'],{'Props/Sign'})

    def test_malformed_component_is_safely_ignored(self):
        found=scan_prefab_tree({'type':'VuGroupEntity','data':{
            'Components':{'Vu3dDrawStaticModelComponent':'not an object'},
            'ChildEntities':[None,42,{'type':'VuGamePropEntity','data':None}]}})
        self.assertEqual(found['static_models'],set())
        self.assertEqual(found['prefab_aliases'],set())

if __name__=='__main__':unittest.main()