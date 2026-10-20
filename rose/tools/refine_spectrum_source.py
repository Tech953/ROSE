"""Apply spectrum materials/lights to preserved 0.8 scenery, proving body reuse."""
import hashlib
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_blender as studio
import spectrum_models
from body_dependencies import fingerprint


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=studio.ROOT
    archive=root/'art-source/archive/rendered-v5'
    source=root/'art-source/Rose-prefabs.blend'
    if sha(source)!=sha(archive/'Rose-prefabs.blend'):
        raise ValueError('Start from the preserved 0.8 source; this patch applies once')
    inherited=json.loads((archive/'body-reuse-proof-v5.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene
    catalog=json.loads(bpy.data.texts['Rose sprite catalog.json'].as_string())
    studio.CFG=catalog['settings']
    studio.COLLECTIONS.update({c.name:c for c in scene.collection.children if c.name!='Collection'})
    studio.MATERIALS.update({m.name:m for m in bpy.data.materials})
    studio.camera(scene,'character',studio.CFG['render']['supersample'])
    scene.frame_set(1)
    before={name:fingerprint(name,catalog) for name,record in catalog['models'].items() if record['camera_kind']=='character'}
    if any(before[k]!=inherited['models'][k]['after'] for k in before):
        raise ValueError('Inherited body dependency proof does not match the saved source')
    spectrum_models.refine(studio,catalog)
    after={name:fingerprint(name,catalog) for name in before}
    if before!=after:
        raise ValueError('Body/studio dependencies changed; a fresh body render is required')
    studio.CFG['art_direction']='spectrum-v6 / regional practical light, material response and doubled scenery sampling'
    catalog['provenance']='Original Rose 3D meshes, physical practical fixtures and regional RGB lighting rendered in Blender Cycles, downsampled into indexed sprites.'
    studio.visibility('traveler')
    embedded=bpy.data.texts['Rose sprite catalog.json']
    text=json.dumps(catalog,indent=2)+'\n'
    embedded.clear();embedded.write(text)
    bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
    (root/'art-source/render-catalog.json').write_text(text)
    (root/'art-source/render-settings.json').write_text(json.dumps(studio.CFG,indent=2)+'\n')
    proof=dict(schema=1,original_body_source_sha256=inherited['original_body_source_sha256'],
               original_renderer_sha256=inherited['original_renderer_sha256'],current_source_sha256=sha(source),
               fingerprint_tool_sha256=sha(root/'tools/body_dependencies.py'),
               inherited_source_sha256=sha(archive/'Rose-prefabs.blend'),inherited_proof_sha256=sha(archive/'body-reuse-proof-v5.json'),
               comparison='Preserved body meshes, animation, original neutral studio, shadow floor, sampling and camera. New environment material copies and model-local practical lights are excluded from body rendering.',
               models={k:dict(before=before[k],after=after[k]) for k in before})
    (root/'art-source/body-reuse-proof-v6.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('ROSE SPECTRUM SOURCE COMPLETE: 40 scenery models updated; all six body dependencies unchanged.',flush=True)


if __name__=='__main__':
    main()
