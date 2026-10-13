"""Tests for private multi-arena library metadata (NO proprietary game assets)."""
import math
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))

from build_private_world_library import BASIS, multiply, water_records, size_value


class PrivateWorldLibraryTest(unittest.TestCase):
    def test_basis_from_game_z_up_to_gltf_y_up(self):
        identity = (1, 0, 0, 0, 0, 1, 0, 0,
                    0, 0, 1, 0, 10, 20, 30, 1)
        mat = multiply(BASIS, identity)
        self.assertEqual([mat[12], mat[13], mat[14]], [10, 30, -20])

    def test_water_surfaces_use_original_sizes_and_positions(self):
        raw = {'instances': [
            {'kind': 'water', 'type': 'VuWaterSurfaceEntity', 'path': '/original/WS01',
             'world_matrix': [1, 0, 0, 0, 0, 1, 0, 0,
                              0, 0, 1, 0, 3, 4, 5, 1],
             'water_map': 'CityA/WS01', 'size': {'X Size': 30, 'Y Size': 12}},
            {'kind': 'water', 'type': 'VuInfiniteOceanWaveEntity', 'path': '/ocean',
             'world_matrix': [1, 0, 0, 0, 0, 1, 0, 0,
                              0, 0, 1, 0, 0, 0, 0, 1], 'size': {}},
            {'kind': 'static', 'world_matrix': [1]*16},
        ]}
        items = water_records(raw)
        self.assertEqual(len(items), 2)
        self.assertTrue(items[0]['drawable'])
        self.assertEqual((items[0]['width'], items[0]['length']), (30., 12.))
        self.assertEqual(items[0]['matrix'][12:15], [3., 5., -4.])
        self.assertEqual(items[0]['waterMap'], 'CityA/WS01')
        self.assertFalse(items[1]['drawable'])
        self.assertIsNone(items[1]['width'])

    def test_unknown_sizes_are_not_invented(self):
        for bad in (None, -1, 0, float('nan'), float('inf'), '1000', True, 1e10):
            self.assertIsNone(size_value(bad))
        self.assertEqual(size_value(10.5), 10.5)


if __name__ == '__main__':
    unittest.main()
