"""Apply the current render recipe to the saved source without changing geometry."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_blender as studio
import individual_models
import fidelity_models
bpy.ops.wm.open_mainfile(filepath=str(studio.ROOT/'art-source/Rose-prefabs.blend'))
catalog=json.loads(bpy.data.texts['Rose sprite catalog.json'].as_string())
catalog['settings']=studio.CFG
catalog['render']['samples']=studio.CFG['render']['samples'];catalog['render']['supersample']=studio.CFG['render']['supersample']
for record in catalog['models'].values():record['supersample']=studio.CFG['render']['texture_supersample'] if record['kind']=='texture' else studio.CFG['render']['supersample']
catalog['render']['source_sha256']=hashlib.sha256(Path(studio.__file__).read_bytes()+(studio.ROOT/'art-source/render-settings.json').read_bytes()+Path(individual_models.__file__).read_bytes()+Path(fidelity_models.__file__).read_bytes()+(studio.ROOT/'static/visual-catalog.json').read_bytes()).hexdigest()
scene=bpy.context.scene;scene.cycles.samples=studio.CFG['render']['samples'];studio.camera(scene,'character',studio.CFG['render']['supersample'])
encoded=json.dumps(catalog,indent=2)+'\n';text=bpy.data.texts['Rose sprite catalog.json'];text.clear();text.write(encoded)
(studio.ROOT/'art-source/render-catalog.json').write_text(encoded)
bpy.ops.wm.save_as_mainfile(filepath=str(studio.ROOT/'art-source/Rose-prefabs.blend'),compress=True)
print('ROSE: source uses 48 jittered samples at the higher native cell resolution',flush=True)
