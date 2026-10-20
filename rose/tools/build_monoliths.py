"""Author solid 3D monument meshes and bake their fixed dimetric sprite bank.

This separate software mesh rasterizer leaves the original Blender assets
untouched. Developer dependencies: NumPy and Pillow. Runtime uses only PNGs.
python3 tools/build_monoliths.py
"""
from pathlib import Path
import hashlib
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_sprites import indexed, alpha_table

ROOT = Path(__file__).resolve().parents[1]
SIZE = (640, 832)
ANCHOR = (224, 606)
PIXELS = 48
COMPRESSION = .52
VERTICAL = math.sqrt(1 - COMPRESSION ** 2)
LIGHT = np.array((.70710678, -4.94974747, 7.0))
LIGHT_UNIT = LIGHT / np.linalg.norm(LIGHT)
VIEW = np.array((VERTICAL / math.sqrt(2), -VERTICAL / math.sqrt(2), COMPRESSION))
DESIGNS = {
    'power': dict(height=10.4, radius=.78, purpose='Collector backbone', crown=.68),
    'water': dict(height=7.8, radius=.86, purpose='Reservoir monolith', crown=.82),
    'relay': dict(height=12.6, radius=.72, purpose='Route signal monument', crown=.50),
}
MATERIALS = {
    'WN_TOWER': dict(base=[73, 79, 57], grain=11, vein=[103, 112, 74], material='mineralized darkwood', roughness=.88),
    'ENACT_HILLS': dict(base=[110, 95, 70], grain=10, vein=[163, 141, 95], material='worked basalt and earth composite', roughness=.93),
    'CITY_CLOUD_S': dict(base=[64, 76, 86], grain=8, vein=[88, 114, 121], material='solid alloy and ceramic', roughness=.64),
    'AETHERGALE': dict(base=[91, 85, 107], grain=9, vein=[130, 148, 140], material='dense faceted crystal', roughness=.56),
}


def project(vertex, ss=1):
    x, y, z = vertex
    return ((ANCHOR[0] + PIXELS * (x + y) / math.sqrt(2)) * ss,
            (ANCHOR[1] + PIXELS * ((x - y) * COMPRESSION / math.sqrt(2) - z * VERTICAL)) * ss)


def model(kind, region):
    design = DESIGNS[kind]
    height, radius = design['height'], design['radius']
    levels = [(0, radius), (.18, radius), (.32, radius * .90),
              (1.0, radius * .87), (height * .35, radius * .82),
              (height * .72, radius * .77), (height - .25, radius * design['crown']),
              (height, radius * design['crown'] * .87)]
    vertices, faces = [], []
    for z, r in levels:
        bend = .035 * math.sin(z / height * math.pi) if region == 'WN_TOWER' else 0
        for i in range(8):
            angle = math.pi / 8 + i * math.pi / 4
            vertices.append([round(math.cos(angle) * r + bend, 7), round(math.sin(angle) * r, 7), z])
    for level in range(len(levels) - 1):
        for i in range(8):
            faces.append([level * 8 + i, level * 8 + (i + 1) % 8,
                          (level + 1) * 8 + (i + 1) % 8, (level + 1) * 8 + i])
    faces.append(list(range((len(levels) - 1) * 8, len(levels) * 8)))
    faces.append(list(range(7, -1, -1)))
    return dict(kind=kind, region=region, design=design, material=MATERIALS[region],
                vertices=vertices, faces=faces, solid=True,
                service_anchor=[0, 0, 0], footprint_radius=radius,
                provenance='Original parameterized 3D mesh; orthographic software rasterization, 2x supersampling, locked v6 palette.')


