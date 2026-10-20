"""Solid monument geometry, registered footprints and original prepared assets."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class MonumentAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'art-source/monoliths-v1/models.json').read_text())
        cls.manifest = json.loads((ROOT / 'static/art-manifest-rendered.json').read_text())

    def test_meshes_are_closed_solids_with_positive_volume(self):
        self.assertEqual(len(self.catalog['models']), 12)
        for key, model in self.catalog['models'].items():
            edges = Counter()
            volume = 0
            v = model['vertices']
            for face in model['faces']:
                for i, a in enumerate(face):
                    edges[tuple(sorted([a, face[(i + 1) % len(face)]]))] += 1
                a = v[face[0]]
                for i in range(1, len(face) - 1):
                    b, c = v[face[i]], v[face[i + 1]]
                    cross = [b[1] * c[2] - b[2] * c[1], b[2] * c[0] - b[0] * c[2], b[0] * c[1] - b[1] * c[0]]
                    volume += sum(a[j] * cross[j] for j in range(3)) / 6
            with self.subTest(key=key):
                self.assertEqual(set(edges.values()), {2})
                self.assertGreater(volume, 0)

    def test_base_and_overhang_fit_one_authoritative_solid_hex(self):
        p = self.catalog['projection']
        for key, model in self.catalog['models'].items():
            with self.subTest(key=key):
                radius = max(math.hypot(x, y) for x, y, z in model['vertices'])
                native = radius * p['pixels_per_world_unit'] * p['runtime_scale']
                self.assertLess(native, 34 * math.sqrt(3) / 2)
                self.assertEqual(model['service_anchor'], [0, 0, 0])

    def test_condition_states_and_transparent_margins_are_registered(self):
        for key in self.catalog['models']:
            asset = self.manifest['assets'][key]
            with self.subTest(key=key), Image.open(ROOT / 'static' / asset['image'].lstrip('/')) as image:
                states = []
                for frame in asset['frames']:
                    x, y, w, h = frame
                    rgba = image.crop((x, y, x + w, y + h)).convert('RGBA')
                    opaque = rgba.getchannel('A').point(lambda a: 255 if a >= 248 else 0).getbbox()
                    self.assertTrue(opaque and 1 < opaque[0] < opaque[2] < w - 1)
                    self.assertTrue(1 < opaque[1] < opaque[3] < h - 1)
                    # Ground shadows must fit too; they remain below picking opacity.
                    bounds = rgba.getbbox()
                    self.assertTrue(1 < bounds[0] < bounds[2] < w - 1)
                    self.assertTrue(1 < bounds[1] < bounds[3] < h - 1)
                    states.append(hashlib.sha256(rgba.tobytes()).hexdigest())
                self.assertNotEqual(*states)
                self.assertEqual(asset['anchor'], self.catalog['projection']['anchor'])

    def test_service_models_and_aliases_use_the_registered_core(self):
        for region in self.manifest['visual_catalog']['regions']:
            for kind in ['power', 'water', 'relay']:
                core = 'monolith_' + kind + '_' + region
                for tone in ['', '_tone1', '_tone2']:
                    self.assertEqual(self.manifest['assets'][kind + '_' + region + tone]['monolith_core'], core)
        for kind in ['power', 'water', 'relay']:
            self.assertEqual(self.manifest['assets'][kind]['monolith_core'], 'monolith_' + kind + '_WN_TOWER')
        for kind in ['garden', 'shelter', 'workshop', 'exchange']:
            self.assertNotIn('monolith_core', self.manifest['assets'][kind])

    def test_receipts_pin_source_and_every_new_atlas(self):
        record = json.loads((ROOT / 'art-source/monoliths-v1/render-record.json').read_text())
        self.assertEqual(record['frames'], 24)
        self.assertEqual(record['source_sha256'], hashlib.sha256((ROOT / 'tools/build_monoliths.py').read_bytes()).hexdigest())
        for asset in record['assets']:
            self.assertEqual(asset['sha256'], hashlib.sha256((ROOT / 'static/art' / asset['image']).read_bytes()).hexdigest())
