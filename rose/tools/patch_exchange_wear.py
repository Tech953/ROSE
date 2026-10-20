"""Move hidden market wear onto its visible counter/apron; preserve body proof."""
import hashlib
import json
import sys
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from reframe_environment import fingerprint
import render_blender as studio

source=studio.ROOT/'art-source/Rose-prefabs.blend'
proof_path=studio.ROOT/'art-source/body-reuse-proof-v3.json';proof=json.loads(proof_path.read_text())
if hashlib.sha256(source.read_bytes()).hexdigest()!=proof['current_source_sha256']:raise ValueError('Source differs from reuse proof')
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1)
catalog=json.loads(bpy.data.texts['Rose sprite catalog.json'].as_string())
for key,item in proof['models'].items():
    if fingerprint(key,catalog)!=item['before']:raise ValueError('Body dependency changed')
for region in catalog['visual_catalog']['regions']:
    for obj in bpy.data.collections['exchange_'+region].objects:
        if obj.name.startswith('Condition / exposed debris'):obj.location.y-=.34
        if obj.name.startswith('Condition / opened fracture'):obj.location.y-=.27
for key,item in proof['models'].items():
    if fingerprint(key,catalog)!=item['after']:raise ValueError('Market patch changed a body dependency')
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
proof['current_source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();proof['environment_fix']='Market wear moved from behind the counter onto the visible face and apron.'
proof_path.write_text(json.dumps(proof,indent=2)+'\n')
print('ROSE: four market wear models corrected; all six body dependencies unchanged.',flush=True)
