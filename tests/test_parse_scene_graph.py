"""Synthetic-only tests: never include or redistribute game resources."""
import pathlib
import struct
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from parse_scene_graph import TemplateReader, SceneFormatError, fnv1a64, extract_instances, summarize


def fixture():
    entity = {'type':'VuWaterSurfaceEntity','name':'SurfaceA',
       'data':{'Properties':{'WaterMap':'CityB/WS01','X Size':'128','Y Size':'64'},
               'Components':{'VuTransformComponent':{'Properties':{'Position':{'X':-128,'Y':5.5,'Z':3},'Rotation':{'Z':-90}}}}}}
    root = {'RootEntity':{'type':'VuContainerEntity',
        'data':{'ChildEntities':[entity]}}}
    # Manually write the recursive tagged schema. Field labels and values
    # use FNV-1a 64 and 32-bit signed relative pointers into the text pool.
    labels=set()
    strings=[]
    def emit(value):
        if isinstance(value,dict):
            parts=[]
            for key,child in value.items():
                labels.add(key)
                parts.append((key,emit(child)))
            buf=bytearray(struct.pack('<II',6,len(parts))+b'\0'*(16*len(parts)))
            for i,(key,child) in enumerate(parts):
                off=len(buf)
                struct.pack_into('<QII',buf,8+16*i,fnv1a64(key),0,off)
                buf+=child
            return buf
        if isinstance(value,list):
            parts=[emit(v) for v in value]
            buf=bytearray(struct.pack('<II',5,len(parts))+b'\0'*(4*len(parts)))
            for i,child in enumerate(parts):
                struct.pack_into('<I',buf,8+i*4,len(buf))
                buf+=child
            return buf
        if isinstance(value,float):return bytearray(struct.pack('<If',2,value))
        if isinstance(value,int):return bytearray(struct.pack('<Ii',1,value))
        if isinstance(value,str):
            # Placeholder pointer; fill using final offsets after scanning.
            strings.append(value)
            return bytearray(struct.pack('<II',4,0))
        raise AssertionError(type(value))
    tree=emit(root)
    output=bytearray(b'\0'*8+tree)
    string_values=iter(strings)
    def patch_strings(start):
        tag=struct.unpack_from('<I',output,start)[0]
        count=struct.unpack_from('<I',output,start+4)[0]
        if tag==4:
            value=next(string_values)
            offset=len(output)
            output.extend(value.encode()+b'\0')
            struct.pack_into('<i',output,start+4,offset-start)
        elif tag==5:
            offs=[struct.unpack_from('<I',output,start+8+4*i)[0] for i in range(count)]
            for v in offs:patch_strings(start+v)
        elif tag==6:
            offs=[struct.unpack_from('<I',output,start+8+16*i+12)[0] for i in range(count)]
            for v in offs:patch_strings(start+v)
    # Re-derive string order by walking tree (emit() inserts strings in DFS).
    patch_strings(8)
    for label in sorted(labels): output.extend(label.encode()+b'\0')
    struct.pack_into('<II',output,0,1,len(output))
    return bytes(output)


class TemplateParserTests(unittest.TestCase):
    def test_hashes_verified_against_original_field_identifiers(self):
        self.assertEqual(fnv1a64('X'),0xaf64154c86024d67)
        self.assertEqual(fnv1a64('Y'),0xaf64144c86024bb4)
        self.assertEqual(fnv1a64('Position'),0xc1611c0558728a2a)
        self.assertEqual(fnv1a64('RootEntity'),0x7456288f86d4ad5a)

    def test_reads_relative_string_and_negative_transform_values(self):
        parser=TemplateReader(fixture())
        root=parser.root()
        self.assertFalse(parser.unresolved)
        scene=extract_instances(root,'CityB')
        self.assertEqual(scene['entities_total'],2)
        self.assertEqual(len(scene['instances']),1)
        a=scene['instances'][0]
        self.assertEqual(a['water_map'],'CityB/WS01')
        self.assertEqual(a['local_transform']['position']['X'],-128)
        self.assertEqual(a['local_transform']['position']['Y'],5.5)
        self.assertEqual(a['local_transform']['rotation']['Z'],-90)
        self.assertEqual(a['water_size']['X Size'],'128')
        self.assertEqual(summarize(scene)['water_entities'],1)

    def test_rejects_header_length_mismatch(self):
        sample=bytearray(fixture())
        struct.pack_into('<I',sample,4,len(sample)+1)
        with self.assertRaises(SceneFormatError): TemplateReader(bytes(sample))

    def test_rejects_bad_variant(self):
        sample=bytearray(fixture());struct.pack_into('<I',sample,8,42)
        with self.assertRaises(SceneFormatError):TemplateReader(bytes(sample)).root()

    def test_rejects_invalid_string_pointer(self):
        sample=bytearray(fixture())
        p=sample.find(struct.pack('<I',4))
        # locate real string node by scan; first type-4 occurs after header.
        self.assertGreaterEqual(p,8)
        struct.pack_into('<i',sample,p+4,0x7fffffff)
        with self.assertRaises(SceneFormatError):TemplateReader(bytes(sample)).root()

if __name__=='__main__':unittest.main()