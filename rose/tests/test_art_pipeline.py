"""Asset registration and color guarantees. Pillow is a developer-only dependency."""
import hashlib
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    from PIL import Image
    sys.path.insert(0, str(ROOT / 'tools'))
    from export_sprites import indexed, pixels, learn_palette, alpha_table
except ImportError:
    Image = None


class ProjectionTests(unittest.TestCase):
    def test_six_facings_match_the_axial_screen_basis(self):
        catalog = json.loads((ROOT / 'art-source/render-catalog.json').read_text())
        phi = math.radians(catalog['projection']['camera_azimuth_degrees'])
        u, v = (-math.sin(phi), math.cos(phi)), (math.cos(phi), math.sin(phi))
        expected = [(1, 0), (.5, -math.sqrt(3) / 2), (-.5, -math.sqrt(3) / 2),
                    (-1, 0), (-.5, math.sqrt(3) / 2), (.5, math.sqrt(3) / 2)]
        for yaw, (x, depth) in zip(catalog['projection']['facing_yaw_degrees'], expected):
            a = math.radians(yaw)
            forward = (math.sin(a), -math.cos(a))  # Model forward is local -Y.
            self.assertAlmostEqual(sum(a * b for a, b in zip(forward, u)), x)
            self.assertAlmostEqual(sum(a * b for a, b in zip(forward, v)), depth)
        self.assertAlmostEqual(math.sin(math.radians(catalog['projection']['elevation_degrees'])), .52)

    def test_complete_bake_has_unique_timeline_frames(self):
        catalog = json.loads((ROOT / 'art-source/render-catalog.json').read_text())
        frames = [n for r in catalog['models'].values() for n in r['timeline_frames']]
        self.assertEqual(sorted(frames), list(range(1, len(frames)+1)))
        self.assertEqual(len(frames),1244)
        for key in [*catalog['visual_catalog']['profiles'], 'construct']:
            record = catalog['models'][key]
            self.assertEqual(len(record['frames']), 192)
            for direction in range(6):
                for pose, animation in catalog['animations'].items():
                    clip = record['clips'][f'{pose}_{direction}']
                    self.assertEqual(len(clip), animation['frames'])
                    self.assertTrue(all(0 <= n < len(record['frames']) for n in clip))


