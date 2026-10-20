"""Render artist-edited Rose meshes and keyframes without rebuilding their geometry.

blender --background --python tools/render_saved_blend.py -- --output build/edited-art
Edit and save art-source/Rose-prefabs.blend first. This tool reads that file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_blender as studio
import spectrum_models


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--blend', type=Path, default=studio.ROOT / 'art-source/Rose-prefabs.blend')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--frames', help='Comma-separated timeline frames for a partial visual check; not a complete export.')
    parser.add_argument('--models', help='Comma-separated model names for an independent render shard.')
    parser.add_argument('--threads',type=int,help='CPU worker threads per shard; 1–64.')
    opts = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(opts.blend.resolve()))
    catalog = json.loads(bpy.data.texts['Rose sprite catalog.json'].as_string())
    models=set(opts.models.split(',')) if opts.models else set(catalog['models'])
    if not models.issubset(catalog['models']): parser.error('Unknown model in --models')
    selected = {int(n) for n in opts.frames.split(',')} if opts.frames else None
    available = {n for record in catalog['models'].values() for n in record['timeline_frames']}
    if selected is not None and not selected.issubset(available):
        parser.error('Requested frames are not present in the saved catalog')
    studio.CFG = catalog['settings']
    cfg = studio.CFG['render']
    threads=opts.threads if opts.threads is not None else cfg['threads']
    if not 1<=threads<=64:parser.error('threads must be 1–64')
    source_hash = hashlib.sha256(opts.blend.read_bytes() + Path(__file__).read_bytes() + Path(studio.__file__).read_bytes()
                                 + Path(spectrum_models.__file__).read_bytes() + (studio.ROOT/'static/lighting-signatures.json').read_bytes()).hexdigest()
    identity = {'source_sha256': source_hash, 'blend_sha256': hashlib.sha256(opts.blend.read_bytes()).hexdigest(),
                'blender': bpy.app.version_string, 'samples': cfg['samples'], 'supersample': cfg['supersample'],
                'mode': 'saved-blend','threads':threads,'texture_supersample':cfg.get('texture_supersample',cfg['supersample'])}
    opts.output.mkdir(parents=True, exist_ok=True)
    identity_path = opts.output / 'render-identity.json'
    if opts.resume and (not identity_path.exists() or json.loads(identity_path.read_text()) != identity):
        parser.error('--resume requires the same saved blend, scripts, Blender and settings')
    identity_path.write_text(json.dumps(identity, indent=2) + '\n')
    catalog['render'] = identity
    output_catalog={**catalog,'models':{k:v for k,v in catalog['models'].items() if k in models}}
    (opts.output / ('catalog-partial.json' if selected is not None or opts.models else 'catalog.json')).write_text(json.dumps(output_catalog, indent=2) + '\n')
    studio.COLLECTIONS.update({c.name: c for c in bpy.context.scene.collection.children if c.name != 'Collection'})
    scene = bpy.context.scene
    original_adaptive=(scene.cycles.use_adaptive_sampling,scene.cycles.adaptive_threshold,scene.cycles.adaptive_min_samples)
    scene.render.engine = 'CYCLES'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    scene.render.film_transparent = True
    scene.render.resolution_percentage = 100
    scene.render.use_persistent_data = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = threads
    scene.cycles.device = 'CPU'
    scene.cycles.samples = cfg['samples']
    scene.cycles.use_denoising = True
    scene.cycles.seed = cfg['seed']
    scene.cycles.use_animated_seed = False
    floor = bpy.data.objects['Shadow catcher / never changes registration']
    done = 0
    for model, record in catalog['models'].items():
        if model not in models: continue
        studio.visibility(model)
        spectrum_models.configure(scene, studio.CFG, record.get('lighting_signature'))
        scene.cycles.samples = record.get('samples', cfg['samples'])
        scene.cycles.use_adaptive_sampling=True if 'adaptive_threshold' in record else original_adaptive[0]
        scene.cycles.adaptive_threshold=record.get('adaptive_threshold',original_adaptive[1])
        scene.cycles.adaptive_min_samples=record.get('adaptive_min_samples',original_adaptive[2])
        floor.hide_render = model.startswith('ground_')
        kind = record.get('camera_kind', 'character' if model in ('traveler', 'construct') else 'environment')
        if len(record['timeline_frames']) != len(record['frames']):
            raise ValueError('Timeline and render frames must have equal lengths')
        for frame, filename in zip(record['timeline_frames'], record['frames']):
            if selected is not None and frame not in selected:
                continue
            scene.frame_set(frame)
            anchor = studio.camera(scene, kind, record.get('supersample',cfg['supersample']))
            if any(abs(a - b) > 0.001 for a, b in zip(anchor, record['anchor'])):
                raise ValueError('Saved camera registration differs from the render catalog')
            path = (opts.output / filename).resolve()
            if not path.is_relative_to(opts.output.resolve()):
                raise ValueError('Catalog frame path escapes the output directory')
            path.parent.mkdir(parents=True, exist_ok=True)
            if not (opts.resume and path.exists()):
                scene.render.filepath = str(path)
                bpy.ops.render.render(write_still=True)
            done += 1
            print(f'ROSE FRAME {done}: {filename}', flush=True)
    print('ROSE COMPLETE:', done, 'frames from saved editable geometry.', flush=True)


if __name__ == '__main__':
    main()
