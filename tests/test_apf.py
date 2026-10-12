"""Fixtures sintéticas: não requer arquivos proprietários do jogo."""
import lzma
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from inspect_xapk import decompress_payload, parse_apf_index


class TestAPF(unittest.TestCase):
    def test_zlib(self):
        sample = b"Hello APF" * 100
        raw, kind, marker = decompress_payload(zlib.compress(sample), len(sample))
        self.assertEqual(raw, sample)
        self.assertEqual(kind, "zlib")
        self.assertTrue(marker)

    def test_lzma_raw(self):
        sample = b"VuAiWaypointEntity\0CheckPoint Width\0" * 200
        filters = [dict(id=lzma.FILTER_LZMA1, lc=3, lp=0, pb=2, dict_size=1 << 20)]
        compressed = lzma.compress(sample, format=lzma.FORMAT_RAW, filters=filters)
        wrapped = b"\x5d" + (1 << 20).to_bytes(4,"little") + compressed
        raw, kind, _ = decompress_payload(wrapped, len(sample))
        self.assertEqual(raw, sample)
        self.assertIn("LZMA1", kind)

    def test_read_index(self):
        index = b"example\0" + struct.pack("<IIIII",60,30,6,12345,65536)
        off = 66
        hdr = b"FPUV" + struct.pack("<5I",6,off,1,len(index),0) + b"TestBuild\0".ljust(32,b"\0") + b"\0"*4
        self.assertEqual(len(hdr),60)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"fixture.apf"
            path.write_bytes(hdr+b"ABCDEF"+index)
            meta,rows=parse_apf_index(path)
            self.assertEqual(meta["resource_count"],1)
            self.assertEqual(rows[0]["name"],"example")
            self.assertEqual(rows[0]["flags"],65536)

    def test_wrong_size_fails(self):
        with self.assertRaises(ValueError):
            decompress_payload(zlib.compress(b"hello"),3)


if __name__ == "__main__":
    unittest.main()