@unittest.skipIf(Image is None, 'Pillow is only required for developer art checks')
class SpriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / 'static/art-manifest-rendered.json').read_text())
        cls.colors = cls.manifest['palette']['rgb']

    def test_dark_opaque_pixels_never_use_transparent_index(self):
        palette = [[0, 0, 0]] + [[i, i, i] for i in range(255)]
        image = Image.new('RGBA', (4, 1))
        image.putdata([(0, 0, 0, 255), (1, 1, 1, 255), (255, 255, 255, 255), (0, 0, 0, 0)])
        result = indexed(image, palette)
        values = list(pixels(result))
        self.assertTrue(all(i > 0 for i in values[:3]))
        self.assertEqual(values[3], 0)
        self.assertEqual(result.info['transparency'], 0)

    def test_palette_rebuild_uses_opaque_surface_colors(self):
        source = Image.new('RGBA', (4, 1))
        source.putdata([(200, 180, 140, 255), (200, 180, 140, 255), (0, 255, 0, 0), (255, 0, 255, 180)])
        palette = learn_palette({'traveler': [source]})
        self.assertEqual(len(palette), 256)
        self.assertEqual(palette[0], [0, 0, 0])
        self.assertIn([200, 180, 140], palette[1:])
        self.assertNotIn([0, 255, 0], palette[1:])
        self.assertNotIn([255, 0, 255], palette[1:])

    def test_alpha_dither_is_spatially_fixed_and_preserves_coverage(self):
        source = Image.new('RGBA', (16, 16), (75, 90, 65, 128))
        a, b = indexed(source, self.colors), indexed(source, self.colors)
        self.assertEqual(a.tobytes(), b.tobytes())
        self.assertEqual(sum(i != 0 for i in pixels(a)), 128)

    def test_every_atlas_has_the_identical_256_entry_palette(self):
        paths = {a['image'] for a in self.manifest['assets'].values()}
        self.assertEqual(len(paths), 132)
        expected = [v for c in self.colors for v in c]
        self.assertEqual(len(expected), 768)
        for url in paths:
            with self.subTest(url=url), Image.open(ROOT / 'static' / url.lstrip('/')) as image:
                self.assertEqual(image.mode, 'P')
                self.assertEqual(image.getpalette(), expected)
                self.assertEqual(image.info.get('transparency'), alpha_table(16))

    def test_manifest_frames_fit_their_atlas_and_share_one_origin(self):
        for key, asset in self.manifest['assets'].items():
            with self.subTest(key=key), Image.open(ROOT / 'static' / asset['image'].lstrip('/')) as image:
                self.assertNotIn('anchors', asset)
                self.assertNotIn('scales', asset)
                self.assertTrue(0 < asset['anchor'][0] < asset['frames'][0][2])
                self.assertTrue(0 < asset['anchor'][1] < asset['frames'][0][3])
                for x, y, w, h in asset['frames']:
                    self.assertGreaterEqual(x, 0)
                    self.assertGreaterEqual(y, 0)
                    self.assertLessEqual(x + w, image.width)
                    self.assertLessEqual(y + h, image.height)
                if asset['kind'] == 'texture':
                    self.assertNotIn(0, set(pixels(image)))
                    self.assertEqual(image.convert('RGBA').getchannel('A').getextrema(),(255,255))

    def test_registered_cells_and_clips_are_nonempty(self):
        for key in ('player', 'threat', 'power', 'water', 'garden', 'shelter', 'workshop', 'exchange', 'relay', 'rock'):
            asset = self.manifest['assets'][key]
            with Image.open(ROOT / 'static' / asset['image'].lstrip('/')) as image:
                for i, (x, y, w, h) in enumerate(asset['frames']):
                    with self.subTest(asset=key, frame=i):
                        # Dithered translucent shadow pixels may reach an edge;
                        # opaque meshes were checked before export by the tool.
                        cell = image.crop((x, y, x + w, y + h))
                        self.assertTrue(any(pixels(cell)))
                for name, clip in asset['clips'].items():
                    self.assertTrue(clip, name)
                    self.assertTrue(all(0 <= i < len(asset['frames']) for i in clip))

    def test_render_receipts_match_shipped_bytes_and_editable_source(self):
        record = json.loads((ROOT / 'art-source/render-record.json').read_text())
        self.assertEqual(record['frame_count'], 1244)
        self.assertEqual(record['modeled_families'],46)
        self.assertEqual(hashlib.sha256((ROOT / 'art-source/Rose-prefabs.blend').read_bytes()).hexdigest(), record['blend_sha256'])
        for asset in record['assets']:
            p = ROOT / 'static/art' / asset['image']
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), asset['sha256'])

    def test_original_pack_remains_byte_identical_to_its_archived_receipts(self):
        archive = ROOT / 'art-source/archive/rendered-v1'
        record = json.loads((archive / 'render-record.json').read_text())
        manifest = json.loads((ROOT / 'static/art-manifest-rendered-legacy.json').read_text())
        self.assertEqual(manifest['style'], 'rendered-legacy')
        self.assertEqual(hashlib.sha256((archive / 'Rose-prefabs.blend').read_bytes()).hexdigest(), record['blend_sha256'])
        urls = {a['image'] for a in manifest['assets'].values()}
        for asset in record['assets']:
            self.assertIn('/art/' + asset['image'], urls)
            self.assertEqual(hashlib.sha256((ROOT / 'static/art' / asset['image']).read_bytes()).hexdigest(), asset['sha256'])

    def test_grounded_pack_preserves_the_original_frame_registration(self):
        original = json.loads((ROOT / 'static/art-manifest-rendered-legacy.json').read_text())
        self.assertEqual(self.manifest['projection'], original['projection'])
        self.assertEqual(self.manifest['animations'], original['animations'])
        for key, old in original['assets'].items():
            with self.subTest(key=key):
                asset = self.manifest['assets'][key]
                self.assertEqual(asset['kind'],old['kind'])
                w,h=asset['frames'][0][2:];ow,oh=old['frames'][0][2:]
                for axis,half in [(0,w/2),(1,h/2)]:
                    self.assertAlmostEqual((asset['anchor'][axis]-half)*asset['scale'],(old['anchor'][axis]-[ow/2,oh/2][axis])*old['scale'],places=4)
                for clip,indices in old['clips'].items():
                    self.assertEqual(asset['clips'][clip],indices)
                    if key in ['player','npc','companion','threat']:
                        for i in indices:
                            self.assertEqual([n*asset['scale'] for n in asset['frames'][i][2:]],[n*old['scale'] for n in old['frames'][i][2:]])

    def test_tone_treatments_preserve_every_alpha_pixel(self):
        for key,asset in self.manifest['assets'].items():
            if '_tone' not in key:continue
            base=self.manifest['assets'][key.rsplit('_tone',1)[0]]
            with Image.open(ROOT/'static'/asset['image'].lstrip('/')) as a, Image.open(ROOT/'static'/base['image'].lstrip('/')) as b:
                self.assertEqual(a.convert('RGBA').getchannel('A').tobytes(),b.convert('RGBA').getchannel('A').tobytes())
                for field in ['anchor','frames','clips']:self.assertEqual(asset[field],base[field])

    def test_body_families_have_distinct_mesh_silhouettes_and_pixels(self):
        hashes=[];masks=[]
        for key in self.manifest['visual_catalog']['profiles']:
            asset=self.manifest['assets'][key];x,y,w,h=asset['frames'][asset['clips']['idle_4'][0]]
            with Image.open(ROOT/'static'/asset['image'].lstrip('/')) as im:
                cell=im.crop((x,y,x+w,y+h)).convert('RGBA');hashes.append(hashlib.sha256(cell.tobytes()).hexdigest());masks.append(hashlib.sha256(cell.getchannel('A').tobytes()).hexdigest())
        self.assertEqual(len(set(hashes)),5);self.assertEqual(len(set(masks)),5)

    def test_each_regional_structure_has_a_distinct_rendered_wear_state(self):
        for region in self.manifest['visual_catalog']['regions']:
            for kind in self.manifest['visual_catalog']['structures']:
                key=kind+'_'+region;asset=self.manifest['assets'][key]
                with self.subTest(key=key),Image.open(ROOT/'static'/asset['image'].lstrip('/')) as im:
                    cells=[]
                    for pose in ['idle','worn']:
                        x,y,w,h=asset['frames'][asset['clips'][pose][0]];cells.append(im.crop((x,y,x+w,y+h)).tobytes())
                    self.assertNotEqual(hashlib.sha256(cells[0]).hexdigest(),hashlib.sha256(cells[1]).hexdigest())

    def test_body_reuse_has_archived_source_and_matching_dependency_proof(self):
        archive=ROOT/'art-source/archive/rendered-v3'
        proof=json.loads((archive/'body-reuse-proof-v3.json').read_text())
        record=json.loads((archive/'render-record.json').read_text())
        self.assertEqual(hashlib.sha256((archive/'body-bake-v3.blend').read_bytes()).hexdigest(),proof['original_body_source_sha256'])
        self.assertEqual(record['blend_sha256'],proof['current_source_sha256'])
        for key,item in proof['models'].items():
            self.assertEqual(item['before'],item['after'])
            self.assertEqual(record['renderer']['model_source_sha256'][key],proof['original_body_source_sha256'])

    def test_shadow_gradient_uses_alpha_levels_without_erasing_opaque_black(self):
        colors=[[0,0,0]]*17+[[i,i,i] for i in range(239)]
        source=Image.new('RGBA',(17,1));source.putdata([(0,0,0,a) for a in range(0,241,15)])
        result=indexed(source,colors,shadow_levels=16)
        self.assertEqual(list(pixels(result)),list(range(17)))
        self.assertEqual(list(pixels(result.convert('RGBA').getchannel('A'))),list(range(0,241,15)))
        opaque=indexed(Image.new('RGBA',(1,1),(0,0,0,255)),colors,shadow_levels=16)
        self.assertGreaterEqual(opaque.getpixel((0,0)),17)
        self.assertEqual(opaque.convert('RGBA').getpixel((0,0)),(0,0,0,255))

    def test_individual_v3_atlases_and_source_remain_byte_identical(self):
        archive=ROOT/'art-source/archive/rendered-v3';record=json.loads((archive/'render-record.json').read_text())
        self.assertEqual(hashlib.sha256((archive/'Rose-prefabs.blend').read_bytes()).hexdigest(),record['blend_sha256'])
        for asset in record['assets']:
            self.assertEqual(hashlib.sha256((ROOT/'static/art'/asset['image']).read_bytes()).hexdigest(),asset['sha256'])

    def test_current_body_reuse_matches_preserved_source_recipe_and_dependencies(self):
        archive=ROOT/'art-source/archive/rendered-v4'
        proof_path=ROOT/'art-source/body-reuse-proof-v6.json';proof=json.loads(proof_path.read_text())
        record=json.loads((ROOT/'art-source/render-record.json').read_text())
        old_sha=hashlib.sha256((archive/'Rose-prefabs.blend').read_bytes()).hexdigest()
        recipe=hashlib.sha256((archive/'Rose-prefabs.blend').read_bytes()+(archive/'render_saved_blend.py').read_bytes()+(archive/'render_blender.py').read_bytes()).hexdigest()
        self.assertEqual(proof['original_body_source_sha256'],old_sha)
        self.assertEqual(proof['original_renderer_sha256'],recipe)
        self.assertEqual(proof['current_source_sha256'],record['blend_sha256'])
        self.assertEqual(record['renderer']['body_reuse_proof_sha256'],hashlib.sha256(proof_path.read_bytes()).hexdigest())
        self.assertEqual(proof['fingerprint_tool_sha256'],hashlib.sha256((ROOT/'tools/body_dependencies.py').read_bytes()).hexdigest())
        self.assertEqual(set(proof['models']),{*self.manifest['visual_catalog']['profiles'],'construct'})
        for key,check in proof['models'].items():
            self.assertEqual(check['before'],check['after'])
            self.assertEqual(record['renderer']['model_source_sha256'][key],old_sha)
        for receipt in record['assets']:
            model=receipt.get('derived_from',receipt['asset'])
            self.assertEqual(receipt['model_source_sha256'],old_sha if model in proof['models'] else record['blend_sha256'])

    def test_fidelity_v4_source_and_every_atlas_remain_byte_identical(self):
        archive=ROOT/'art-source/archive/rendered-v4';record=json.loads((archive/'render-record.json').read_text())
        self.assertEqual(hashlib.sha256((archive/'Rose-prefabs.blend').read_bytes()).hexdigest(),record['blend_sha256'])
        self.assertEqual(len(record['assets']),116)
        for asset in record['assets']:
            self.assertEqual(hashlib.sha256((ROOT/'static/art'/asset['image']).read_bytes()).hexdigest(),asset['sha256'])

    def test_repaletted_bodies_preserve_every_alpha_pixel_and_registration(self):
        before=json.loads((ROOT/'art-source/archive/rendered-v4/art-manifest-rendered.json').read_text())
        for model in [*self.manifest['visual_catalog']['profiles'],'construct']:
            for key in [model,*([model+'_tone1',model+'_tone2'] if model!='construct' else [])]:
                a,b=self.manifest['assets'][key],before['assets'][key]
                with Image.open(ROOT/'static'/a['image'].lstrip('/')) as current, Image.open(ROOT/'static'/b['image'].lstrip('/')) as previous:
                    self.assertEqual(current.convert('RGBA').getchannel('A').tobytes(),previous.convert('RGBA').getchannel('A').tobytes())
                for field in ['anchor','scale','frames','clips']:self.assertEqual(a[field],b[field])

    def test_regional_paths_are_opaque_distinct_and_registered_with_their_floor(self):
        hashes=[]
        for region in self.manifest['visual_catalog']['regions']:
            path=self.manifest['assets']['ground_path_'+region];floor=self.manifest['assets']['ground_'+region]
            self.assertEqual(path['kind'],'texture')
            for field in ['anchor','scale','frames','clips']:self.assertEqual(path[field],floor[field])
            with Image.open(ROOT/'static'/path['image'].lstrip('/')) as p,Image.open(ROOT/'static'/floor['image'].lstrip('/')) as f:
                self.assertEqual(p.convert('RGBA').getchannel('A').getextrema(),(255,255))
                self.assertNotEqual(p.tobytes(),f.tobytes());hashes.append(hashlib.sha256(p.tobytes()).hexdigest())
        self.assertEqual(len(set(hashes)),4)

    def test_v5_source_and_every_archived_atlas_remain_byte_identical(self):
        archive=ROOT/'art-source/archive/rendered-v5';record=json.loads((archive/'render-record.json').read_text())
        self.assertEqual(hashlib.sha256((archive/'Rose-prefabs.blend').read_bytes()).hexdigest(),record['blend_sha256'])
        for a in record['assets']:self.assertEqual(hashlib.sha256((ROOT/'static/art'/a['image']).read_bytes()).hexdigest(),a['sha256'])

    def test_spectrum_practicals_source_sampling_and_recipe_match(self):
        catalog=json.loads((ROOT/'art-source/render-catalog.json').read_text());count=0
        for key,record in catalog['models'].items():
            if record['camera_kind']=='character':self.assertEqual(record['supersample'],1)
            else:
                self.assertEqual(record['samples'],96);self.assertEqual(record['supersample'],2);self.assertEqual(record['adaptive_threshold'],.035);self.assertEqual(record['adaptive_min_samples'],24)
                count+=len(record['practicals'])
        self.assertEqual(count,34)
        data=json.loads((ROOT/'art-source/render-record.json').read_text())['renderer']
        recipe=b''.join((ROOT/p).read_bytes() for p in ['art-source/Rose-prefabs.blend','tools/render_saved_blend.py','tools/render_blender.py','tools/spectrum_models.py','static/lighting-signatures.json'])
        self.assertEqual(hashlib.sha256(recipe).hexdigest(),data['source_sha256'])
        checks=ROOT/'art-source/archive/rendered-v5/raw-body-checksums.json';self.assertEqual(hashlib.sha256(checks.read_bytes()).hexdigest(),data['retained_body_checksums_sha256'])
        proof=json.loads((ROOT/'art-source/body-reuse-proof-v6.json').read_text());archive=ROOT/'art-source/archive/rendered-v5'
        self.assertEqual(proof['inherited_source_sha256'],hashlib.sha256((archive/'Rose-prefabs.blend').read_bytes()).hexdigest())
        self.assertEqual(proof['inherited_proof_sha256'],hashlib.sha256((archive/'body-reuse-proof-v5.json').read_bytes()).hexdigest())

    def test_two_repeated_spectrum_frames_retain_pixels_and_recipe(self):
        proof=json.loads((ROOT/'art-source/repeat-render-v6.json').read_text());record=json.loads((ROOT/'art-source/render-record.json').read_text())
        self.assertEqual(proof['renderer']['blend_sha256'],record['blend_sha256']);self.assertEqual(proof['renderer']['source_sha256'],record['renderer']['source_sha256']);self.assertEqual(len(proof['frames']),2)
        self.assertTrue(all(n['identical_rgba'] and n['max_channel_delta']==0 for n in proof['frames']))


if __name__ == '__main__':
    unittest.main()
