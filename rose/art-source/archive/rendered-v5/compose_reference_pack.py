"""Compose verified 0.7 body frames with the complete 0.8 environment bake."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def compose(bodies,environments,destination):
    expected=json.loads((ROOT/'art-source/render-catalog.json').read_text())
    proof_path=ROOT/'art-source/body-reuse-proof-v5.json';proof=json.loads(proof_path.read_text())
    archive=ROOT/'art-source/archive/rendered-v4';old=json.loads((bodies/'catalog.json').read_text())
    old_sha=sha(archive/'Rose-prefabs.blend');new_sha=sha(ROOT/'art-source/Rose-prefabs.blend')
    recipe=hashlib.sha256((archive/'Rose-prefabs.blend').read_bytes()+(archive/'render_saved_blend.py').read_bytes()+(archive/'render_blender.py').read_bytes()).hexdigest()
    if (old['render']['blend_sha256']!=old_sha or proof['original_body_source_sha256']!=old_sha or old['render']['source_sha256']!=recipe or proof['original_renderer_sha256']!=recipe or proof['current_source_sha256']!=new_sha or proof['fingerprint_tool_sha256']!=sha(ROOT/'tools/body_dependencies.py')):raise ValueError('Body reuse provenance does not match the preserved source and recipe')
    paths={};provenance={};catalog=None
    for key,check in proof['models'].items():
        if check['before']!=check['after'] or old['models'][key]!=expected['models'][key]:raise ValueError('Body dependency or registration changed')
        paths[key]=(bodies,expected['models'][key]);provenance[key]=old_sha
    for folder in environments:
        part=json.loads((folder/'catalog-partial.json').read_text())
        if part['render']['blend_sha256']!=new_sha:raise ValueError('Environment source changed after rendering')
        if catalog is None:catalog={**part,'models':{}}
        if any(part[k]!=catalog[k] for k in ['settings','render','projection','animations','visual_catalog']):raise ValueError('Environment shards differ')
        if any(part[k]!=expected[k] for k in ['settings','projection','animations','visual_catalog']):raise ValueError('Environment recipe differs from the editable source')
        for key,record in part['models'].items():
            if key in paths or record!=expected['models'].get(key):raise ValueError('Unexpected or duplicated environment model: '+key)
            paths[key]=(folder,record);provenance[key]=new_sha
    if set(paths)!=set(expected['models']):raise ValueError('Complete body and environment coverage is required')
    jobs=[]
    for key,(folder,record) in paths.items():
        for filename in record['frames']:
            p=(folder/filename).resolve()
            if not p.is_relative_to(folder.resolve()) or not p.is_file():raise ValueError('Missing or unsafe frame: '+filename)
            jobs.append((p,filename))
    destination.mkdir(parents=True,exist_ok=True)
    for p,filename in jobs:
        target=destination/filename;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    catalog['models']=expected['models'];catalog['render']={**catalog['render'],'mode':'saved-blend-with-verified-body-reuse','model_source_sha256':provenance,'body_reuse_proof_sha256':sha(proof_path),'body_renderer_sha256':recipe}
    (destination/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    (destination/'render-identity.json').write_text(json.dumps(catalog['render'],indent=2)+'\n')
    print('Composed',len(jobs),'frames;',len(proof['models']),'body sources verified unchanged.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bodies',type=Path,required=True);p.add_argument('--environment',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();compose(a.bodies,a.environment,a.output)
