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
    canvas = Image.new('RGB', (1160, 860), '#111b18')
    draw = ImageDraw.Draw(canvas)
    font_path = Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
    font = ImageFont.truetype(str(font_path), 14) if font_path.exists() else ImageFont.load_default()
    small = ImageFont.truetype(str(font_path), 12) if font_path.exists() else font
    draw.text((30, 24), 'ROSE / ORIGINAL 3D PREFABS', font=font, fill='#d1bdad')
    draw.text((30, 48), 'BLENDER CYCLES  /  SIX FACINGS  /  ONE 256-ENTRY PALETTE', font=small, fill='#86b3a0')
    keys = ['power', 'water', 'garden', 'shelter', 'workshop', 'exchange', 'relay', 'rock']
    for n, key in enumerate(keys):
        x, y = 35 + n % 4 * 283, 92 + n // 4 * 275
        draw.rectangle((x, y, x + 252, y + 255), fill='#202923', outline='#425347')
        asset = manifest['assets'][key]
        with Image.open(ROOT / 'static' / asset['image'].lstrip('/')) as sheet:
            sx, sy, w, h = asset['frames'][0]
            frame = sheet.crop((sx, sy, sx + w, sy + h)).convert('RGBA')
            # Exact 1x pixels; the lower row of facings is also shown at 1x.
            canvas.paste(frame, (x + (252 - w) // 2, y + 16), frame)
        draw.text((x + 16, y + 235), key.upper(), font=small, fill='#b8c3a3')
    draw.text((35, 665), 'TRAVELER / SIX DIRECTIONS', font=small, fill='#cfb0b7')
    actor = manifest['assets']['player']
    with Image.open(ROOT / 'static' / actor['image'].lstrip('/')) as sheet:
        for direction, label in enumerate(['E', 'NE', 'NW', 'W', 'SW', 'SE']):
            i = actor['clips'][f'idle_{direction}'][0]
            sx, sy, w, h = actor['frames'][i]
            frame = sheet.crop((sx, sy, sx + w, sy + h)).convert('RGBA')
            x = 58 + direction * 134
            canvas.paste(frame, (x, 687), frame)
            draw.text((x + 35, 805), label, font=small, fill='#acc4ac')
    draw.text((907, 690), 'PALETTE', font=small, fill='#86b3a0')
    colors = manifest['palette']['rgb']
    for i, color in enumerate(colors):
        x, y = 908 + i % 16 * 11, 715 + i // 16 * 7
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


def preview_individuals(manifest, destination):
    """Exact exported pixels at integer magnification, with honest family labels."""
    canvas=Image.new('RGB',(1420,1180),'#161d18');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',15)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',12)
    draw.text((30,22),'ROSE / INDIVIDUAL FIELD PREFABS',font=font,fill='#ddc6ad')
    draw.text((30,49),'ACTUAL INDEXED SPRITES / 2x NEAREST PIXELS / ORIGINAL BLENDER SOURCE',font=small,fill='#a0b49a')
    def cell(key,pose,direction,x,y,scale=2):
        a=manifest['assets'][key];clip=a['clips'].get(f'{pose}_{direction}',a['clips'].get(pose));i=clip[0]
        sx,sy,w,h=a['frames'][i]
        with Image.open(ROOT/'static'/a['image'].lstrip('/')) as sheet:
            f=sheet.crop((sx,sy,sx+w,sy+h)).convert('RGBA')
            if w>128:
                f=f.crop(f.getbbox())
                x+=(256-f.width*scale)//2
            f=f.resize((f.width*scale,f.height*scale),Image.Resampling.NEAREST)
            canvas.paste(f,(x,y),f)
    for i,(key,info) in enumerate(manifest['visual_catalog']['profiles'].items()):
        x=26+i*280;draw.rectangle((x,82,x+262,360),fill='#2b3125',outline='#4b5544');cell(key,'idle',4,x+3,94)
        draw.text((x+12,337),info['label'],font=small,fill='#d3c8ab')
    draw.text((30,388),'THE SAME WORKSHOP FUNCTION / FOUR REGIONAL CONSTRUCTIONS',font=small,fill='#a0b49a')
    for i,region in enumerate(manifest['visual_catalog']['regions']):
        x=35+i*346;draw.rectangle((x,418,x+320,771),fill='#282f24',outline='#4b5544');cell('workshop_'+region,'idle',0,x+32,424)
        draw.text((x+16,744),region, font=small,fill='#d3c8ab')
    draw.text((30,803),'REGIONAL SHELTERS / MATERIAL AND SILHOUETTE VARIATION',font=small,fill='#a0b49a')
    for i,region in enumerate(manifest['visual_catalog']['regions']):
        x=35+i*346;draw.rectangle((x,835,x+320,1166),fill='#282f24',outline='#4b5544');cell('shelter_'+region,'idle',0,x+32,840)
        draw.text((x+16,1143),region,font=small,fill='#d3c8ab')
    canvas.save(destination)


def export(folder, palette_path, relearn=False):
    catalog = json.loads((folder / 'catalog.json').read_text())
    source = ROOT / 'art-source/Rose-prefabs.blend'
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if catalog['render'].get('blend_sha256') and catalog['render']['blend_sha256'] != source_sha:
        raise ValueError('The rendered source must match art-source/Rose-prefabs.blend before exporting an editable game pack')
    designs = json.loads((ROOT / 'static/visual-catalog.json').read_text())
    required = {*designs['profiles'], 'construct', *[kind+'_'+region for kind in designs['structures'] for region in designs['regions']],
                *['rock_'+region for region in designs['regions']], *['ground_'+region for region in designs['regions']]}
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
                'provenance': catalog['provenance'], 'projection': catalog['projection'], 'animations': catalog['animations'], 'visual_catalog': designs,
                'palette': {'entries': 256, 'transparent_index': 0, 'rgb': colors,
                            'rgb_dither': 'FLOYDSTEINBERG', 'alpha_dither': 'BAYER_4X4'}, 'assets': {}}
    receipts = []
    tone_luts = {tone: [0]+[min(range(1,256),key=lambda j:sum((colors[j][k]-colors[i][k]*gains[k])**2 for k in range(3))) for i in range(1,256)] for tone,gains in [(1,(.94,1.015,1.065)),(2,(1.055,1.005,.93))]}
    for model, frames in images.items():
        record = catalog['models'][model]
        sheet, regions = atlas(frames, record['size'], colors)
        filename = f'rose-3d-{model.replace("_", "-").lower()}-v3.png'
        path = ROOT / 'static/art' / filename
        sheet.save(path, optimize=True, transparency=0)
        asset = {'kind': record['kind'], 'image': '/art/' + filename, 'frames': regions,
                 'anchor': record['anchor'], 'scale': 1, 'clips': record['clips']}
        manifest['assets'][model] = asset
        receipts.append({'asset': model, 'frames': len(frames), 'image': filename,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'size': list(sheet.size),
                         'anchor': record['anchor']})
        if not model.startswith('ground_') and model != 'construct':
            for tone, gains in [(1,(.94,1.015,1.065)),(2,(1.055,1.005,.93))]:
                # A shared palette lookup changes patina without altering alpha,
                # registration or clips. These are treatments, not new 3D bodies.
                lut=tone_luts[tone]
                toned=sheet.point(lut);toned.putpalette(sheet.getpalette());toned.info['transparency']=0
                variant_file=filename.replace('-v3.png',f'-tone{tone}-v3.png')
                variant_path=ROOT/'static/art'/variant_file;toned.save(variant_path,optimize=True,transparency=0)
                manifest['assets'][model+'_tone'+str(tone)]={**asset,'image':'/art/'+variant_file,'treatment':designs['tones'][tone]}
                receipts.append({'asset':model+'_tone'+str(tone),'derived_from':model,'frames':len(frames),'image':variant_file,
                                 'sha256':hashlib.sha256(variant_path.read_bytes()).hexdigest(),'size':list(toned.size),'anchor':record['anchor']})
    for alias, model in [('player','traveler'),('npc','traveler'),('companion','traveler'),('threat','construct'),
                         *[(kind,kind+'_WN_TOWER') for kind in [*designs['structures'],'rock']]]:
        manifest['assets'][alias]=manifest['assets'][model].copy()
    # Write the manifest only after every atlas has been exported successfully.
    (ROOT / 'static/art-manifest-rendered.json').write_text(json.dumps(manifest, indent=2) + '\n')
    record = {'schema': 1, 'renderer': catalog['render'], 'frame_count': sum(len(f) for f in images.values()), 'modeled_families':len(images),
              'blend_sha256': source_sha, 'assets': receipts}
    (ROOT / 'art-source/render-record.json').write_text(json.dumps(record, indent=2) + '\n')
    preview(manifest, ROOT / 'docs/Rose-3D-prefabs-preview.png')
    preview_walk(manifest, ROOT / 'docs/Rose-3D-walk-preview.gif')
    preview_individuals(manifest, ROOT / 'docs/Rose-individual-prefabs-preview.png')
    print('Exported', record['frame_count'], 'rendered frames,', len(receipts), 'atlases and', len(manifest['assets']), 'game entries.')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--palette', type=Path, default=ROOT / 'art-source/rose-palette-v3.json')
    parser.add_argument('--rebuild-palette', action='store_true', help='Explicitly relearn the common palette from every raw frame.')
    opts = parser.parse_args()
    export(opts.input, opts.palette, opts.rebuild_palette)


if __name__ == '__main__':
    main()
