"""Synthetic-only tests. No proprietary assets redistributed."""
import struct
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from visual_models import parse_static_model,visual_to_collision_preview,VisualModelError


def synthetic():
    buf=bytearray(struct.pack('<3f',10,50,200)+b'\0'*34)
    buf+=struct.pack('<I',1)+b'AR/RampA\0'+struct.pack('<I',1)
    buf+=struct.pack('<4I',0,0,0,1)+struct.pack('<8f',-1,-1,-1,0,1,1,1,0)
    buf+=struct.pack('<II',0,1)+struct.pack('<II',20,60)
    for i in range(3):buf+=struct.pack('<5f',i,i+1,i+2,.5,.5)
    buf+=struct.pack('<I3H',3,0,1,2)+b'\0'
    return bytes(buf)

class VisualModelTests(unittest.TestCase):
    def test_parses_model(self):
        m=parse_static_model(synthetic());self.assertEqual(m.materials,['AR/RampA'])
        self.assertEqual(len(m.streams),1)
        self.assertEqual(m.streams[0].positions[0],(0.,1.,2.))
        self.assertEqual(m.streams[0].indices,[0,1,2])
        preview=visual_to_collision_preview(m)
        self.assertEqual(struct.unpack_from('<I',preview,0)[0],3)
        self.assertEqual(struct.unpack_from('<I',preview,52)[0],3)
    def test_rejects_modified_index(self):
        b=bytearray(synthetic());b[-3]=9
        with self.assertRaises(VisualModelError):parse_static_model(bytes(b))
    def test_rejects_unknown_tail(self):
        with self.assertRaises(VisualModelError):parse_static_model(synthetic()+b'\1'*40)

if __name__=='__main__': unittest.main()