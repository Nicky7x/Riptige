"""Fixtures sintéticas: não requer arquivos do jogo."""
import struct
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from export_collision import decode_mesh_header

def fake(vertices=((1.,2.,3.,0.),(5.,2.,3.,0.),(3.,4.,3.,0.)),indices=(0,1,2),tail=b'extra'):
    return (struct.pack('<I',len(vertices))+
        b''.join(struct.pack('<4f',*v) for v in vertices)+
        struct.pack('<I',len(indices))+struct.pack('<'+str(len(indices))+'H',*indices)+tail)

class TestCollision(unittest.TestCase):
    def test_mesh_layout(self):
        m=decode_mesh_header(fake())
        self.assertEqual(m['vertices'],3)
        self.assertEqual(m['triangles'],1)
        self.assertEqual(m['unknown_tail_bytes'],5)
        self.assertEqual(m['bounds']['min'],[1.,2.,3.])
        self.assertEqual(m['bounds']['max'],[5.,4.,3.])
    def test_out_of_range_index(self):
        with self.assertRaisesRegex(ValueError,'inexistente'):decode_mesh_header(fake(indices=(0,1,3)))
    def test_invalid_vertex_count(self):
        with self.assertRaises(ValueError):decode_mesh_header(struct.pack('<I',999999)+b'xxxx')
    def test_invalid_component(self):
        with self.assertRaisesRegex(ValueError,'Quarta componente'):decode_mesh_header(fake(vertices=((1,2,3,1),)))
    def test_invalid_triangle(self):
        with self.assertRaisesRegex(ValueError,'Índices triangulares'):decode_mesh_header(fake(indices=(0,1)))

if __name__=='__main__':unittest.main()
