"""Downsample actual Blender frames, lock a common palette and register sprite atlases.

Developer dependency: Pillow. Game runtime dependencies remain unchanged.
python tools/export_sprites.py --input build/art
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def pixels(image):
    reader = getattr(image, 'get_flattened_data', None)
    return reader() if reader else image.getdata()


def load_frames(folder, catalog):
    result = {}
    root = folder.resolve()
    for key, record in catalog['models'].items():
        w, h = record['size']
        frames = []
        for filename in record['frames']:
            path = (root / filename).resolve()
            if not path.is_relative_to(root):
                raise ValueError('Frame path escapes the render folder')
            with Image.open(path) as source:
                ss = catalog['render']['supersample']
                if source.size != (w * ss, h * ss):
                    raise ValueError(f'{filename}: expected {w * ss}×{h * ss}; got {source.size}')
                rgba = source.convert('RGBA')
                if record['kind'] == 'texture':
                    # A ground fill samples the central relief, avoiding the
                    # edge of the finite modeling plane in a dimetric render.
                    sw, sh = rgba.size
                    rgba = rgba.crop((sw // 4, sh // 4, sw * 3 // 4, sh * 3 // 4))
                # Pillow performs RGBA resizing in premultiplied-alpha space.
                frame = rgba.resize((w, h), Image.Resampling.LANCZOS)
                if record['kind'] == 'texture' and frame.getchannel('A').getextrema() != (255, 255):
                    raise ValueError(filename + ': ground relief sample must be opaque')
            if record['kind'] == 'sprite':
                bounds = frame.getchannel('A').point(lambda a: 255 if a >= 128 else 0).getbbox()
                if not bounds:
                    raise ValueError(filename + ': empty model render')
                if bounds[0] < 1 or bounds[1] < 1 or bounds[2] > w - 1 or bounds[3] > h - 1:
                    raise ValueError(filename + ': model crosses the fixed cell boundary; enlarge the camera frame')
            frames.append(frame)
        result[key] = frames
    return result


def learn_palette(frames):
    samples = []
    for key, images in frames.items():
        for image in images:
            eligible = [rgb[:3] for rgb in pixels(image) if rgb[3] >= 224]
            if not eligible:
                continue
            budget = 12000 if key.startswith('ground_') else 1200
            stride = max(1, math.ceil(len(eligible) / budget))
            samples.extend(eligible[::stride])
    if not samples:
        raise ValueError('No opaque source colors to learn')
    sample = Image.new('RGB', (len(samples), 1))
    sample.putdata(samples)
    quantized = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    rgb = quantized.getpalette()[:765]
    return [[0, 0, 0]] + [rgb[i:i + 3] for i in range(0, 765, 3)]


def indexed(image, colors, dither=True):
    if len(colors) != 256 or any(len(c) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in c) for c in colors):
        raise ValueError('Palette must contain exactly 256 RGB entries')
    # The temporary quantizer contains only opaque colors. Its padding duplicates
    # the last opaque entry, so index zero can never erase a dark opaque pixel.
    temporary = Image.new('P', (1, 1))
    temporary.putpalette([v for c in colors[1:] + [colors[-1]] for v in c])
    source = image.convert('RGBA')
    quantized = source.convert('RGB').quantize(palette=temporary, dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE)
    indices, alpha = list(pixels(quantized)), list(pixels(source.getchannel('A')))
    width, height = image.size
    data = []
    for i, (value, opacity) in enumerate(zip(indices, alpha)):
        threshold = (BAYER[(i // width) % 4][(i % width) % 4] + 0.5) * 255 / 16
        data.append(min(value, 254) + 1 if opacity > threshold else 0)
    result = Image.new('P', (width, height))
    result.putpalette([v for color in colors for v in color])
    result.putdata(data)
    result.info['transparency'] = 0
    return result


def atlas(images, size, colors, columns=8):
    w, h = size
    columns = min(columns, len(images))
    sheet = Image.new('P', (columns * w, math.ceil(len(images) / columns) * h))
    sheet.putpalette([v for color in colors for v in color])
    sheet.info['transparency'] = 0
    frames = []
    for index, source in enumerate(images):
        x, y = index % columns * w, index // columns * h
        sheet.paste(indexed(source, colors), (x, y))
        frames.append([x, y, w, h])
    return sheet, frames


def preview(manifest, destination):
    canvas = Image.new('RGB', (1160, 760), '#111b18')
    draw = ImageDraw.Draw(canvas)
    font_path = Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
    font = ImageFont.truetype(str(font_path), 14) if font_path.exists() else ImageFont.load_default()
    small = ImageFont.truetype(str(font_path), 12) if font_path.exists() else font
    draw.text((30, 24), 'ROSE / ORIGINAL 3D PREFABS', font=font, fill='#d1bdad')
    draw.text((30, 48), 'BLENDER CYCLES  /  SIX FACINGS  /  ONE 256-ENTRY PALETTE', font=small, fill='#86b3a0')
    keys = ['power', 'water', 'garden', 'shelter', 'workshop', 'exchange', 'relay', 'rock']
    for n, key in enumerate(keys):
        x, y = 35 + n % 4 * 283, 92 + n // 4 * 235
        draw.rectangle((x, y, x + 252, y + 211), fill='#202923', outline='#425347')
        asset = manifest['assets'][key]
        with Image.open(ROOT / 'static' / asset['image'].lstrip('/')) as sheet:
            sx, sy, w, h = asset['frames'][0]
            frame = sheet.crop((sx, sy, sx + w, sy + h)).convert('RGBA')
            # Exact 1x pixels; the lower row of facings is also shown at 1x.
            canvas.paste(frame, (x + (252 - w) // 2, y + 16), frame)
        draw.text((x + 16, y + 184), key.upper(), font=small, fill='#b8c3a3')
    draw.text((35, 575), 'TRAVELER / SIX DIRECTIONS', font=small, fill='#cfb0b7')
    actor = manifest['assets']['player']
    with Image.open(ROOT / 'static' / actor['image'].lstrip('/')) as sheet:
        for direction, label in enumerate(['E', 'NE', 'NW', 'W', 'SW', 'SE']):
            i = actor['clips'][f'idle_{direction}'][0]
            sx, sy, w, h = actor['frames'][i]
            frame = sheet.crop((sx, sy, sx + w, sy + h)).convert('RGBA')
            x = 58 + direction * 134
            canvas.paste(frame, (x, 597), frame)
            draw.text((x + 35, 715), label, font=small, fill='#acc4ac')
    draw.text((907, 600), 'PALETTE', font=small, fill='#86b3a0')
    colors = manifest['palette']['rgb']
    for i, color in enumerate(colors):
        x, y = 908 + i % 16 * 11, 625 + i // 16 * 7
        draw.rectangle((x, y, x + 10, y + 6), fill=tuple(color))
    canvas.save(destination)


def preview_walk(manifest, destination):
    """Eight real walk poses, in six facings, with the shared palette intact."""
    colors = manifest['palette']['rgb']
    nearest = lambda rgb: min(range(1, 256), key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb, colors[i])))
    background, ink, line = nearest((17, 27, 24)), nearest((174, 195, 162)), nearest((54, 75, 59))
    frames = []
    actor = manifest['assets']['player']
    with Image.open(ROOT / 'static' / actor['image'].lstrip('/')) as sheet:
        count = manifest['animations']['walk']['frames']
        for n in range(count):
            canvas = Image.new('P', (828, 194), background)
            canvas.putpalette([v for color in colors for v in color])
            draw = ImageDraw.Draw(canvas)
            draw.text((22, 16), 'ROSE / BLENDER WALK CYCLE / SIX FACINGS', fill=ink)
            for direction, label in enumerate(['E', 'NE', 'NW', 'W', 'SW', 'SE']):
                i = actor['clips'][f'walk_{direction}'][n]
                x, y, w, h = actor['frames'][i]
                cell = sheet.crop((x, y, x + w, y + h))
                cx, cy = 22 + direction * 132, 35
                draw.line((cx + 26, cy + actor['anchor'][1], cx + 103, cy + actor['anchor'][1]), fill=line)
                mask = cell.convert('RGBA').getchannel('A')
                canvas.paste(cell, (cx, cy), mask)
                draw.text((cx + 58, 170), label, fill=ink)
            frames.append(canvas)
    frames[0].save(destination, save_all=True, append_images=frames[1:],
                   duration=manifest['animations']['walk']['frame_ms'], loop=0, disposal=2, optimize=False)


def export(folder, palette_path, relearn=False):
    catalog = json.loads((folder / 'catalog.json').read_text())
    source = ROOT / 'art-source/Rose-prefabs.blend'
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if catalog['render'].get('blend_sha256') and catalog['render']['blend_sha256'] != source_sha:
        raise ValueError('The rendered source must match art-source/Rose-prefabs.blend before exporting an editable game pack')
    required = {'traveler', 'construct', 'power', 'water', 'garden', 'shelter', 'workshop', 'exchange', 'relay', 'rock',
                'ground_WN_TOWER', 'ground_CITY_CLOUD_S', 'ground_ENACT_HILLS', 'ground_AETHERGALE'}
    if set(catalog['models']) != required:
        raise ValueError('A complete render catalog is required to export the game style')
    images = load_frames(folder, catalog)
    if palette_path.exists() and not relearn:
        colors = json.loads(palette_path.read_text())['rgb']
    else:
        colors = learn_palette(images)
        palette_path.parent.mkdir(parents=True, exist_ok=True)
        palette_path.write_text(json.dumps({'schema': 1, 'transparent_index': 0, 'rgb': colors,
                                          'trained_from_source_sha256': catalog['render']['source_sha256']}, indent=2) + '\n')
    manifest = {'schema': 1, 'style': 'rendered', 'license': 'Original Rose meshes and renders; no Fallout assets included.',
                'provenance': catalog['provenance'], 'projection': catalog['projection'], 'animations': catalog['animations'],
                'palette': {'entries': 256, 'transparent_index': 0, 'rgb': colors,
                            'rgb_dither': 'FLOYDSTEINBERG', 'alpha_dither': 'BAYER_4X4'}, 'assets': {}}
    receipts = []
    for model, frames in images.items():
        record = catalog['models'][model]
        sheet, regions = atlas(frames, record['size'], colors)
        filename = f'rose-3d-{model.replace("_", "-").lower()}-v2.png'
        path = ROOT / 'static/art' / filename
        sheet.save(path, optimize=True, transparency=0)
        asset = {'kind': record['kind'], 'image': '/art/' + filename, 'frames': regions,
                 'anchor': record['anchor'], 'scale': 1, 'clips': record['clips']}
        if model == 'traveler':
            asset['note'] = 'Shared provisional traveler mesh; biography and stats are individually registered. Body and equipped-item variants are future assets.'
            for key in ('player', 'companion', 'npc'):
                manifest['assets'][key] = asset.copy()
        elif model == 'construct':
            manifest['assets']['threat'] = asset
        else:
            manifest['assets'][model] = asset
        receipts.append({'asset': model, 'frames': len(frames), 'image': filename,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'size': list(sheet.size),
                         'anchor': record['anchor']})
    # Write the manifest only after every atlas has been exported successfully.
    (ROOT / 'static/art-manifest-rendered.json').write_text(json.dumps(manifest, indent=2) + '\n')
    record = {'schema': 1, 'renderer': catalog['render'], 'frame_count': sum(len(f) for f in images.values()),
              'blend_sha256': source_sha, 'assets': receipts}
    (ROOT / 'art-source/render-record.json').write_text(json.dumps(record, indent=2) + '\n')
    preview(manifest, ROOT / 'docs/Rose-3D-prefabs-preview.png')
    preview_walk(manifest, ROOT / 'docs/Rose-3D-walk-preview.gif')
    print('Exported', record['frame_count'], 'rendered frames,', len(receipts), 'atlases and', len(manifest['assets']), 'game entries.')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--palette', type=Path, default=ROOT / 'art-source/rose-palette-v2.json')
    parser.add_argument('--rebuild-palette', action='store_true', help='Explicitly relearn the common palette from every raw frame.')
    opts = parser.parse_args()
    export(opts.input, opts.palette, opts.rebuild_palette)


if __name__ == '__main__':
    main()
