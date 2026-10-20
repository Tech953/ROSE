"""Compose checksum-pinned 0.8 body frames with a complete new spectrum bake."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compose(bodies,environments,destination):
    expected=json.loads((ROOT/'art-source/render-catalog.json').read_text())
    proof_path=ROOT/'art-source/body-reuse-proof-v6.json'
    proof=json.loads(proof_path.read_text())
    archive=ROOT/'art-source/archive/rendered-v5'
    inherited=json.loads((archive/'body-reuse-proof-v5.json').read_text())
    pinned=json.loads((archive/'raw-body-checksums.json').read_text())
    old=json.loads((bodies/'catalog.json').read_text())
    new_sha=sha(ROOT/'art-source/Rose-prefabs.blend')
    if (proof['current_source_sha256']!=new_sha or proof['inherited_source_sha256']!=sha(archive/'Rose-prefabs.blend')
        or proof['inherited_proof_sha256']!=sha(archive/'body-reuse-proof-v5.json')
        or old['render']['blend_sha256']!=proof['inherited_source_sha256']
        or proof['fingerprint_tool_sha256']!=sha(ROOT/'tools/body_dependencies.py')):
        raise ValueError('Body reuse source/proof differs from the preserved bank')
    paths={};provenance={};catalog=None
    for key,check in proof['models'].items():
        if (check['before']!=check['after'] or check['before']!=inherited['models'][key]['after']
            or old['models'][key]!=expected['models'][key]
            or old['render']['model_source_sha256'][key]!=proof['original_body_source_sha256']
            or old['render']['body_renderer_sha256']!=proof['original_renderer_sha256']):
            raise ValueError('Body dependency, original recipe or registration changed')
        for filename in expected['models'][key]['frames']:
            path=(bodies/filename).resolve()
            if not path.is_relative_to(bodies.resolve()) or sha(path)!=pinned['frames'][filename]:
                raise ValueError('Retained raw body checksum changed: '+filename)
        paths[key]=(bodies,expected['models'][key]);provenance[key]=proof['original_body_source_sha256']
    recipe=hashlib.sha256((ROOT/'art-source/Rose-prefabs.blend').read_bytes()+(ROOT/'tools/render_saved_blend.py').read_bytes()+(ROOT/'tools/render_blender.py').read_bytes()+(ROOT/'tools/spectrum_models.py').read_bytes()+(ROOT/'static/lighting-signatures.json').read_bytes()).hexdigest()
    for folder in environments:
        part=json.loads((folder/'catalog-partial.json').read_text())
        if part['render']['blend_sha256']!=new_sha or part['render']['source_sha256']!=recipe:
            raise ValueError('Environment source or rendering recipe changed')
        if catalog is None:catalog={**part,'models':{}}
        if any(part[k]!=catalog[k] for k in ['settings','render','projection','animations','visual_catalog']):
            raise ValueError('Environment shards differ')
        if any(part[k]!=expected[k] for k in ['settings','projection','animations','visual_catalog']):
            raise ValueError('Environment recipe differs from the final editable source')
        for key,record in part['models'].items():
            if key in paths or record!=expected['models'].get(key):
                raise ValueError('Unexpected or duplicated model: '+key)
            paths[key]=(folder,record);provenance[key]=new_sha
    if set(paths)!=set(expected['models']):
        raise ValueError('Complete body, scenery and terrain coverage is required')
    jobs=[]
    for folder,record in paths.values():
        for filename in record['frames']:
            path=(folder/filename).resolve()
            if not path.is_relative_to(folder.resolve()) or not path.is_file():
                raise ValueError('Missing or unsafe frame: '+filename)
            jobs.append((path,filename))
    destination.mkdir(parents=True,exist_ok=True)
    for path,filename in jobs:
        target=destination/filename;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    catalog['models']=expected['models']
    catalog['render']={**catalog['render'],'mode':'saved-blend-with-verified-body-reuse',
                       'model_source_sha256':provenance,'body_reuse_proof_sha256':sha(proof_path),
                       'body_renderer_sha256':proof['original_renderer_sha256'],
                       'retained_body_checksums_sha256':sha(archive/'raw-body-checksums.json')}
    for name in ['catalog.json','render-identity.json']:
        (destination/name).write_text(json.dumps(catalog if name=='catalog.json' else catalog['render'],indent=2)+'\n')
    print('Composed',len(jobs),'frames; all 1,152 retained raw body checksums and 92 fresh scenery frames verified.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bodies',type=Path,required=True)
    p.add_argument('--environment',type=Path,nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();compose(a.bodies,a.environment,a.output)
