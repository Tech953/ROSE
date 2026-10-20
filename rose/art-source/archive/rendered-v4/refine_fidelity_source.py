"""Update the saved v4 trial with the same final body and material builder recipe."""
import hashlib
import json
import sys
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_blender as studio
import fidelity_models
import individual_models

bpy.ops.wm.open_mainfile(filepath=str(studio.ROOT/'art-source/Rose-prefabs.blend'))
catalog=json.loads(bpy.data.texts['Rose sprite catalog.json'].as_string())
studio.COLLECTIONS.update({c.name:c for c in bpy.context.scene.collection.children if c.name!='Collection'})
old_materials={name:bpy.data.materials.get(name) for name in studio.CFG['materials']['surfaces']}
for name,settings in studio.CFG['materials']['surfaces'].items():
    studio.material(name,tuple(settings['color']),**{k:v for k,v in settings.items() if k!='color'})
for obj in bpy.data.objects:
    if obj.type=='MESH':
        for slot in obj.material_slots:
            if slot.material and slot.material.name in studio.MATERIALS:slot.material=studio.MATERIALS[slot.material.name]
for name in catalog['visual_catalog']['profiles']:
    col=studio.COLLECTIONS[name]
    pick=lambda label:next(obj for obj in col.objects if obj.name.split('.')[0]==label)
    joints={'head':pick('Facial turn'),'body':pick('Breath and lean')}
    for side in ['L','R']:joints['elbow'+side]=pick('Elbow '+side);joints['knee'+side]=pick('Knee '+side);joints['leg'+side]=pick('Hip '+side)
    fidelity_models.body(studio,name,joints)
for name,old in old_materials.items():
    if old and old.users==0:bpy.data.materials.remove(old)
    studio.MATERIALS[name].name=name
catalog['settings']=studio.CFG
catalog['render']['source_sha256']=hashlib.sha256(Path(studio.__file__).read_bytes()+(studio.ROOT/'art-source/render-settings.json').read_bytes()+Path(individual_models.__file__).read_bytes()+Path(fidelity_models.__file__).read_bytes()+(studio.ROOT/'static/visual-catalog.json').read_bytes()).hexdigest()
source=json.dumps(catalog,indent=2)+'\n';text=bpy.data.texts['Rose sprite catalog.json'];text.clear();text.write(source)
(studio.ROOT/'art-source/render-catalog.json').write_text(source)
bpy.ops.wm.save_as_mainfile(filepath=str(studio.ROOT/'art-source/Rose-prefabs.blend'),compress=True)
print('ROSE: final fidelity source saved; pose controls and timeline retained',flush=True)