def render(record, worn=False):
    ss = 2
    w, h = SIZE
    image = Image.new('RGBA', (w * ss, h * ss))
    vertices = np.array(record['vertices'], dtype=float)
    seed = int(hashlib.sha256((record['kind'] + record['region']).encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    # Project the actual mesh along the directional light onto the ground.
    shadow = [project((x - z * LIGHT[0] / LIGHT[2], y - z * LIGHT[1] / LIGHT[2], 0), ss)
              for x, y, z in vertices]
    shadow_mask = Image.new('L', image.size)
    sd = ImageDraw.Draw(shadow_mask)
    for face in record['faces']:
        sd.polygon([shadow[i] for i in face], fill=54)
    image.putalpha(shadow_mask)
    faces = []
    for face in record['faces']:
        points = vertices[face]
        normal = np.cross(points[1] - points[0], points[2] - points[0])
        normal /= np.linalg.norm(normal)
        if normal @ VIEW <= 0:
            continue
        faces.append((points.mean(axis=0) @ VIEW, points, normal))
    for index, (_, points, normal) in enumerate(sorted(faces, key=lambda f: f[0])):
        xy = [project(p, ss) for p in points]
        mask = Image.new('L', image.size)
        ImageDraw.Draw(mask).polygon(xy, fill=255)
        box = mask.getbbox()
        if not box:
            continue
        x0, y0, x1, y1 = box
        width, height = x1 - x0, y1 - y0
        yy, xx = np.mgrid[y0:y1, x0:x1]
        grain = rng.normal(0, record['material']['grain'], (height, width))
        # Mineral variation and fine directional pores, never screen-cell tiles.
        strata = 3.5 * np.sin(xx / ss * .17 + yy / ss * .038 + index)
        pores = np.where(rng.random((height, width)) < .025, -14, 0)
        light = .37 + .72 * max(0, float(normal @ LIGHT_UNIT))
        base = np.array(record['material']['base']) * light * (.73 if worn else 1)
        rgb = np.clip(base + (grain + strata + pores)[..., None], 0, 255).astype('uint8')
        # A restrained vertical seam and worn edges give the mass a readable scale.
        seam = (np.sin(xx / ss * .22 + index * 1.8) > .995) & (yy % (ss * 29) < ss * 21)
        rgb[seam] = np.clip(rgb[seam].astype(float) * .65, 0, 255)
        layer = Image.fromarray(rgb).convert('RGBA')
        if worn:
            center = points.mean(axis=0)
            a = project(center, ss)
            # Keep damage on its physical face, including low base courses.
            damage = [(a[0] - x0, a[1] - y0),
                      (a[0] + 4 * ss - x0, a[1] + 9 * ss - y0),
                      (a[0] - 2 * ss - x0, a[1] + 16 * ss - y0)]
            ImageDraw.Draw(layer).line(damage, fill=(24, 29, 26, 255), width=ss)
        image.paste(layer, (x0, y0), mask.crop(box))
    frame = image.resize(SIZE, Image.Resampling.LANCZOS)
    # Bounds must leave space for physical opaque geometry; shadows are separate.
    opaque = frame.getchannel('A').point(lambda a: 255 if a >= 248 else 0).getbbox()
    if not opaque or opaque[0] < 2 or opaque[1] < 2 or opaque[2] > w - 2 or opaque[3] > h - 2:
        raise ValueError('Monument exceeds its registered frame: ' + record['kind'] + record['region'])
    return frame


def main():
    source = ROOT / 'art-source/monoliths-v1'
    source.mkdir(exist_ok=True)
    catalog = dict(schema=1, projection=dict(azimuth_degrees=-45, ground_compression=COMPRESSION,
                   pixels_per_world_unit=PIXELS, size=list(SIZE), anchor=list(ANCHOR), runtime_scale=2 / 3),
                   renderer='Original software 3D mesh rasterizer; not a new Blender/Cycles bake.',
                   models={})
    palette = json.loads((ROOT / 'art-source/rose-palette-v6.json').read_text())
    colors, shadow_levels = palette['rgb'], palette['shadow_alpha_levels']
    manifest_path = ROOT / 'static/art-manifest-rendered.json'
    manifest = json.loads(manifest_path.read_text())
    receipts = []
    for region in MATERIALS:
        for kind in DESIGNS:
            key = 'monolith_' + kind + '_' + region
            record = model(kind, region)
            catalog['models'][key] = record
            frames = [render(record, worn) for worn in [False, True]]
            sheet = Image.new('RGBA', (SIZE[0] * 2, SIZE[1]))
            for i, frame in enumerate(frames):
                sheet.paste(frame, (SIZE[0] * i, 0))
            quantized = indexed(sheet, colors, shadow_levels=shadow_levels)
            for i in range(2):
                frame = quantized.crop((SIZE[0] * i, 0, SIZE[0] * (i + 1), SIZE[1])).convert('RGBA')
                box = frame.getbbox()
                if not box or min(box[:2]) < 2 or box[2] > SIZE[0] - 2 or box[3] > SIZE[1] - 2:
                    raise ValueError('Indexed geometry or projected shadow exceeds frame: ' + key)
            filename = 'rose-' + key.replace('_', '-').lower() + '-v1.png'
            target = ROOT / 'static/art' / filename
            quantized.save(target, optimize=True, transparency=alpha_table(shadow_levels))
            manifest['assets'][key] = dict(kind='sprite', image='/art/' + filename,
                frames=[[0, 0, *SIZE], [SIZE[0], 0, *SIZE]], anchor=list(ANCHOR), scale=2 / 3,
                clips=dict(idle=[0], worn=[1]), pick_alpha_min=248,
                provenance=record['provenance'], footprint_radius=record['footprint_radius'])
            for base_key, asset in manifest['assets'].items():
                if base_key == kind + '_' + region or base_key.startswith(kind + '_' + region + '_tone'):
                    asset['monolith_core'] = key
            if region == 'WN_TOWER':
                manifest['assets'][kind]['monolith_core'] = key
            receipts.append(dict(asset=key, image=filename, frames=2, sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    catalog['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (source / 'models.json').write_text(json.dumps(catalog, indent=2) + '\n')
    (source / 'render-record.json').write_text(json.dumps(dict(schema=1, renderer=catalog['renderer'],
        source_sha256=catalog['source_sha256'], models=12, frames=24, assets=receipts), indent=2) + '\n')
    manifest['monolith_associations'] = dict(schema=1, core_functions=list(DESIGNS),
        scope='Vertical mass at existing solid node footprints; human-scale service modules and gameplay rules retained.',
        source='art-source/monoliths-v1/models.json', renderer=catalog['renderer'])
    manifest['provenance'] = ('Original Rose service, scenery and body meshes rendered in Blender Cycles, '
        'with separately authored solid monument meshes baked by the original software 3D rasterizer; '
        'both use fixed dimetric projection and the locked v6 indexed palette.')
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print('Prepared 12 original 3D monolith meshes and 24 indexed condition frames.')


if __name__ == '__main__':
    main()
