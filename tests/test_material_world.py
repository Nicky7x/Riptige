"""Tests for verified UV-to-material glTF scene export; synthetic assets only."""
import json
import pathlib
import struct
import sys
import unittest

BASE=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'tools'))
sys.path.insert(0,str(BASE/'tests'))
from test_visual_models import synthetic
from visual_models import parse_static_model
from export_world_glb import convert_model_parts
import trimesh
import numpy as np


class TexturedWorldTests(unittest.TestCase):
    def test_uv_model_groups_have_correct_material_names(self):
        parsed=parse_static_model(synthetic())
        self.assertEqual(parsed.streams[0].uvs[0],(.5,.5))
        parts=convert_model_parts(synthetic())
        self.assertEqual(len(parts),1)
        mesh,material,_=parts[0]
        self.assertEqual(material,'AR/RampA')
        self.assertEqual(mesh.visual.kind,'texture')
        self.assertEqual(mesh.visual.material.name,material)
        self.assertEqual(mesh.visual.uv.shape,(3,2))
        self.assertTrue(np.allclose(mesh.visual.uv,np.full((3,2),.5)))

    def test_glb_keeps_uv_material_and_triangle_group(self):
        scene=trimesh.Scene()
        part,material,_=convert_model_parts(synthetic())[0]
        scene.add_geometry(part,geom_name='synthetic_ramp',node_name='test')
        blob=scene.export(file_type='glb')
        self.assertEqual(blob[:4],b'glTF')
        length=struct.unpack_from('<I',blob,12)[0]
        doc=json.loads(blob[20:20+length])
        self.assertEqual(doc['materials'][0]['name'],material)
        primitive=doc['meshes'][0]['primitives'][0]
        self.assertIn('TEXCOORD_0',primitive['attributes'])
        self.assertEqual(primitive['material'],0)
        self.assertEqual(doc['accessors'][primitive['indices']]['count'],3)

if __name__=='__main__':
    unittest.main()
