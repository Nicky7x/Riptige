import io
import pathlib
import tempfile
import zipfile
import os
import struct
import lzma
import sys
import unittest
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),'..','tools')))
from scene_dependencies import index_apf, scan_scene, payload, local_apf, Entry

class WaterSceneIndexTest(unittest.TestCase):
    def mk_apf(self):
        scene=b'\x00VuWaterSurfaceEntity\x00CityA/WS01\x00VuInfiniteOceanWaveEntity\x00'
        tex=bytearray(70+16)
        struct.pack_into('<II',tex,20,4,4)
        struct.pack_into('<I',tex,32,0x83f3)
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
    def test_xapk_nested_archives_are_processed_locally(self):
        with tempfile.TemporaryDirectory() as directory:
            src=pathlib.Path(directory)/'game.xapk'
            base=io.BytesIO()
            with zipfile.ZipFile(base,'w') as apk:apk.writestr('assets/Assets.apf',self.mk_apf().getvalue())
            with zipfile.ZipFile(src,'w') as xapk:xapk.writestr('base.apk',base.getvalue())
            with local_apf(src) as unpacked:
                scene=scan_scene(unpacked,index_apf(unpacked))
                self.assertEqual(scene['arenas'][0]['water_references'],1)

    def test_original_lzma_template_single_null_trailer_is_validated_and_trimmed(self):
        scene=struct.pack('<II',1,16)+struct.pack('<II',3,123)
        filters=[dict(id=lzma.FILTER_LZMA1,dict_size=1048576,lc=3,lp=0,pb=2)]
        def encoded(data):
            packed=lzma.compress(data,format=lzma.FORMAT_RAW,filters=filters)
            return bytes([93])+struct.pack('<I',1048576)+packed
        for suffix,allowed in ((b'\0',True),(b'!',False)):
            packed=encoded(scene+suffix)
            entry=Entry('VuTemplateAsset/Building/OriginalPadding',56,len(scene),len(packed),2<<16)
            f=io.BytesIO(b'\0'*56+packed)
            if allowed:self.assertEqual(payload(f,entry),scene)
            else:
                with self.assertRaisesRegex(ValueError,'Tamanho'):payload(f,entry)

    def test_unsupported_version(self):
        f=self.mk_apf();blob=bytearray(f.getvalue());struct.pack_into('<I',blob,4,7)
        with self.assertRaisesRegex(ValueError,'Cabeçalho'):index_apf(io.BytesIO(blob))

if __name__=='__main__':unittest.main()