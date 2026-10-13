import io
import os
import struct
import sys
import unittest
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'..','tools')))
from scene_dependencies import index_apf, scan_scene, payload

class WaterSceneIndexTest(unittest.TestCase):
    def mk_apf(self):
        scene=b'\x00VuWaterSurfaceEntity\x00CityA/WS01\x00VuInfiniteOceanWaveEntity\x00'
        tex=bytearray(70+16)
        struct.pack_into('<II',tex,21,4,4)
        struct.pack_into('<I',tex,33,0x83f3)
        resources=[('VuTemplateAsset/Levels/CityA',scene),('VuWaterMapAsset/CityA/WS01',bytes(tex)),('VuWaterMapAsset/CityA/WS02',bytes(tex))]
        blob=bytearray(56);idx=bytearray();off=56
        for name,data in resources:
            idx+=name.encode()+b'\0'+struct.pack('<5I',off,len(data),len(data),0,0)
            blob+=data;off+=len(data)
        struct.pack_into('<4s4I',blob,0,b'FPUV',6,off,len(resources),len(idx))
        return io.BytesIO(bytes(blob)+bytes(idx))
    def test_exact_reference_without_faking_surface(self):
        f=self.mk_apf();data=scan_scene(f,index_apf(f));one=data['arenas'][0]
        self.assertEqual(one['arena'],'CityA')
        self.assertEqual(one['water_assets'],2)
        self.assertEqual(one['water_references'],1)
        self.assertEqual(one['unlinked_water'],['CityA/WS02'])
        self.assertEqual(one['map_formats']['CityA/WS01']['format'],'DXT5')
        self.assertIn('VuWaterSurfaceEntity',one['entity_types'])
        self.assertNotIn('geometry',one)
    def test_unsupported_version(self):
        f=self.mk_apf();blob=bytearray(f.getvalue());struct.pack_into('<I',blob,4,7)
        with self.assertRaisesRegex(ValueError,'Cabeçalho'):index_apf(io.BytesIO(blob))

if __name__=='__main__':unittest.main()