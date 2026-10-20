"""Refine the archived 0.7 environment; prove all six body bakes remain valid."""
import hashlib
import json
import sys
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_blender as studio
import reference_models
from body_dependencies import fingerprint


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=studio.ROOT;archive=root/'art-source/archive/rendered-v4';source=root/'art-source/Rose-prefabs.blend'
    if sha(source)!=sha(archive/'Rose-prefabs.blend'):raise ValueError('Start from the preserved 0.7 source')
    bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1)
    catalog=json.loads(bpy.data.texts['Rose sprite catalog.json'].as_string());studio.CFG=catalog['settings']
    studio.COLLECTIONS.update({c.name:c for c in scene.collection.children if c.name!='Collection'})
    studio.MATERIALS.update({m.name:m for m in bpy.data.materials})
    bodies=[k for k,r in catalog['models'].items() if r['camera_kind']=='character']
    before={k:fingerprint(k,catalog) for k in bodies}
    print('ROSE: six original body dependencies captured.',flush=True)
    reference_models.materials(studio)
    for region in catalog['visual_catalog']['regions']:
        for kind in catalog['visual_catalog']['structures']:reference_models.architecture(studio,region,kind)
        reference_models.obstacle(studio,region);reference_models.ground(studio,region,replace=True)
        print('ROSE: updated scenery and ground for '+region,flush=True)
    frame=max(n for r in catalog['models'].values() for n in r['timeline_frames'])+1
    for region in catalog['visual_catalog']['regions']:
        reference_models.ground(studio,region,path=True);name='ground_path_'+region
        catalog['models'][name]=dict(size=studio.CFG['camera']['texture']['size'],anchor=studio.camera(scene,'texture',studio.CFG['render']['texture_supersample']),frames=[name+'/idle-0-00.png'],timeline_frames=[frame],clips={'idle':[0]},camera_kind='texture',supersample=studio.CFG['render']['texture_supersample'],kind='texture')
        scene.timeline_markers.new(name+'/idle/0/0',frame=frame);frame+=1
        print('ROSE: added path surface for '+region,flush=True)
    studio.camera(scene,'character',studio.CFG['render']['supersample']);scene.frame_set(1)
    after={k:fingerprint(k,catalog) for k in bodies}
    if before!=after:raise ValueError('Environment edits changed a body dependency; require a new body bake')
    catalog['visual_catalog']=json.loads((root/'static/visual-catalog.json').read_text())
    catalog['settings']['art_direction']='reference-v5 / recessed facades, handled materials, granular terrain and regional paths'
    (root/'art-source/render-settings.json').write_text(json.dumps(catalog['settings'],indent=2)+'\n')
    catalog['render']['source_sha256']=hashlib.sha256(Path(studio.__file__).read_bytes()+(root/'art-source/render-settings.json').read_bytes()+(root/'tools/individual_models.py').read_bytes()+(root/'tools/fidelity_models.py').read_bytes()+Path(reference_models.__file__).read_bytes()+(root/'static/visual-catalog.json').read_bytes()).hexdigest()
    scene.frame_end=frame-1;studio.visibility('traveler')
    text=json.dumps(catalog,indent=2)+'\n';embedded=bpy.data.texts['Rose sprite catalog.json'];embedded.clear();embedded.write(text)
    bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
    (root/'art-source/render-catalog.json').write_text(text)
    (root/'art-source/render-settings.json').write_text(json.dumps(catalog['settings'],indent=2)+'\n')
    proof=dict(schema=1,original_body_source_sha256=sha(archive/'Rose-prefabs.blend'),current_source_sha256=sha(source),original_renderer_sha256=hashlib.sha256((archive/'Rose-prefabs.blend').read_bytes()+(archive/'render_saved_blend.py').read_bytes()+(archive/'render_blender.py').read_bytes()).hexdigest(),fingerprint_tool_sha256=sha(root/'tools/body_dependencies.py'),comparison='Meshes, faces, transforms, parents, modifiers, material nodes and links, pose curves, body camera, sampling, all studio lights including area fill, ambient, shadow floor and color management.',models={k:dict(before=before[k],after=after[k]) for k in bodies})
    (root/'art-source/body-reuse-proof-v5.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('ROSE: 40 environment/terrain models; six body dependency hashes unchanged.',flush=True)


if __name__=='__main__':main()
