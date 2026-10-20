"""Combine proven unchanged body renders with newly framed scenery."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def compose(bodies,environment,destination):
    expected=json.loads((ROOT/'art-source/render-catalog.json').read_text())
    proof=json.loads((ROOT/'art-source/body-reuse-proof-v3.json').read_text())
    current_sha=hashlib.sha256((ROOT/'art-source/Rose-prefabs.blend').read_bytes()).hexdigest()
    old_sha=hashlib.sha256((ROOT/'art-source/body-bake-v3.blend').read_bytes()).hexdigest()
    recipe=ROOT/'art-source/archive/body-bake-v3'
    renderer_sha=hashlib.sha256((ROOT/'art-source/body-bake-v3.blend').read_bytes()
                                +(recipe/'render_saved_blend.py').read_bytes()+(recipe/'render_blender.py').read_bytes()).hexdigest()
    if (current_sha,old_sha)!=(proof['current_source_sha256'],proof['original_body_source_sha256']):raise ValueError('Reuse source bytes changed')
    catalog=json.loads((environment/'catalog-partial.json').read_text())
    if catalog['render']['blend_sha256']!=current_sha or catalog['settings']!=expected['settings']:raise ValueError('Environment source/settings do not match')
    paths={};provenance={}
    for folder in bodies:
        part=json.loads((folder/'catalog-partial.json').read_text())
        if part['render']['blend_sha256']!=old_sha or part['render']['source_sha256']!=renderer_sha:raise ValueError('Body frames have an unexpected source or renderer recipe')
        for key,record in part['models'].items():
            if key not in proof['models']:continue
            check=proof['models'][key]
            if check['before']!=check['after'] or check['after']!=expected['models'][key]['dependency_sha256']:raise ValueError('Unchanged-body proof is incomplete')
            current={k:v for k,v in expected['models'][key].items() if k!='dependency_sha256'}
            if record!=current or key in paths:raise ValueError('Body registration changed or was duplicated')
            paths[key]=(folder,record);provenance[key]=old_sha
    for key,record in catalog['models'].items():
        if key in proof['models'] or key in paths or record!=expected['models'][key]:raise ValueError('Unexpected scenery model')
        paths[key]=(environment,record);provenance[key]=current_sha
    if set(paths)!=set(expected['models']):raise ValueError('Complete model coverage is required')
    jobs=[]
    for key,(folder,record) in paths.items():
        for filename in record['frames']:
            p=(folder/filename).resolve()
            if not p.is_relative_to(folder.resolve()) or not p.is_file():raise ValueError('Missing or unsafe frame: '+filename)
            jobs.append((p,filename))
    destination.mkdir(parents=True,exist_ok=True)
    for p,filename in jobs:
        target=destination/filename;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    catalog['models']=expected['models'];catalog['render']={**catalog['render'],'mode':'saved-blend-with-verified-body-reuse',
      'model_source_sha256':provenance,'body_reuse_proof_sha256':hashlib.sha256((ROOT/'art-source/body-reuse-proof-v3.json').read_bytes()).hexdigest()}
    (destination/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    (destination/'render-identity.json').write_text(json.dumps(catalog['render'],indent=2)+'\n')
    print('Composed',len(jobs),'frames; six unchanged bodies retain their archived source provenance.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bodies',type=Path,nargs='+',required=True);p.add_argument('--environment',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();compose(a.bodies,a.environment,a.output)
